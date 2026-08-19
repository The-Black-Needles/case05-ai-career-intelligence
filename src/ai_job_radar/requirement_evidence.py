"""Deterministic validation and factual assessment of synthetic evidence links."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIREMENT_TYPES = ("MANDATORY", "PREFERRED", "DIFFERENTIAL", "CONTEXTUAL")
LINKED = "EXPLICIT_EVIDENCE_LINKED"
NO_LINK = "NO_EXPLICIT_EVIDENCE_LINK"


class ValidationError(ValueError):
    """Raised when a synthetic assessment does not meet the public contract."""


def load_assessment(path: str | Path) -> dict[str, Any]:
    """Load and strictly validate one UTF-8 JSON assessment file."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("invalid assessment JSON") from error
    return validate_assessment(value)


def validate_assessment(value: Any) -> dict[str, Any]:
    """Fail closed unless *value* exactly satisfies the assessment schema."""
    _exact_object(value, ("schema_version", "synthetic", "assessment_id", "requirements", "candidate_evidence", "links"), "assessment")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValidationError("schema_version must be the JSON integer 1")
    if value["synthetic"] is not True:
        raise ValidationError("synthetic must be JSON true")
    _nonblank_string(value["assessment_id"], "assessment_id")
    _list(value["requirements"], "requirements")
    _list(value["candidate_evidence"], "candidate_evidence")
    _list(value["links"], "links")

    requirement_ids: set[str] = set()
    for requirement in value["requirements"]:
        _exact_object(requirement, ("requirement_id", "requirement_type", "statement"), "requirement")
        requirement_id = _nonblank_string(requirement["requirement_id"], "requirement_id")
        if requirement_id in requirement_ids:
            raise ValidationError("duplicate requirement_id")
        requirement_ids.add(requirement_id)
        if requirement["requirement_type"] not in REQUIREMENT_TYPES:
            raise ValidationError("invalid requirement_type")
        _nonblank_string(requirement["statement"], "requirement statement")

    evidence_ids: set[str] = set()
    for evidence in value["candidate_evidence"]:
        _exact_object(evidence, ("evidence_id", "statement"), "candidate evidence")
        evidence_id = _nonblank_string(evidence["evidence_id"], "evidence_id")
        if evidence_id in evidence_ids:
            raise ValidationError("duplicate evidence_id")
        evidence_ids.add(evidence_id)
        _nonblank_string(evidence["statement"], "evidence statement")

    linked_requirement_ids: set[str] = set()
    for link in value["links"]:
        _exact_object(link, ("requirement_id", "evidence_ids"), "link")
        requirement_id = _nonblank_string(link["requirement_id"], "link requirement_id")
        if requirement_id not in requirement_ids:
            raise ValidationError("link references unknown requirement_id")
        if requirement_id in linked_requirement_ids:
            raise ValidationError("duplicate link requirement_id")
        linked_requirement_ids.add(requirement_id)
        _list(link["evidence_ids"], "link evidence_ids")
        linked_evidence_ids: set[str] = set()
        for evidence_id in link["evidence_ids"]:
            _nonblank_string(evidence_id, "link evidence_id")
            if evidence_id not in evidence_ids:
                raise ValidationError("link references unknown evidence_id")
            if evidence_id in linked_evidence_ids:
                raise ValidationError("duplicate evidence_id in link")
            linked_evidence_ids.add(evidence_id)
    if linked_requirement_ids != requirement_ids:
        raise ValidationError("missing link for declared requirement_id")
    return value


def evaluate_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
    """Return the fixed factual output for an already-valid assessment."""
    validate_assessment(assessment)
    links = {link["requirement_id"]: link["evidence_ids"] for link in assessment["links"]}
    counts = {
        requirement_type: {
            "total_requirements": 0,
            "with_explicit_evidence_link": 0,
            "without_explicit_evidence_link": 0,
        }
        for requirement_type in REQUIREMENT_TYPES
    }
    requirements = []
    for requirement in assessment["requirements"]:
        evidence_ids = links[requirement["requirement_id"]]
        linkage_state = LINKED if evidence_ids else NO_LINK
        count = counts[requirement["requirement_type"]]
        count["total_requirements"] += 1
        count[
            "with_explicit_evidence_link" if evidence_ids else "without_explicit_evidence_link"
        ] += 1
        requirements.append(
            {
                "requirement_id": requirement["requirement_id"],
                "requirement_type": requirement["requirement_type"],
                "statement": requirement["statement"],
                "evidence_ids": evidence_ids,
                "linkage_state": linkage_state,
            }
        )
    return {
        "assessment_id": assessment["assessment_id"],
        "validation": "VALID",
        "requirements": requirements,
        "raw_counts_by_requirement_type": counts,
        "limitations": [
            "Explicit linkage does not establish requirement satisfaction or capability.",
            "No scoring, readiness, ranking, eligibility, or recommendation is produced.",
            "Human review determines relevance, sufficiency, and persuasiveness.",
        ],
        "HUMAN_REVIEW_REQUIRED": "YES",
    }


def serialize_result(result: dict[str, Any]) -> str:
    """Serialize a result using the canonical public-demo representation."""
    return json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _exact_object(value: Any, fields: tuple[str, ...], label: str) -> None:
    if type(value) is not dict:
        raise ValidationError(f"{label} must be an object")
    if set(value) != set(fields):
        raise ValidationError(f"{label} fields must be exactly: {', '.join(fields)}")


def _list(value: Any, label: str) -> None:
    if type(value) is not list:
        raise ValidationError(f"{label} must be a list")


def _nonblank_string(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValidationError(f"{label} must be a non-blank string")
    return value
