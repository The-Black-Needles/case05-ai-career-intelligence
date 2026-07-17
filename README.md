# AI Job Radar

**Agentic Career Opportunity Intelligence**

AI Job Radar is an explainable, human-in-the-loop system for discovering, classifying, deduplicating and prioritizing career opportunities from authorized sources.

## Current status

This repository is an initial public-ready scaffold for Case 06.

The operational implementation is being validated separately before the first public release.

## Core capabilities

- Incremental collection from authorized career pages and ATS platforms
- Job normalization and cross-run deduplication
- Strategic relevance and candidate-readiness analysis
- AI role archetype classification
- Explainable multidimensional scoring
- Material-change detection
- Weekly opportunity intelligence reports
- Human approval before every external action
- Security guardrails and domain allowlists
- Evaluation with labeled reference jobs

## Decision model

The initial score separates:

- Strategic relevance
- Candidate readiness
- Company quality
- Life fit

Objective eligibility rules remain deterministic and are evaluated before semantic scoring.

## Safety principles

- No automatic applications
- No automatic recruiter messages
- No authenticated LinkedIn scraping
- No CAPTCHA bypass
- No access outside configured domains
- No secrets or personal application history in the public repository
- Human review is mandatory

## Repository status

The project is currently in the architecture and evaluation-design phase.

See:

- `docs/CASE06_PUBLIC_BLUEPRINT.md`
- `docs/SCORING_MODEL_V2.md`
- `data/reference_jobs.json`
