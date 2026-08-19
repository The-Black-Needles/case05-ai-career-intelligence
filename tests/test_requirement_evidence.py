from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ai_job_radar.requirement_evidence import (
    LINKED,
    NO_LINK,
    ValidationError,
    evaluate_assessment,
    load_assessment,
    serialize_result,
    validate_assessment,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/demo_assessment.json"


def assessment() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class RequirementEvidenceTests(unittest.TestCase):
    def assert_invalid(self, value: object) -> None:
        with self.assertRaises(ValidationError):
            validate_assessment(value)

    def test_fixture_happy_path_preserves_order_and_explicit_links(self) -> None:
        loaded = load_assessment(FIXTURE)
        result = evaluate_assessment(loaded)
        self.assertEqual("VALID", result["validation"])
        self.assertEqual("YES", result["HUMAN_REVIEW_REQUIRED"])
        self.assertEqual(
            ["MANDATORY", "PREFERRED", "DIFFERENTIAL", "CONTEXTUAL"],
            list(result["raw_counts_by_requirement_type"]),
        )
        requirements = result["requirements"]
        self.assertEqual("requirement_synthetic_core", requirements[0]["requirement_id"])
        self.assertEqual(LINKED, requirements[0]["linkage_state"])
        self.assertEqual(NO_LINK, requirements[2]["linkage_state"])
        self.assertEqual([], requirements[2]["evidence_ids"])
        self.assertIn("evidence_synthetic_component_work", requirements[0]["evidence_ids"])
        self.assertIn("evidence_synthetic_component_work", requirements[1]["evidence_ids"])
        expected_counts = {
            "MANDATORY": {
                "total_requirements": 1,
                "with_explicit_evidence_link": 1,
                "without_explicit_evidence_link": 0,
            },
            "PREFERRED": {
                "total_requirements": 1,
                "with_explicit_evidence_link": 1,
                "without_explicit_evidence_link": 0,
            },
            "DIFFERENTIAL": {
                "total_requirements": 1,
                "with_explicit_evidence_link": 0,
                "without_explicit_evidence_link": 1,
            },
            "CONTEXTUAL": {
                "total_requirements": 1,
                "with_explicit_evidence_link": 1,
                "without_explicit_evidence_link": 0,
            },
        }
        self.assertEqual(expected_counts, result["raw_counts_by_requirement_type"])
        for requirement_type, expected_count in expected_counts.items():
            with self.subTest(requirement_type=requirement_type):
                actual_count = result["raw_counts_by_requirement_type"][requirement_type]
                self.assertEqual(
                    expected_count["total_requirements"],
                    actual_count["with_explicit_evidence_link"]
                    + actual_count["without_explicit_evidence_link"],
                )

    def test_shape_and_top_level_policies_fail_closed(self) -> None:
        for label, mutate in (
            ("extra", lambda item: item.update(extra=True)),
            ("missing", lambda item: item.pop("links")),
            ("wrong-list", lambda item: item.__setitem__("requirements", {})),
            ("bool-version", lambda item: item.__setitem__("schema_version", True)),
            ("wrong-version", lambda item: item.__setitem__("schema_version", 2)),
            ("false-synthetic", lambda item: item.__setitem__("synthetic", False)),
            ("missing-synthetic", lambda item: item.pop("synthetic")),
        ):
            with self.subTest(label=label):
                value = assessment()
                mutate(value)
                self.assert_invalid(value)
        self.assert_invalid([])

    def test_nested_shape_and_values_fail_closed(self) -> None:
        cases = (
            lambda item: item["requirements"][0].update(extra=True),
            lambda item: item["requirements"][0].pop("statement"),
            lambda item: item["requirements"].__setitem__(0, []),
            lambda item: item["candidate_evidence"].__setitem__(0, {"evidence_id": "x", "statement": 1}),
            lambda item: item["links"][0].__setitem__("evidence_ids", "x"),
            lambda item: item["requirements"][0].__setitem__("requirement_type", "mandatory"),
            lambda item: item["requirements"][0].__setitem__("requirement_id", ""),
            lambda item: item["requirements"][0].__setitem__("requirement_id", " \t"),
            lambda item: item["requirements"][0].__setitem__("statement", ""),
            lambda item: item["candidate_evidence"][0].__setitem__("statement", "\n"),
        )
        for mutate in cases:
            with self.subTest(mutate=repr(mutate)):
                value = assessment()
                mutate(value)
                self.assert_invalid(value)

    def test_identifier_and_link_invariants_fail_closed(self) -> None:
        cases = (
            lambda item: item["requirements"][1].__setitem__("requirement_id", item["requirements"][0]["requirement_id"]),
            lambda item: item["candidate_evidence"][1].__setitem__("evidence_id", item["candidate_evidence"][0]["evidence_id"]),
            lambda item: item["links"].append(copy.deepcopy(item["links"][0])),
            lambda item: item["links"][0].__setitem__("evidence_ids", [item["candidate_evidence"][0]["evidence_id"], item["candidate_evidence"][0]["evidence_id"]]),
            lambda item: item["links"][0].__setitem__("requirement_id", "unknown"),
            lambda item: item["links"][0].__setitem__("evidence_ids", ["unknown"]),
            lambda item: item["links"].pop(),
        )
        for mutate in cases:
            with self.subTest(mutate=repr(mutate)):
                value = assessment()
                mutate(value)
                self.assert_invalid(value)

    def test_valid_strings_remain_unchanged_and_result_boundary_is_exact(self) -> None:
        value = assessment()
        value["assessment_id"] = " assessment preserved "
        value["requirements"][0]["statement"] = " statement preserved "
        result = evaluate_assessment(value)
        self.assertEqual(" assessment preserved ", result["assessment_id"])
        self.assertEqual(" statement preserved ", result["requirements"][0]["statement"])
        self.assertEqual(
            {"assessment_id", "validation", "requirements", "raw_counts_by_requirement_type", "limitations", "HUMAN_REVIEW_REQUIRED"},
            set(result),
        )
        self.assertEqual(
            {"requirement_id", "requirement_type", "statement", "evidence_ids", "linkage_state"},
            set(result["requirements"][0]),
        )
        for count in result["raw_counts_by_requirement_type"].values():
            self.assertEqual(
                {"total_requirements", "with_explicit_evidence_link", "without_explicit_evidence_link"},
                set(count),
            )
        forbidden_fields = {"score", "readiness", "ranking", "recommendation", "eligibility"}
        self.assertTrue(forbidden_fields.isdisjoint(result))
        for requirement in result["requirements"]:
            self.assertNotIn("satisfied", requirement)
            self.assertNotIn("pass", requirement)
            self.assertIn(requirement["linkage_state"], {LINKED, NO_LINK})

    def test_result_and_serialization_are_deterministic(self) -> None:
        first = evaluate_assessment(assessment())
        second = evaluate_assessment(assessment())
        self.assertEqual(first, second)
        self.assertEqual(serialize_result(first), serialize_result(second))

        unicode_assessment = assessment()
        unicode_assessment["requirements"][0]["statement"] = "Experiência sintética com automação"
        expected_result = evaluate_assessment(unicode_assessment)
        expected_serialization = json.dumps(
            expected_result,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n"
        serialized = serialize_result(expected_result)

        self.assertEqual(expected_serialization, serialized)
        self.assertEqual(expected_result, json.loads(serialized))
        self.assertIn("Experiência sintética com automação", serialized)
        self.assertNotIn("\\u", serialized)
        self.assertTrue(serialized.endswith("\n"))
        self.assertFalse(serialized.endswith("\n\n"))

    def test_cli_success_and_validation_error(self) -> None:
        command = [sys.executable, "-m", "ai_job_radar.demo", "--assessment", str(FIXTURE)]
        environment = {"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
        success = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        self.assertEqual(0, success.returncode)
        self.assertEqual("", success.stderr)
        self.assertEqual("YES", json.loads(success.stdout)["HUMAN_REVIEW_REQUIRED"])
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "invalid.json"
            invalid.write_text("{}", encoding="utf-8")
            failure = subprocess.run(command[:-1] + [str(invalid)], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        self.assertEqual(2, failure.returncode)
        self.assertEqual("", failure.stdout)
        self.assertEqual("VALIDATION_ERROR", json.loads(failure.stderr)["error"])
        self.assertNotIn("Traceback", failure.stderr)


if __name__ == "__main__":
    unittest.main()
