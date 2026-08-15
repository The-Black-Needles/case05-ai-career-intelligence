from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from ai_job_radar import public_sanitizer as sanitizer


class PublicSanitizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, name: str, content: str | bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")

    def categories(self, names: list[str]) -> set[str]:
        return {item.category for item in sanitizer.scan_repository(self.root, names)}

    def synthetic(self, **updates: object) -> str:
        value: dict[str, object] = {"schema_version": 1, "synthetic": True, "jobs": []}
        value.update(updates)
        return json.dumps(value)

    def test_safe_ordinary_utf8_text_passes(self) -> None:
        self.write("notes.txt", "Public scaffold notes with café.\n")
        self.assertEqual([], sanitizer.scan_repository(self.root, ["notes.txt"]))

    def test_valid_and_empty_synthetic_fixtures_pass(self) -> None:
        self.write("data/empty.json", self.synthetic())
        self.write("data/url.json", self.synthetic(site="https://fixtures.example.org/jobs"))
        self.write(
            "config/example.example.json",
            json.dumps({"schema_version": 4, "synthetic": True, "unknown_domain_field": {}}),
        )
        self.assertEqual(
            [],
            sanitizer.scan_repository(
                self.root,
                ["data/empty.json", "data/url.json", "config/example.example.json"],
            ),
        )

    def test_generic_sensitive_content_fails(self) -> None:
        cases = {
            "home-path": "/" + "Users" + "/sample-person/private/file.txt",
            "windows-path": "C:" + "\\" + "private" + "\\" + "notes.txt",
            "windows-unc": "\\" * 2 + "server" + "\\share\\notes.txt",
            "email": "person" + "@" + "ordinary-domain.test",
            "phone": "+55 " + "11 " + "98765" + "-" + "4321",
            "personal-profile-url": "https://" + "github.com" + "/sample-person",
            "private-key": "-----BEGIN " + "PRIVATE KEY-----",
            "known-token": "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0",
            "credential-assignment": "pass" + "word=not-a-real-value",
            "local-file-url": "file" + ":///private/example.txt",
            "aws-access-key-id": "AK" + "IA" + "A1B2C3D4E5F6G7H8",
            "sk-token": "s" + "k-" + "A1b2C3d4E5f6G7h8I9j0",
            "authorization-bearer": "Author" + "ization: Bearer example-token-value",
            "client-secret": "client" + "_secret=example-secret-value",
            "aws-secret-access-key": "aws_secret" + "_access_key=example-secret-value",
            "dsa-private-key": "-----BEGIN " + "DSA PRIVATE KEY-----",
            "encrypted-private-key": "-----BEGIN " + "ENCRYPTED PRIVATE KEY-----",
        }
        for expected, content in cases.items():
            with self.subTest(expected=expected):
                self.write("sample.txt", content)
                categories = self.categories(["sample.txt"])
                normalized = {
                    "windows-unc": "windows-path",
                    "client-secret": "credential-assignment",
                    "aws-secret-access-key": "credential-assignment",
                    "dsa-private-key": "private-key",
                    "encrypted-private-key": "private-key",
                }.get(expected, expected)
                self.assertIn(normalized, categories)

    def test_force_added_ignored_file_is_enumerated_and_detected(self) -> None:
        self.write(".gitignore", "ignored.txt\n")
        self.write("ignored.txt", "client" + "_secret=example-secret-value")
        subprocess.run(["git", "-C", str(self.root), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "-f", "ignored.txt"], check=True)
        candidates = sanitizer._git_candidates(self.root)
        self.assertIn("ignored.txt", candidates)
        self.assertIn("credential-assignment", self.categories(candidates))

    def test_high_entropy_material_fails(self) -> None:
        material = "aB3dE5fG7hJ9" + "kL2mN4pQ6rS8" + "tV1wX0yZ"
        self.write("sample.txt", material)
        self.assertIn("high-entropy-material", self.categories(["sample.txt"]))

    def test_sensitive_and_publication_artifact_names_fail(self) -> None:
        cases = {
            ".env": "sensitive-config",
            "run.log": "publication-artifact",
            "results/output.txt": "publication-artifact",
            "snapshot.bak": "publication-artifact",
            "state.dump": "publication-artifact",
            "shell.history": "publication-artifact",
            "trace.har": "browser-session-artifact",
            "cookies.sqlite": "browser-session-artifact",
            "session.txt": "browser-session-artifact",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.write(name, "placeholder")
                self.assertIn(expected, self.categories([name]))

    def test_synthetic_contract_failures(self) -> None:
        cases = {
            "missing": json.dumps({"schema_version": 1}),
            "false": self.synthetic(synthetic=False),
            "string": self.synthetic(synthetic="true"),
            "malformed": "{",
            "version": self.synthetic(schema_version="1"),
            "domain": self.synthetic(site="https://jobs.ordinary-domain.test/opening"),
        }
        expected = {
            "missing": "synthetic-provenance",
            "false": "synthetic-provenance",
            "string": "synthetic-provenance",
            "malformed": "synthetic-json",
            "version": "synthetic-schema-version",
            "domain": "synthetic-url-domain",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                self.write("data/sample.json", content)
                self.assertIn(expected[label], self.categories(["data/sample.json"]))

    def test_fictional_identifier_checks_are_narrow(self) -> None:
        self.write(
            "config/profile.example.json",
            json.dumps({"schema_version": 1, "synthetic": True, "profile_id": "ordinary"}),
        )
        self.assertIn("fictional-identifier", self.categories(["config/profile.example.json"]))
        self.write(
            "config/companies.example.json",
            json.dumps({"schema_version": 1, "synthetic": True, "companies": [{"id": "ordinary"}]}),
        )
        self.assertIn("fictional-identifier", self.categories(["config/companies.example.json"]))

    def test_invalid_binary_opaque_oversized_and_symlink_fail(self) -> None:
        self.write("invalid.txt", b"\xff")
        self.write("binary.txt", b"safe\0unsafe")
        self.write("archive.zip", "text despite suffix")
        self.write("large.txt", b"x" * (sanitizer.MAX_FILE_BYTES + 1))
        self.write("target.txt", "safe")
        (self.root / "link.txt").symlink_to("target.txt")
        cases = {
            "invalid.txt": "invalid-utf8",
            "binary.txt": "binary-content",
            "archive.zip": "opaque-file-type",
            "large.txt": "oversized-file",
            "link.txt": "symlink",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertIn(expected, self.categories([name]))

    def test_one_failure_makes_cli_nonzero_and_output_is_redacted(self) -> None:
        sensitive = "person" + "@" + "ordinary-domain.test"
        source_line = "prefix " + sensitive + " suffix"
        self.write("safe.txt", "safe")
        self.write("nested/finding.txt", source_line)
        subprocess.run(["git", "-C", str(self.root), "add", "safe.txt", "nested/finding.txt"], check=True)
        stdout = io.StringIO()
        stderr = io.StringIO()
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = sanitizer.main()
        finally:
            os.chdir(previous)
        combined = stdout.getvalue() + stderr.getvalue()
        self.assertNotEqual(0, result)
        self.assertIn("nested/finding.txt | email | FAIL", combined)
        self.assertNotIn(sensitive, combined)
        self.assertNotIn(source_line, combined)
        self.assertNotIn(str(self.root), combined)
        self.assertNotIn("Traceback", combined)
        self.assertEqual("", stderr.getvalue())

    def test_malformed_local_denylist_fails_safely(self) -> None:
        self.write("safe.txt", "safe")
        self.write("config/public-sanitizer.local.json", "{")
        stdout = io.StringIO()
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with redirect_stdout(stdout):
                result = sanitizer.main()
        finally:
            os.chdir(previous)
        self.assertNotEqual(0, result)
        self.assertEqual(". | scanner-error | FAIL\n", stdout.getvalue())

    def test_git_candidate_failure_is_redacted_and_silent_on_stderr(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        failed = subprocess.CompletedProcess([], 23, b"", b"sensitive git detail")
        with mock.patch.object(sanitizer.subprocess, "run", return_value=failed):
            previous = Path.cwd()
            try:
                os.chdir(self.root)
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = sanitizer.main()
            finally:
                os.chdir(previous)
        self.assertNotEqual(0, result)
        self.assertEqual(". | scanner-error | FAIL\n", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        self.assertNotIn("sensitive", stdout.getvalue())

    def test_malformed_local_regex_fails_without_disclosure(self) -> None:
        invalid_regex = "private-marker-("
        self.write(
            "config/public-sanitizer.local.json",
            json.dumps({"literals": [], "regexes": [invalid_regex]}),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = sanitizer.main()
        finally:
            os.chdir(previous)
        self.assertNotEqual(0, result)
        self.assertEqual(". | scanner-error | FAIL\n", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        self.assertNotIn(invalid_regex, stdout.getvalue())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable")
    def test_special_filesystem_object_fails_closed(self) -> None:
        fifo = self.root / "special.fifo"
        try:
            os.mkfifo(fifo)
        except OSError as exc:
            self.skipTest(f"FIFO creation unavailable: {exc.__class__.__name__}")
        self.assertIn("special-file", self.categories(["special.fifo"]))

    def test_unicode_separator_in_git_filename_cannot_inject_output(self) -> None:
        name = "record\u2028injection.txt"
        self.write(name, "person" + "@" + "ordinary-domain.test")
        subprocess.run(["git", "-C", str(self.root), "add", "--", name], check=True)
        stdout = io.StringIO()
        stderr = io.StringIO()
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = sanitizer.main()
        finally:
            os.chdir(previous)
        self.assertNotEqual(0, result)
        self.assertEqual(["record?injection.txt | email | FAIL"], stdout.getvalue().splitlines())
        self.assertEqual("", stderr.getvalue())
        self.assertNotIn(str(self.root), stdout.getvalue())

    def test_local_denylist_matches_without_disclosure(self) -> None:
        private_literal = "private" + "-maintainer-term"
        self.write("safe.txt", "contains " + private_literal)
        self.write(
            "config/public-sanitizer.local.json",
            json.dumps({"literals": [private_literal], "regexes": []}),
        )
        findings = sanitizer.scan_repository(self.root, ["safe.txt"])
        rendered = "\n".join(f"{item.path} | {item.category} | FAIL" for item in findings)
        self.assertIn("local-private-denylist", rendered)
        self.assertNotIn(private_literal, rendered)

    def test_candidate_path_escape_fails_closed(self) -> None:
        findings = sanitizer.scan_repository(self.root, ["../outside.txt"])
        self.assertEqual([sanitizer.Finding(".", "candidate-path")], findings)

    def test_current_repository_and_scanner_sources_pass_ordinary_scan(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        candidates = sanitizer._git_candidates(repository)
        self.assertIn("src/ai_job_radar/public_sanitizer.py", candidates)
        self.assertIn("tests/test_public_sanitizer.py", candidates)
        self.assertEqual([], sanitizer.scan_repository(repository, candidates))


if __name__ == "__main__":
    unittest.main()
