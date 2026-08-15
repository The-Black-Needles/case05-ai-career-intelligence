"""Strict in-memory contract for a public job record."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from ipaddress import ip_address
import unicodedata
from urllib.parse import urlsplit


_STRING_LIMITS = {
    "record_id": 256,
    "source_name": 128,
    "source_record_id": 256,
    "title": 512,
    "company_name": 256,
    "location_text": 512,
    "description_text": 100_000,
    "source_url": 4_096,
}


@dataclass(frozen=True, slots=True)
class PublicJobRecord:
    """A validated, immutable public job record with supplied values preserved."""

    record_id: str
    source_name: str
    source_record_id: str
    title: str
    company_name: str
    location_text: str
    description_text: str
    source_url: str
    observed_at: datetime
    published_at: datetime | None = None

    def __post_init__(self) -> None:
        for field in fields(self):
            if field.name not in _STRING_LIMITS:
                continue
            value = getattr(self, field.name)
            if type(value) is not str:
                raise TypeError(f"{field.name} must be exactly str")
            if not value:
                raise ValueError(f"{field.name} must be nonempty")
            if value != value.strip():
                raise ValueError(f"{field.name} must already be trimmed")
            if len(value) > _STRING_LIMITS[field.name]:
                raise ValueError(f"{field.name} exceeds its maximum length")
            if field.name == "description_text":
                forbidden_control = any(
                    unicodedata.category(character) == "Cc"
                    and character not in {"\n", "\t"}
                    for character in value
                )
            else:
                forbidden_control = any(
                    unicodedata.category(character) == "Cc" for character in value
                )
            if forbidden_control:
                raise ValueError(f"{field.name} contains a forbidden control character")

        self._validate_url()
        self._validate_datetime("observed_at", self.observed_at)
        if self.published_at is not None:
            self._validate_datetime("published_at", self.published_at)
            if self.published_at.astimezone(timezone.utc) > self.observed_at.astimezone(
                timezone.utc
            ):
                raise ValueError("published_at cannot be later than observed_at")

    def _validate_url(self) -> None:
        if any(character.isspace() for character in self.source_url):
            raise ValueError("source_url must not contain whitespace")
        try:
            parsed = urlsplit(self.source_url)
            hostname = parsed.hostname
            username = parsed.username
            parsed.port
        except ValueError as exc:
            raise ValueError("source_url is invalid") from exc
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be an absolute HTTP or HTTPS URL")
        if hostname is None:
            raise ValueError("source_url must contain a hostname")
        if username is not None or parsed.password is not None:
            raise ValueError("source_url must not contain credentials")
        self._validate_hostname(hostname)

    @staticmethod
    def _validate_hostname(hostname: str) -> None:
        try:
            ip_address(hostname)
            return
        except ValueError:
            pass

        try:
            ascii_name = hostname.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("source_url hostname is invalid") from exc
        dns_name = ascii_name[:-1] if ascii_name.endswith(".") else ascii_name
        if not dns_name:
            raise ValueError("source_url hostname is invalid")
        ascii_labels = dns_name.split(".")
        if any(
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
            or any(not (character.isalnum() or character == "-") for character in label)
            for label in ascii_labels
        ) or len(".".join(ascii_labels)) > 253:
            raise ValueError("source_url hostname is invalid")

    @staticmethod
    def _validate_datetime(name: str, value: object) -> None:
        if type(value) is not datetime:
            raise TypeError(f"{name} must be exactly datetime")
        try:
            offset = value.utcoffset()
        except (OverflowError, ValueError) as exc:
            raise ValueError(f"{name} must have a valid UTC offset") from exc
        if offset is None:
            raise ValueError(f"{name} must be timezone-aware")
