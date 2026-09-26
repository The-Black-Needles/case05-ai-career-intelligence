# Case 05 — AI Career Intelligence

**Intelligent Job Opportunity Decision System**

AI Career Intelligence is the proposed broader system for supporting transparent,
evidence-aware career opportunity decisions. **AI Job Radar** is a prospective
module/concept within that system, intended to discover and organize job
opportunities if it is implemented in a later increment.

## Quickstart

This repository requires Python 3.11 or newer. It provides a small local,
synthetic requirement/evidence assessment demo and a separate synthetic
readiness/evidence-boundary demo; it is not a job-discovery product. From the
repository root, run the first demo:

```sh
PYTHONPATH=src python3 -m ai_job_radar.demo --assessment data/demo_assessment.json
```

Run each readiness example with the same local command, changing the file name:

```sh
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/ready_now.json
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/moderate_gaps.json
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/future_target.json
PYTHONPATH=src python3 -m ai_job_radar.synthetic_readiness --assessment data/demo_readiness_cases/insufficient_evidence.json
```

The first demo's deterministic JSON output preserves supplied requirement
statements and explicit evidence IDs, reports only factual linkage states and raw counts, and
always requires human review. It demonstrates strict data contracts,
traceability, reproducibility, and a public/private boundary without collecting
or processing real jobs. The second demo validates declared evidence scope and
characterizes only fictional readiness cases. Both require human review. See
[the readiness guide](docs/SYNTHETIC_READINESS_DEMO.md). Run the tests with:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Current public status

This public repository is a **narrow public foundation with two local synthetic
demos**. It contains documentation, package metadata, synthetic example
configuration, an empty reference dataset, scaffold-level tests, an in-memory
`PublicJobRecord` contract, and two deterministic demos. It does not contain an
operational AI Job Radar or decision system.

### IMPLEMENTED

- Case 05 public identity and truthful status documentation
- Python package metadata with no runtime dependencies
- Synthetic example configuration files
- An empty reference-job dataset
- Standard-library scaffold tests
- A standard-library public-release sanitization check for the publication candidate
- A strict standard-library in-memory `PublicJobRecord` value contract; it does
  not load, transform, normalize, enrich, or process records
- A local, deterministic synthetic requirement/evidence assessment demo with
  strict validation, explicit ID linkage, factual raw counts, and mandatory
  human review
- A separate deterministic synthetic readiness and evidence-boundary demo with
  explicit input characterization, conservative coverage, and mandatory human
  review; its four fictional cases are not candidate assessments
- A reserved `src/ai_job_radar` package namespace; its presence does not mean an
  AI Job Radar module is operational

### PLANNED / NOT ACTIVE

All broader operational stages and capabilities are target-state concepts only:

- authorized-source collection
- loading, transformation, normalization, enrichment, and identity resolution
- cross-run deduplication
- semantic classification and requirement/evidence matching
- deterministic gates, scoring, ranking, and recommendation
- real-job Candidate Readiness assessment
- LLM evaluation
- reporting and change detection
- security enforcement and audit controls
- agents or automated actions
- Decision Model runtime

The local demos perform no real-job collection, semantic matching, weighted
scoring, real-job readiness, ranking, recommendation, LLM/agent runtime, or
production activity. They do not process real candidate data, track real
applications, run the private operational Radar, use live LLMs, or
automatically recommend applications.

## Target architecture — PLANNED / NOT ACTIVE

The following diagram is architectural intent, not a description of running
software.

```mermaid
flowchart LR
    A["Collection<br/>PLANNED / NOT ACTIVE"] --> B["Normalization & deduplication<br/>PLANNED / NOT ACTIVE"]
    B --> C["Classification & evidence matching<br/>PLANNED / NOT ACTIVE"]
    C --> D["Decision Model & scoring<br/>PLANNED / NOT ACTIVE"]
    D --> E["Reporting & human review<br/>PLANNED / NOT ACTIVE"]
```

## Public artifacts

- `docs/CASE05_PUBLIC_BLUEPRINT.md` — truthful architectural and publication blueprint
- `docs/SCORING_MODEL_V2.md` — `DRAFT_NOT_ACTIVE` target-state scoring notes
- `docs/PUBLIC_RELEASE_CHECKLIST.md` — public-release scope, gates, and maintainer checklist
- `config/*.example.json` — synthetic examples, not active configuration
- `data/reference_jobs.json` — empty placeholder dataset
- `src/ai_job_radar/job_record.py` — immutable in-memory public record contract
- `src/ai_job_radar/requirement_evidence.py` — deterministic synthetic
  requirement/evidence validation and factual assessment
- `data/demo_assessment.json` — public-safe synthetic demo fixture
- `src/ai_job_radar/synthetic_readiness.py` — separate synthetic readiness
  characterization and evidence-boundary validation
- `data/demo_readiness_cases/*.json` — four fictional readiness examples
- `docs/SYNTHETIC_READINESS_DEMO.md` — scope, contract, and run commands

This repository is available under the [MIT License](LICENSE).

The demo and record contract do not establish an operational AI Job Radar. The
repository makes no claim that collection, loading, transformation,
normalization, enrichment, deduplication, classification,
semantic requirement/evidence matching, real-job Candidate Readiness, scoring,
ranking,
recommendation, LLM evaluation, reporting, security controls, agents, or a
Decision Model runtime exist.

## Release verification

Run these checks from the repository root before publishing a candidate:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m ai_job_radar.public_sanitizer
```

Both commands must pass. The sanitizer inspects tracked files and untracked,
non-ignored files in the current publication candidate; it does not inspect Git
history or replace human review.
