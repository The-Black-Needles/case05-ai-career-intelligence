# Scoring Model V2

## Status

**DRAFT_NOT_ACTIVE**

This document is conceptual target-state material only. A narrow deterministic
synthetic readiness demonstration exists for fictional inputs. The public
repository has no real-job Candidate Readiness assessment and no executable weighted scoring.
It also has no Company Quality, Life Compatibility, application recommendation,
eligibility gate, classification pipeline, report policy, or Decision Model
runtime. The synthetic policy is documented separately and is not this model.

## Conceptual design principle

A future model could separate opportunity relevance from current candidate
readiness so that a strategically relevant role is not confused with evidence
of present readiness. This is a proposal, not an implemented evaluation.

## Conceptual weights

The synthetic example configuration records these draft values:

| Proposed dimension | Draft value |
|---|---:|
| Strategic relevance | 25% |
| Candidate Readiness | 25% |
| Company quality | 35% |
| Life fit | 15% |

They are configuration examples only. No code applies them, and they do not
constitute an active weighted score.

## Conceptual gates and classifications

Possible target-state gates include source authorization, company activation,
job status, contract and geographic eligibility, affirmative-action eligibility,
work authorization, domain policy, and authentication or CAPTCHA constraints.

Possible target-state classifications include AI role archetype, AI centrality,
requirement importance, evidence level, gap severity, and confidence. None is
computed, enforced, or validated by this scaffold.

## Evidence interpretation invariants

Any future design and implementation must preserve all of the following:

- declared evidence is not proven capability
- demonstrable project is not production experience
- course is not professional experience
- knowledge is not productive execution
- absence of evidence is not inability
- `NO_EVIDENCE` does not automatically imply structural gap
- empty limitations do not imply unrestricted evidence
- evidence levels do not silently become numeric weights
- requirement types do not silently become scoring weights

These rules constrain interpretation. The separate synthetic readiness demo
enforces its declared evidence-scope boundaries for fictional inputs only; it
does not implement a real-job evidence model or this weighted decision model.

## Conceptual report policy

A future pilot might cap a weekly report at 15 new or materially changed jobs
and 3 detailed jobs per company, without requiring the limit to be filled. It
might omit previously analyzed jobs unless materially changed and exclude
previously applied jobs from recommendations.

That policy is **PLANNED / NOT ACTIVE**. This repository does not generate
reports, track prior analysis or applications, or enforce these limits.
