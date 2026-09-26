from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from ai_job_radar import public_sanitizer
from ai_job_radar.synthetic_readiness import (
    ValidationError,
    evaluate_assessment,
    load_assessment,
    serialize_result,
    validate_assessment,
)


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/demo_readiness_cases"
PROHIBITED_OUTPUT_TOKENS = {
    "score", "scores", "scored", "scoring", "percent", "percentage",
    "probability", "probabilities", "likelihood", "chance", "chances",
}


def fixture(name: str = "ready_now") -> dict:
    return json.loads((CASES / f"{name}.json").read_text(encoding="utf-8"))


class SyntheticReadinessTests(unittest.TestCase):
    def assert_no_scoring_fields(self, value: object, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                self.assertIsInstance(key, str, f"non-string output key at {path}")
                normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
                tokens = set(re.findall(r"[a-z]+", normalized.casefold()))
                self.assertFalse(
                    tokens & PROHIBITED_OUTPUT_TOKENS or key == "recommendation",
                    f"prohibited output field at {path}.{key}",
                )
                self.assert_no_scoring_fields(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self.assert_no_scoring_fields(child, f"{path}[{index}]")

    def assert_invalid(self, value: dict) -> None:
        with self.assertRaises(ValidationError):
            validate_assessment(value)

    def test_four_documented_states(self) -> None:
        expected = {
            "ready_now": "READY_NOW",
            "moderate_gaps": "READY_WITH_MODERATE_GAPS",
            "future_target": "FUTURE_TARGET",
            "insufficient_evidence": "INSUFFICIENT_EVIDENCE",
        }
        for name, state in expected.items():
            with self.subTest(name=name):
                self.assertEqual(state, evaluate_assessment(load_assessment(CASES / f"{name}.json"))["readiness_state"])

    def test_coverage_and_unknowns_fail_closed(self) -> None:
        for coverage in ("PARTIAL", "UNKNOWN"):
            value = fixture()
            value["coverage_state"] = coverage
            self.assertEqual("INSUFFICIENT_EVIDENCE", evaluate_assessment(value)["readiness_state"])
        value = fixture()
        value["requirements"][0]["centrality"] = "UNKNOWN"
        self.assertEqual("INSUFFICIENT_EVIDENCE", evaluate_assessment(value)["readiness_state"])
        value = fixture()
        for item in value["requirements"]:
            item["centrality"] = "SECONDARY"
        self.assertEqual("INSUFFICIENT_EVIDENCE", evaluate_assessment(value)["readiness_state"])
        value = fixture()
        value["links"][0] = {"requirement_id": "r1", "evidence_ids": [], "support_state": "UNKNOWN"}
        self.assertEqual("INSUFFICIENT_EVIDENCE", evaluate_assessment(value)["readiness_state"])

    def test_secondary_and_responsibility_gaps_do_not_downgrade(self) -> None:
        result = evaluate_assessment(fixture())
        self.assertEqual("READY_NOW", result["readiness_state"])
        self.assertEqual("NOT_EVIDENCED", result["secondary_requirements"][0]["support_state"])
        self.assertEqual("NOT_EVIDENCED", result["responsibility_only_requirements"][0]["support_state"])

    def test_direct_professional_boundary(self) -> None:
        for level in ("PROJECT", "EDUCATION"):
            value = fixture("moderate_gaps")
            value["requirements"][1]["evidence_expectation"] = "PROFESSIONAL"
            value["candidate_evidence"][0]["evidence_level"] = level
            value["links"][1]["support_state"] = "DIRECT"
            with self.subTest(level=level):
                self.assert_invalid(value)

    def test_direct_production_boundary(self) -> None:
        for level, scope in (
            ("PROJECT", "NOT_PRODUCTION"),
            ("EDUCATION", "NOT_DECLARED"),
            ("PROFESSIONAL", "NOT_PRODUCTION"),
            ("PROFESSIONAL", "NOT_DECLARED"),
        ):
            value = fixture("future_target")
            value["candidate_evidence"][0]["evidence_level"] = level
            value["candidate_evidence"][0]["production_scope"] = scope
            value["links"][0] = {"requirement_id": "r1", "evidence_ids": ["e1"], "support_state": "DIRECT"}
            with self.subTest(level=level, scope=scope):
                self.assert_invalid(value)

    def test_mixed_direct_evidence_fails_if_any_item_exceeds_scope(self) -> None:
        value = fixture()
        value["links"][1]["evidence_ids"].append("e1")
        self.assert_invalid(value)

    def test_partial_project_and_education_remain_allowed(self) -> None:
        value = fixture("moderate_gaps")
        self.assertEqual("READY_WITH_MODERATE_GAPS", evaluate_assessment(value)["readiness_state"])
        value["candidate_evidence"][0]["evidence_level"] = "EDUCATION"
        self.assertEqual("READY_WITH_MODERATE_GAPS", evaluate_assessment(value)["readiness_state"])

    def test_empty_limitations_and_text_do_not_grant_scope(self) -> None:
        value = fixture("future_target")
        value["candidate_evidence"][0]["limitations"] = []
        value["candidate_evidence"][0]["statement"] = "Fictional text claims production authority."
        result = evaluate_assessment(value)
        self.assertEqual("NO_LIMITATIONS_DECLARED", result["evidence_summary"][0]["limitations_state"])
        self.assertEqual("FUTURE_TARGET", result["readiness_state"])
        value["links"][0] = {"requirement_id": "r1", "evidence_ids": ["e1"], "support_state": "DIRECT"}
        self.assert_invalid(value)

    def test_schema_and_link_integrity(self) -> None:
        modifications = (
            lambda v: v.update(extra=True),
            lambda v: v.pop("synthetic"),
            lambda v: v.update(synthetic=False),
            lambda v: v.update(schema_version=True),
            lambda v: v.update(coverage_state="READY"),
            lambda v: v["requirements"][0].update(extra=True),
            lambda v: v["requirements"][1].update(requirement_id="r1"),
            lambda v: v["candidate_evidence"][1].update(evidence_id="e1"),
            lambda v: v["links"].append(copy.deepcopy(v["links"][0])),
            lambda v: v["links"][0].update(evidence_ids=["e1", "e1"]),
            lambda v: v["links"][0].update(evidence_ids=["missing"]),
            lambda v: v["links"].pop(),
            lambda v: v["links"][0].update(evidence_ids=[]),
            lambda v: v["links"][2].update(evidence_ids=["e1"]),
            lambda v: v["candidate_evidence"][0].update(production_scope="PRODUCTION"),
        )
        for modify in modifications:
            value = fixture()
            modify(value)
            with self.subTest(modify=repr(modify)):
                self.assert_invalid(value)

    def test_output_contract_and_determinism(self) -> None:
        result = evaluate_assessment(fixture())
        self.assertEqual("YES", result["HUMAN_REVIEW_REQUIRED"])
        self.assertEqual("YES", result["NO_APPLICATION_RECOMMENDATION"])
        self.assertEqual("VALID", result["validation"])
        self.assertEqual(serialize_result(result), serialize_result(evaluate_assessment(fixture())))
        self.assertEqual(result, json.loads(serialize_result(result)))
        for name in ("ready_now", "moderate_gaps", "future_target", "insufficient_evidence"):
            with self.subTest(name=name):
                self.assert_no_scoring_fields(evaluate_assessment(fixture(name)))

    def test_output_scoring_guard_rejects_adversarial_fields(self) -> None:
        result = evaluate_assessment(fixture())
        for key, nested in (
            ("readiness_score", False),
            ("hiring_probability", True),
            ("match_percentage", True),
            ("interview_probability", False),
        ):
            mutated = copy.deepcopy(result)
            target = mutated["central_requirements"][0] if nested else mutated
            target[key] = 0.5
            with self.subTest(key=key, nested=nested):
                with self.assertRaises(AssertionError):
                    self.assert_no_scoring_fields(mutated)

    def test_cli_and_sanitizer_on_synthetic_fixtures(self) -> None:
        for path in sorted(CASES.glob("*.json")):
            command = [sys.executable, "-m", "ai_job_radar.synthetic_readiness", "--assessment", str(path)]
            completed = subprocess.run(command, cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=False)
            with self.subTest(path=path.name):
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertEqual("YES", json.loads(completed.stdout)["HUMAN_REVIEW_REQUIRED"])
                self.assertEqual([], public_sanitizer.scan_repository(ROOT, [str(path.relative_to(ROOT))]))

    def test_sanitizer_rejects_nested_fixture_without_provenance(self) -> None:
        path = CASES / "ready_now.json"
        altered = path.read_text(encoding="utf-8").replace('"synthetic": true', '"synthetic": false')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "data/demo_readiness_cases/ready_now.json"
            target.parent.mkdir(parents=True)
            target.write_text(altered, encoding="utf-8")
            findings = public_sanitizer.scan_repository(root, ["data/demo_readiness_cases/ready_now.json"])
        self.assertIn("synthetic-provenance", [finding.category for finding in findings])


if __name__ == "__main__":
    unittest.main()
