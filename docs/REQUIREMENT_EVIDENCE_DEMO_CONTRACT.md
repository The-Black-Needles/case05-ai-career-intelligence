# Requirement/Evidence Demo Contract

## Status

**IMPLEMENTATION_STATUS=IMPLEMENTED_LOCAL_DEMO**

P5B froze this design contract as `DESIGN_CONTRACT_ONLY`. P5C implements only
its narrow deterministic synthetic subset locally: strict validation, explicit
ID linkage, factual linkage states, raw counts, and mandatory human review.
It is non-production and does not activate collection, semantic matching,
scoring, recommendation, AI/LLM, or agents.

## Purpose and boundary

The first future deterministic slice is limited to explicit synthetic
requirements, explicit synthetic candidate evidence, explicit linkage by IDs,
strict validation, factual linkage assessment, and traceable human-review
output. It performs no semantic inference or automatic matching.

It has no scoring, readiness calculation, ranking, recommendation, or
candidate/job decision. `SCORING_MODEL_V2` is not activated by this contract
and remains `DRAFT_NOT_ACTIVE`. No LLM, embeddings, classifier, agent,
external service, or AI-assisted feature is part of this contract.

## Implemented input bundle

One deterministic synthetic assessment bundle should contain an assessment ID,
requirements, candidate evidence, and explicit requirement/evidence links.
The bundle is intentionally small; no fixture is created by this contract.

### Requirements

Each requirement record has the conceptual fields `requirement_id`,
`requirement_type`, and `statement`. `requirement_id` is unique within the
assessment. The statement is supplied input: the runtime must not infer or
rewrite it.

The initial declarative requirement types are `MANDATORY`, `PREFERRED`,
`DIFFERENTIAL`, and `CONTEXTUAL`. They are input categories only. They do not
provide numeric weight, score, readiness contribution, automatic gate,
ranking, recommendation, or relative importance beyond their declared
category. A future runtime must not silently convert them into weights.

### Candidate evidence

Each candidate evidence record has the conceptual fields `evidence_id` and
`statement`; `evidence_id` is unique. Evidence is explicit supplied input, not
inferred from CV text or free-form profile text. This contract defines neither
evidence levels nor gap levels.

### Explicit linkage and validation

For every requirement, there is exactly one linkage record with
`requirement_id` and `evidence_ids`. `evidence_ids` is a list and may be
empty. This distinguishes a missing mapping from an explicit empty evidence
list. The same evidence may link to multiple requirements only through
explicitly declared links.

The future validator fails closed for unknown requirement or evidence IDs,
duplicate requirement or evidence IDs, duplicate linkage records for one
requirement, a missing linkage record for a declared requirement, and malformed
types. Explicit IDs are the only matching mechanism; the first slice performs
no semantic matching.

## Implemented factual assessment

After validation, a requirement may have only one of these factual linkage
states:

- `EXPLICIT_EVIDENCE_LINKED`: one or more explicitly supplied evidence IDs are
  linked to the requirement and every referenced ID passed validation. It does
  not mean the requirement is satisfied, evidence is sufficient, the candidate
  is capable or ready, or the candidate should apply.
- `NO_EXPLICIT_EVIDENCE_LINK`: the validated linkage record contains no
  evidence IDs. It does not mean the candidate lacks a skill or capability,
  the requirement is impossible to satisfy, or the candidate is unsuitable.

The absence of an explicit evidence link must never be interpreted as an
absence of capability: `NO_EXPLICIT_EVIDENCE_LINK != NO_CAPABILITY`.

The future demo may aggregate raw counts by requirement type, including counts
of requirements with and without explicit evidence links. For example, a
factual label may be `MANDATORY_WITH_EXPLICIT_EVIDENCE_LINK`. Counts are not
percentages of readiness and must not produce a readiness, fit, weighted,
confidence, suitability, or recommendation score.

## Human review and output

Every future output preserves `HUMAN_REVIEW_REQUIRED=YES`. It is decision
support, not autonomous career decision-making. The reviewer remains
responsible for deciding whether linked evidence is relevant, sufficient, and
persuasive.

Future output may contain the assessment ID, validation result, requirement
IDs, types, statements, linked evidence IDs, factual linkage states, raw counts
by type, limitations, and `HUMAN_REVIEW_REQUIRED=YES`. Every factual output is
traceable to explicit input IDs; no conclusion depends on hidden inference.

This contract produces none of the following candidate/job recommendation
states: `APPLY`, `APPLY_WITH_CAVEATS`, `DO_NOT_APPLY`, `ELIGIBLE`,
`INELIGIBLE`, `READY`, `NOT_READY`, `PASS`, or `FAIL`. Validation errors may be
reported, but they are not candidate assessments.

## Synthetic/public-safe boundary

Future demo inputs must be synthetic, generic, company-neutral, and
public-safe. They must not reproduce or encode a real candidate profile,
application history, salary expectations, company preferences, mobility rules,
recruiter communications, client information, private job datasets, private
evidence records, proprietary scoring logic or prompts, local paths, or
credentials. If URLs are ever introduced, they must use reserved example
domains.

## Implemented local command

`PYTHONPATH=src python3 -m ai_job_radar.demo --assessment data/demo_assessment.json`

This command executes the public-safe local synthetic flow deterministically.
It is not production-ready and does not establish an operational AI Job Radar.
