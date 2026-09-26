# Synthetic Readiness Demo

## What a reviewer can see

Four fictional examples show how a small deterministic policy handles declared
requirements and evidence. The output identifies central gaps, preserves
secondary and responsibility-only items, and always requires human review. It
does not assess a real person or job and never recommends applying.

This is a **synthetic portfolio demonstration**, not the private operational
Candidate Readiness model. It uses no network, model provider, semantic text
inference, employer ranking, weighted score, or application history.

## Run the examples

Use Python 3.11 or newer from the repository root:

```sh
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/ready_now.json
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/moderate_gaps.json
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/future_target.json
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/insufficient_evidence.json
```

The four outputs respectively show `READY_NOW`, `READY_WITH_MODERATE_GAPS`,
`FUTURE_TARGET`, and `INSUFFICIENT_EVIDENCE`. These names describe only the
fictional input under this demo policy. They are not hiring judgments.

## Input contract

One JSON object contains exactly `schema_version` (integer `1`), `synthetic`
(`true`), `assessment_id`, `coverage_state`, `requirements`,
`candidate_evidence`, and `links`. Extra or missing fields fail validation.
Coverage is `COMPLETE`, `PARTIAL`, or `UNKNOWN`. A false or missing synthetic
marker fails validation.

Each requirement declares an ID, statement, centrality, and evidence
expectation. Centrality is `CENTRAL`, `SECONDARY`, `RESPONSIBILITY_ONLY`, or
`UNKNOWN`. Only central requirements determine the readiness state. Secondary
items are reported without independently blocking readiness; responsibility
items do not create a candidate gap. Unknown centrality blocks an optimistic
state. Expectations are `GENERAL`, `PROFESSIONAL`, or `PRODUCTION` and are never
inferred from the statement.

Each evidence item declares an ID, statement, evidence level, production scope,
and explicit limitations list. Levels are `PROFESSIONAL`, `PROJECT`, and
`EDUCATION`. Production scope is `PRODUCTION`, `NOT_PRODUCTION`, or
`NOT_DECLARED`. Project and education evidence cannot declare production scope.
An empty limitations list means `NO_LIMITATIONS_DECLARED`; it does not mean
unrestricted skill, authority, or production experience.

Every requirement has exactly one link with its ID, evidence IDs, and one
support state: `DIRECT`, `PARTIAL`, `CONTEXT_ONLY`, `NOT_EVIDENCED`, or
`UNKNOWN`. IDs must exist and cannot repeat. The first three states require
at least one evidence ID; the last two require none. A `DIRECT` professional
link may reference only professional evidence. A `DIRECT` production link may
reference only professional evidence explicitly marked `PRODUCTION`. Project
and education evidence can still be explicitly marked partial or contextual.
Free-text wording never changes these structural declarations.

## Deterministic policy

Incomplete or unknown coverage, no central requirements, unknown central
support, or unknown centrality yields `INSUFFICIENT_EVIDENCE`. With complete
coverage, any central `NOT_EVIDENCED` yields `FUTURE_TARGET`; otherwise any
central `PARTIAL` or `CONTEXT_ONLY` yields `READY_WITH_MODERATE_GAPS`;
otherwise all central links are `DIRECT` and the result is `READY_NOW`.
This conservative order is a demo contract, not a universal hiring rule.

Output preserves the characterized requirements, evidence, support states,
limitations, and coverage. It always includes `HUMAN_REVIEW_REQUIRED=YES` and
`NO_APPLICATION_RECOMMENDATION=YES`. Declared evidence does not prove
capability, and missing evidence does not prove inability. A reviewer must
check the underlying claims and their relevance before drawing any conclusion.
