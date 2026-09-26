"""Fail-closed checks for the repository's public publication candidate."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Iterable, NamedTuple, Pattern
import unicodedata
from urllib.parse import urlsplit


MAX_FILE_BYTES = 1_048_576
LOCAL_RULES_PATH = PurePosixPath("config/public-sanitizer.local.json")


class Finding(NamedTuple):
    path: str
    category: str


class ScanFailure(Exception):
    """An intentionally detail-free scanner failure."""


def _rx(*parts: str, flags: int = 0) -> Pattern[str]:
    return re.compile("".join(parts), flags)


# Signatures are split so this source is scanned by the same rules it applies.
CONTENT_RULES: tuple[tuple[str, Pattern[str]], ...] = (
    ("home-path", _rx(r"(?<![\w.-])/(?:Users|home)/", r"[^/\s]+/")),
    ("windows-path", _rx(r"(?i)(?:\b[A-Z]:\\", r"|\\\\[^\\\s]+\\[^\\\s]+)")),
    ("local-file-url", _rx(r"(?i)file", r":/{2,3}(?!/)(?:[^\s]+)")),
    ("email", _rx(r"(?i)\b[A-Z0-9._%+-]+@", r"(?![A-Z0-9.-]*example\.(?:com|org|net)\b)[A-Z0-9.-]+\.[A-Z]{2,}\b")),
    ("phone", _rx(r"(?<!\w)(?:\+\d{1,3}[ .-]?)?(?:\(\d{2,3}\)[ .-]?|\d{2,3}[ .-])\d{3,5}[ .-]\d{4}(?!\w)")),
    ("personal-profile-url", _rx(r"(?i)https?://(?:www\.)?(?:linkedin\.com/in|github\.com)/", r"[A-Z0-9_.-]+(?:/|\b)")),
    ("private-key", _rx(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE ", r"KEY-----")),
    ("aws-access-key-id", _rx(r"\bAKIA", r"[A-Z0-9]{16}\b")),
    ("sk-token", _rx(r"\bsk-", r"[A-Za-z0-9_-]{16,}\b")),
    ("authorization-bearer", _rx(r"(?im)^\s*Authorization\s*:\s*Bearer\s+", r"[^\s,;]{6,}")),
    ("known-token", _rx(r"\b(?:gh[pousr]_|xox[baprs]-)", r"[A-Za-z0-9_-]{16,}\b")),
    ("credential-assignment", _rx(r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|bearer|client_secret|aws_secret_access_key)\b\s*[:=]\s*", r"['\"]?[^\s,'\"}]{6,}")),
)

OPAQUE_SUFFIXES = {
    ".7z", ".a", ".avi", ".bin", ".bmp", ".bz2", ".class", ".db", ".dll",
    ".dmg", ".doc", ".docx", ".exe", ".gif", ".gz", ".ico", ".jar", ".jpeg",
    ".jpg", ".mov", ".mp3", ".mp4", ".o", ".pdf", ".png", ".pyc", ".rar",
    ".so", ".sqlite", ".tar", ".tgz", ".webp", ".xls", ".xlsx", ".xz", ".zip",
}
ARTIFACT_SUFFIXES = {".bak", ".dump", ".history", ".log", ".old", ".orig", ".result", ".results"}
ARTIFACT_PARTS = {"backup", "backups", "dump", "dumps", "history", "logs", "results"}
BROWSER_SUFFIXES = {".har"}
BROWSER_NAMES = {"cookies", "cookies.sqlite", "session", "sessions", "sessionstore.jsonlz4"}
SENSITIVE_NAMES = {".env", ".npmrc", ".pypirc", "credentials.json", "id_dsa", "id_ed25519", "id_rsa", "secrets.json"}


def _display_path(path: str) -> str:
    """Make a repository-relative path safe for one-record-per-line output."""
    return "".join(
        ch if ch != "|" and (ch == " " or unicodedata.category(ch)[0] not in {"C", "Z"}) else "?"
        for ch in path
    )


def _finding(path: str, category: str) -> Finding:
    return Finding(_display_path(path), category)


def _git_candidates(root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", os.fspath(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode != 0:
        raise ScanFailure()
    result: list[str] = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            result.append(raw.decode("utf-8", "strict"))
        except UnicodeDecodeError as exc:
            raise ScanFailure() from exc
    return sorted(set(result))


def _validate_relative(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or "\\" in name or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ScanFailure()
    if path.parts[0] == ".git":
        raise ScanFailure()
    return path


def _read_regular(root: Path, rel: PurePosixPath) -> tuple[bytes | None, str | None]:
    current = root
    for part in rel.parts:
        current = current / part
        try:
            info = current.lstat()
        except OSError:
            return None, "unreadable-file"
        if stat.S_ISLNK(info.st_mode):
            return None, "symlink"
    if not stat.S_ISREG(info.st_mode):
        return None, "special-file"
    if info.st_size > MAX_FILE_BYTES:
        return None, "oversized-file"
    try:
        with current.open("rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
    except OSError:
        return None, "unreadable-file"
    if len(data) > MAX_FILE_BYTES:
        return None, "oversized-file"
    return data, None


def _name_category(rel: PurePosixPath) -> str | None:
    lowered = [part.lower() for part in rel.parts]
    name = lowered[-1]
    suffix = Path(name).suffix
    if name in SENSITIVE_NAMES or name.startswith(".env."):
        return "sensitive-config"
    if suffix in BROWSER_SUFFIXES or name in BROWSER_NAMES or "cookie" in name or "session" in name:
        return "browser-session-artifact"
    if suffix in OPAQUE_SUFFIXES:
        return "opaque-file-type"
    if suffix in ARTIFACT_SUFFIXES or any(part in ARTIFACT_PARTS for part in lowered[:-1]):
        return "publication-artifact"
    return None


def _entropy(value: str) -> float:
    counts = {char: value.count(char) for char in set(value)}
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in counts.values())


def _has_high_entropy_material(text: str) -> bool:
    token_pattern = _rx(r"(?<![A-Za-z0-9])(?=[A-Za-z0-9]{32,}\b)(?=[A-Za-z0-9]*[a-z])", r"(?=[A-Za-z0-9]*[A-Z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{32,}")
    return any(_entropy(match.group(0)) >= 4.2 for match in token_pattern.finditer(text))


def _is_synthetic_fixture(rel: PurePosixPath) -> bool:
    return (
        (
            len(rel.parts) == 2
            and ((rel.parts[0] == "config" and rel.name.endswith(".example.json"))
                 or (rel.parts[0] == "data" and rel.suffix == ".json"))
        )
        or (
            len(rel.parts) == 3
            and rel.parts[:2] == ("data", "demo_readiness_cases")
            and rel.suffix == ".json"
        )
    )


def _walk_urls(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_urls(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_urls(child)
    elif isinstance(value, str) and value.lower().startswith(("http://", "https://")):
        yield value


def _reserved_host(host: str | None) -> bool:
    if not host:
        return False
    host = host.rstrip(".").lower()
    return host.endswith(".invalid") or any(host == base or host.endswith("." + base) for base in ("example.com", "example.org", "example.net"))


def _synthetic_findings(rel: PurePosixPath, text: str) -> list[Finding]:
    shown = rel.as_posix()
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, RecursionError):
        return [_finding(shown, "synthetic-json")]
    if not isinstance(value, dict):
        return [_finding(shown, "synthetic-object")]
    found: list[Finding] = []
    if not isinstance(value.get("schema_version"), int) or isinstance(value.get("schema_version"), bool):
        found.append(_finding(shown, "synthetic-schema-version"))
    if value.get("synthetic") is not True:
        found.append(_finding(shown, "synthetic-provenance"))
    if rel.as_posix() == "config/profile.example.json":
        profile_id = value.get("profile_id")
        if not isinstance(profile_id, str) or not profile_id.startswith(("synthetic_", "example_")):
            found.append(_finding(shown, "fictional-identifier"))
    if rel.as_posix() == "config/companies.example.json":
        companies = value.get("companies")
        if isinstance(companies, list):
            for company in companies:
                identifier = company.get("id") if isinstance(company, dict) else None
                if not isinstance(identifier, str) or not identifier.startswith(("synthetic_", "example_")):
                    found.append(_finding(shown, "fictional-identifier"))
                    break
    if any(not _reserved_host(urlsplit(url).hostname) for url in _walk_urls(value)):
        found.append(_finding(shown, "synthetic-url-domain"))
    return found


def _load_local_rules(root: Path) -> tuple[list[str], list[Pattern[str]]]:
    path = root.joinpath(*LOCAL_RULES_PATH.parts)
    if not path.exists():
        return [], []
    data, error = _read_regular(root, LOCAL_RULES_PATH)
    if error or data is None or b"\0" in data:
        raise ScanFailure()
    try:
        value = json.loads(data.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ScanFailure() from exc
    if not isinstance(value, dict) or set(value) - {"literals", "regexes"}:
        raise ScanFailure()
    literals = value.get("literals", [])
    regexes = value.get("regexes", [])
    if not isinstance(literals, list) or not isinstance(regexes, list) or not all(isinstance(item, str) and item for item in literals + regexes):
        raise ScanFailure()
    try:
        compiled = [re.compile(item) for item in regexes]
    except re.error as exc:
        raise ScanFailure() from exc
    return literals, compiled


def scan_repository(root: Path, candidates: Iterable[str] | None = None) -> list[Finding]:
    root = root.absolute()
    if not root.is_dir() or root.is_symlink():
        raise ScanFailure()
    literals, local_regexes = _load_local_rules(root)
    names = _git_candidates(root) if candidates is None else sorted(set(candidates))
    findings: list[Finding] = []
    for name in names:
        try:
            rel = _validate_relative(name)
        except ScanFailure:
            findings.append(_finding(".", "candidate-path"))
            continue
        shown = rel.as_posix()
        category = _name_category(rel)
        if category:
            findings.append(_finding(shown, category))
            continue
        data, error = _read_regular(root, rel)
        if error or data is None:
            findings.append(_finding(shown, error or "scanner-error"))
            continue
        if b"\0" in data:
            findings.append(_finding(shown, "binary-content"))
            continue
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeDecodeError:
            findings.append(_finding(shown, "invalid-utf8"))
            continue
        for rule, pattern in CONTENT_RULES:
            if pattern.search(text):
                findings.append(_finding(shown, rule))
        if _has_high_entropy_material(text):
            findings.append(_finding(shown, "high-entropy-material"))
        if any(literal in text for literal in literals) or any(pattern.search(text) for pattern in local_regexes):
            findings.append(_finding(shown, "local-private-denylist"))
        if _is_synthetic_fixture(rel):
            findings.extend(_synthetic_findings(rel, text))
    return sorted(set(findings))


def main() -> int:
    try:
        findings = scan_repository(Path.cwd())
        if findings:
            for finding in findings:
                print(f"{finding.path} | {finding.category} | FAIL")
            return 1
        print(". | repository-sanitization | PASS")
        return 0
    except BaseException:
        print(". | scanner-error | FAIL")
        return 2


if __name__ == "__main__":
    sys.exit(main())
