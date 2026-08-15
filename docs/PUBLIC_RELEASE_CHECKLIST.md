# Public Release Checklist

## Status

This repository is releasable only as a public scaffold and narrow
non-operational foundation. Public release must not imply that AI Job Radar,
AI Career Intelligence, Candidate Readiness, scoring, collection, evaluation,
reporting, agents, security enforcement, or a Decision Model runtime are
implemented.

## Required local checks

Run the following from the repository root for each publication candidate:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m ai_job_radar.public_sanitizer
```

Expected results:

- The test suite passes.
- The sanitizer prints `. | repository-sanitization | PASS`.
- No generated build output, logs, caches, private local rules, or opaque files
  are included in the publication candidate.

## Maintainer checklist

- Confirm that `README.md` and `docs/CASE05_PUBLIC_BLUEPRINT.md` still describe
  the repository as a scaffold, not an operational system.
- Confirm that `docs/SCORING_MODEL_V2.md` remains `DRAFT_NOT_ACTIVE` unless
  executable scoring code and proportionate tests are present.
- Confirm that `config/*.example.json` and `data/*.json` remain synthetic and
  satisfy the synthetic provenance contract.
- Confirm that `config/public-sanitizer.local.json`, if present locally, is not
  committed.
- Review Git history and repository hosting settings separately before public
  publication; the sanitizer checks the current candidate only.
- Confirm that the repository includes the MIT License and that its public reuse
  terms remain intentional.

## Release boundary

The public candidate may contain documentation, package metadata, synthetic
examples, an empty reference dataset, scaffold tests, the public sanitizer, and
the strict in-memory `PublicJobRecord` contract. Any future operational module
or dataset needs its own implementation evidence, tests, and public/private
boundary review before being described as active.
