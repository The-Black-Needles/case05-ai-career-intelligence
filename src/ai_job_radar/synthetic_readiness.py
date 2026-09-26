"""Deterministic readiness characterization for wholly synthetic assessments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


CENTRALITIES = ("CENTRAL", "SECONDARY", "RESPONSIBILITY_ONLY", "UNKNOWN")
EXPECTATIONS = ("GENERAL", "PROFESSIONAL", "PRODUCTION")
EVIDENCE_LEVELS = ("PROFESSIONAL", "PROJECT", "EDUCATION")
PRODUCTION_SCOPES = ("PRODUCTION", "NOT_PRODUCTION", "NOT_DECLARED")
SUPPORT_STATES = ("DIRECT", "PARTIAL", "CONTEXT_ONLY", "NOT_EVIDENCED", "UNKNOWN")


class ValidationError(ValueError):
    """The synthetic input contradicts or fails the public contract."""


def _object(value: Any, fields: set[str], label: str) -> None:
    if type(value) is not dict or set(value) != fields:
        raise ValidationError(f"{label} must have exactly the required fields")


def _string(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValidationError(f"{label} must be a nonblank string")
    return value


def _choice(value: Any, choices: tuple[str, ...], label: str) -> None:
    if type(value) is not str or value not in choices:
        raise ValidationError(f"{label} has an invalid value")


def _list(value: Any, label: str) -> None:
    if type(value) is not list:
        raise ValidationError(f"{label} must be a list")


def validate_assessment(value: Any) -> dict[str, Any]:
    """Validate shape, identifiers, links, and declared evidence boundaries."""
    _object(value, {"schema_version", "synthetic", "assessment_id", "coverage_state", "requirements", "candidate_evidence", "links"}, "assessment")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValidationError("schema_version must be the JSON integer 1")
    if value["synthetic"] is not True:
        raise ValidationError("synthetic must be JSON true")
    _string(value["assessment_id"], "assessment_id")
    _choice(value["coverage_state"], ("COMPLETE", "PARTIAL", "UNKNOWN"), "coverage_state")
    for key in ("requirements", "candidate_evidence", "links"):
        _list(value[key], key)

    requirements: dict[str, dict[str, Any]] = {}
    for item in value["requirements"]:
        _object(item, {"requirement_id", "statement", "centrality", "evidence_expectation"}, "requirement")
        identifier = _string(item["requirement_id"], "requirement_id")
        if identifier in requirements:
            raise ValidationError("duplicate requirement_id")
        _string(item["statement"], "requirement statement")
        _choice(item["centrality"], CENTRALITIES, "centrality")
        _choice(item["evidence_expectation"], EXPECTATIONS, "evidence_expectation")
        requirements[identifier] = item

    evidence: dict[str, dict[str, Any]] = {}
    for item in value["candidate_evidence"]:
        _object(item, {"evidence_id", "statement", "evidence_level", "production_scope", "limitations"}, "candidate evidence")
        identifier = _string(item["evidence_id"], "evidence_id")
        if identifier in evidence:
            raise ValidationError("duplicate evidence_id")
        _string(item["statement"], "evidence statement")
        _choice(item["evidence_level"], EVIDENCE_LEVELS, "evidence_level")
        _choice(item["production_scope"], PRODUCTION_SCOPES, "production_scope")
        if item["evidence_level"] != "PROFESSIONAL" and item["production_scope"] == "PRODUCTION":
            raise ValidationError("non-professional evidence cannot declare production scope")
        _list(item["limitations"], "limitations")
        for limitation in item["limitations"]:
            _string(limitation, "limitation")
        evidence[identifier] = item

    linked_ids: set[str] = set()
    for link in value["links"]:
        _object(link, {"requirement_id", "evidence_ids", "support_state"}, "link")
        identifier = _string(link["requirement_id"], "link requirement_id")
        if identifier not in requirements:
            raise ValidationError("link references unknown requirement_id")
        if identifier in linked_ids:
            raise ValidationError("duplicate link requirement_id")
        linked_ids.add(identifier)
        _choice(link["support_state"], SUPPORT_STATES, "support_state")
        _list(link["evidence_ids"], "link evidence_ids")
        seen: set[str] = set()
        for evidence_id in link["evidence_ids"]:
            _string(evidence_id, "link evidence_id")
            if evidence_id not in evidence:
                raise ValidationError("link references unknown evidence_id")
            if evidence_id in seen:
                raise ValidationError("duplicate evidence_id in link")
            seen.add(evidence_id)
        state = link["support_state"]
        if state in ("DIRECT", "PARTIAL", "CONTEXT_ONLY") and not seen:
            raise ValidationError("support state requires evidence IDs")
        if state in ("NOT_EVIDENCED", "UNKNOWN") and seen:
            raise ValidationError("unresolved or absent support cannot declare evidence IDs")
        if state == "DIRECT":
            expectation = requirements[identifier]["evidence_expectation"]
            for evidence_id in seen:
                item = evidence[evidence_id]
                if expectation in ("PROFESSIONAL", "PRODUCTION") and item["evidence_level"] != "PROFESSIONAL":
                    raise ValidationError("DIRECT support requires professional evidence")
                if expectation == "PRODUCTION" and item["production_scope"] != "PRODUCTION":
                    raise ValidationError("DIRECT support requires declared production scope")
    if linked_ids != set(requirements):
        raise ValidationError("missing link for declared requirement_id")
    return value


def load_assessment(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("invalid assessment JSON") from error
    return validate_assessment(value)


def evaluate_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
    """Apply the declared synthetic policy; no text interpretation occurs."""
    validate_assessment(assessment)
    links = {link["requirement_id"]: link for link in assessment["links"]}
    groups: dict[str, list[dict[str, Any]]] = {key: [] for key in CENTRALITIES}
    for requirement in assessment["requirements"]:
        link = links[requirement["requirement_id"]]
        groups[requirement["centrality"]].append({
            **requirement,
            "support_state": link["support_state"],
            "evidence_ids": link["evidence_ids"],
        })
    central = groups["CENTRAL"]
    states = {item["support_state"] for item in central}
    if assessment["coverage_state"] != "COMPLETE" or not central or groups["UNKNOWN"] or "UNKNOWN" in states:
        readiness = "INSUFFICIENT_EVIDENCE"
    elif "NOT_EVIDENCED" in states:
        readiness = "FUTURE_TARGET"
    elif states & {"PARTIAL", "CONTEXT_ONLY"}:
        readiness = "READY_WITH_MODERATE_GAPS"
    else:
        readiness = "READY_NOW"
    return {
        "assessment_id": assessment["assessment_id"],
        "validation": "VALID",
        "coverage_state": assessment["coverage_state"],
        "readiness_state": readiness,
        "central_requirements": groups["CENTRAL"],
        "secondary_requirements": groups["SECONDARY"],
        "responsibility_only_requirements": groups["RESPONSIBILITY_ONLY"],
        "unknown_requirements": groups["UNKNOWN"],
        "evidence_summary": [
            {**item, "limitations_state": "DECLARED" if item["limitations"] else "NO_LIMITATIONS_DECLARED"}
            for item in assessment["candidate_evidence"]
        ],
        "requirement_support_summary": [
            {"requirement_id": item["requirement_id"], "support_state": links[item["requirement_id"]]["support_state"]}
            for item in assessment["requirements"]
        ],
        "limitations": [
            "Synthetic characterization is not a hiring or application decision.",
            "Declared evidence and empty limitation lists do not establish unrestricted capability.",
            "Human review must verify relevance, sufficiency, and the underlying claims.",
        ],
        "HUMAN_REVIEW_REQUIRED": "YES",
        "NO_APPLICATION_RECOMMENDATION": "YES",
    }


def serialize_result(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Characterize one wholly synthetic readiness assessment.")
    parser.add_argument("--assessment", required=True, help="Path to a synthetic assessment JSON file.")
    args = parser.parse_args()
    try:
        result = evaluate_assessment(load_assessment(args.assessment))
    except ValidationError as error:
        sys.stderr.write(json.dumps({"error": "VALIDATION_ERROR", "message": str(error)}, sort_keys=True, indent=2) + "\n")
        return 2
    sys.stdout.write(serialize_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
