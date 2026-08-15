from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone, tzinfo
import unittest

from ai_job_radar.job_record import PublicJobRecord


LIMITS = {
    "record_id": 256,
    "source_name": 128,
    "source_record_id": 256,
    "title": 512,
    "company_name": 256,
    "location_text": 512,
    "description_text": 100_000,
    "source_url": 4_096,
}


def values(**updates: object) -> dict[str, object]:
    supplied: dict[str, object] = {
        "record_id": "record-1",
        "source_name": "Example Board",
        "source_record_id": "source-9",
        "title": "Platform Engineer",
        "company_name": "Example Company",
        "location_text": "Remote",
        "description_text": "Build reliable systems.",
        "source_url": "https://jobs.example.org/openings/9?view=public#details",
        "observed_at": datetime(2026, 8, 14, 12, 30, tzinfo=timezone.utc),
        "published_at": datetime(
            2026, 8, 13, 9, 15, tzinfo=timezone(timedelta(hours=-3))
        ),
    }
    supplied.update(updates)
    return supplied


class StringSubclass(str):
    pass


class DateTimeSubclass(datetime):
    pass


class FoldAwareTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> timedelta:
        return timedelta(hours=-value.fold if value is not None else 0)

    def dst(self, value: datetime | None) -> timedelta:
        return timedelta(0)


class PublicJobRecordTests(unittest.TestCase):
    def test_valid_construction_preserves_every_supplied_value(self) -> None:
        supplied = values()
        record = PublicJobRecord(**supplied)
        for name, value in supplied.items():
            with self.subTest(name=name):
                self.assertIs(getattr(record, name), value)

    def test_frozen_slotted_and_value_equality(self) -> None:
        first = PublicJobRecord(**values())
        second = PublicJobRecord(**values())
        different = PublicJobRecord(**values(title="Another title"))
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.title = "Changed"
        with self.assertRaises((AttributeError, TypeError)):
            first.extra = "value"

    def test_published_at_may_be_none(self) -> None:
        record = PublicJobRecord(**values(published_at=None))
        self.assertIsNone(record.published_at)

    def test_string_fields_require_exact_str_type(self) -> None:
        for name in LIMITS:
            for invalid in (1, None, StringSubclass("text")):
                with self.subTest(name=name, invalid=type(invalid).__name__):
                    supplied = values(**{name: invalid})
                    with self.assertRaises(TypeError):
                        PublicJobRecord(**supplied)

    def test_datetimes_require_exact_datetime_type(self) -> None:
        subclass = DateTimeSubclass(2026, 8, 14, tzinfo=timezone.utc)
        for name, invalid in (
            ("observed_at", "2026-08-14T00:00:00Z"),
            ("observed_at", subclass),
            ("published_at", "2026-08-13T00:00:00Z"),
            ("published_at", subclass),
        ):
            with self.subTest(name=name, invalid=type(invalid).__name__):
                with self.assertRaises(TypeError):
                    PublicJobRecord(**values(**{name: invalid}))

    def test_strings_reject_empty_and_surrounding_whitespace(self) -> None:
        for name in LIMITS:
            for invalid in ("", " value", "value ", "\tvalue"):
                with self.subTest(name=name, invalid=repr(invalid)):
                    with self.assertRaises(ValueError):
                        PublicJobRecord(**values(**{name: invalid}))

    def test_short_text_fields_reject_controls(self) -> None:
        for name in set(LIMITS) - {"description_text"}:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    PublicJobRecord(**values(**{name: "safe\x00text"}))

    def test_description_allows_newline_and_tab_but_other_controls_fail(self) -> None:
        text = "First line\n\tIndented line\nLast line"
        record = PublicJobRecord(**values(description_text=text))
        self.assertEqual(text, record.description_text)
        for invalid in ("text\x00value", "text\rvalue", "text\x1fvalue"):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(ValueError):
                    PublicJobRecord(**values(description_text=invalid))

    def test_every_string_length_boundary_is_inclusive(self) -> None:
        for name, limit in LIMITS.items():
            at_limit = "x" * limit
            if name == "source_url":
                prefix = "https://example.org/"
                at_limit = prefix + "x" * (limit - len(prefix))
            with self.subTest(name=name, boundary="accepted"):
                record = PublicJobRecord(**values(**{name: at_limit}))
                self.assertEqual(limit, len(getattr(record, name)))
            with self.subTest(name=name, boundary="rejected"):
                with self.assertRaises(ValueError):
                    PublicJobRecord(**values(**{name: at_limit + "x"}))

    def test_url_failures(self) -> None:
        credential_url = "https://" + "user" + "@" + "example.org/job"
        password_url = "https://" + "user" + ":secret" + "@" + "example.org/job"
        invalid_urls = (
            "example.org/job",
            "/relative/job",
            "ftp://example.org/job",
            "https:///job",
            "https://",
            "https://example.org/a b",
            "https://example.org/a\nb",
            credential_url,
            password_url,
            "https://example.org:invalid/job",
            "https://[invalid/job",
        )
        for source_url in invalid_urls:
            with self.subTest(source_url=source_url):
                with self.assertRaises(ValueError):
                    PublicJobRecord(**values(source_url=source_url))

    def test_url_rejects_malformed_dns_hostnames(self) -> None:
        for source_url in (
            "https://./job",
            "https://example..org/job",
            "https://.example.org/job",
        ):
            with self.subTest(source_url=source_url):
                with self.assertRaises(ValueError):
                    PublicJobRecord(**values(source_url=source_url))

    def test_url_accepts_dns_idna_and_ip_hosts(self) -> None:
        for source_url in (
            "https://jobs.example.org/job",
            "https://b\N{LATIN SMALL LETTER U WITH DIAERESIS}cher.example/job",
            "https://192.0.2.1/job",
            "https://[2001:db8::1]/job",
        ):
            with self.subTest(source_url=source_url):
                record = PublicJobRecord(**values(source_url=source_url))
                self.assertIs(record.source_url, source_url)

    def test_url_accepts_idna_dot_separator_without_replacing_source(self) -> None:
        source_url = "https://jobs\N{IDEOGRAPHIC FULL STOP}example.org/job"

        record = PublicJobRecord(**values(source_url=source_url))

        self.assertIs(record.source_url, source_url)
        self.assertEqual(record.source_url, source_url)

    def test_datetimes_must_be_timezone_aware(self) -> None:
        naive = datetime(2026, 8, 14, 12, 30)
        for name in ("observed_at", "published_at"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    PublicJobRecord(**values(**{name: naive}))

    def test_chronology_uses_instants_and_allows_equality(self) -> None:
        observed = datetime(2026, 8, 14, 12, tzinfo=timezone.utc)
        equal = datetime(
            2026, 8, 14, 9, tzinfo=timezone(timedelta(hours=-3))
        )
        self.assertEqual(
            equal,
            PublicJobRecord(
                **values(observed_at=observed, published_at=equal)
            ).published_at,
        )
        later = observed + timedelta(microseconds=1)
        with self.assertRaises(ValueError):
            PublicJobRecord(**values(observed_at=observed, published_at=later))

    def test_chronology_compares_instants_across_a_fold(self) -> None:
        shared_timezone = FoldAwareTimezone()
        observed = datetime(2026, 11, 1, 1, 30, tzinfo=shared_timezone, fold=0)
        published = datetime(2026, 11, 1, 1, 30, tzinfo=shared_timezone, fold=1)

        with self.assertRaises(ValueError):
            PublicJobRecord(
                **values(observed_at=observed, published_at=published)
            )

    def test_rejects_instead_of_transforming(self) -> None:
        cases = (
            {"title": " Trim me "},
            {"source_url": "HTTPS://EXAMPLE.ORG/job "},
            {"observed_at": "2026-08-14T12:30:00+00:00"},
        )
        for updates in cases:
            with self.subTest(updates=updates):
                with self.assertRaises((TypeError, ValueError)):
                    PublicJobRecord(**values(**updates))


if __name__ == "__main__":
    unittest.main()
