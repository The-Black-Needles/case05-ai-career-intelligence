# Scoring Model V2

## Design principle

The model separates opportunity relevance from current candidate readiness.

A role can be strategically excellent while still requiring meaningful professional growth.

## Overall weights

| Dimension | Weight |
|---|---:|
| Strategic relevance | 25% |
| Candidate readiness | 25% |
| Company quality | 35% |
| Life fit | 15% |

Objective eligibility gates are evaluated before the weighted score.

## Eligibility gates

- Authorized source
- Active configured company
- Open job
- Accepted employment contract
- Geographic eligibility
- Compatible affirmative-action eligibility
- Work authorization
- Domain allowlist
- No authentication or CAPTCHA requirement

## AI role archetypes

- `AI_AGENT_ENGINEERING`
- `AI_BUSINESS_AUTOMATION`
- `AI_PROCESS_TRANSFORMATION`
- `AI_DATA_SCIENCE`
- `AI_PRODUCT_STRATEGY`
- `AI_PLATFORM_LLMOPS`
- `AI_SECURITY_GOVERNANCE`
- `AI_DOMAIN_ANALYTICS`

## AI centrality

- `AI_CORE`
- `AI_ADJACENT`
- `AI_CONTEXTUAL`
- `NONE`

## Requirement importance

- `MANDATORY`
- `PREFERRED`
- `DIFFERENTIAL`
- `CONTEXTUAL`

## Evidence levels

- Professional production experience
- Demonstrable private or public project
- Course or certification
- Development-stage knowledge
- Conceptual knowledge
- No evidence

## Gap severity

- `LIGHT`
- `MODERATE`
- `STRUCTURAL`

## Confidence

- `HIGH`
- `MEDIUM`
- `LOW`

## Weekly-report policy

Initial pilot:

- Maximum of 15 new or materially changed jobs
- Maximum of 3 detailed jobs from the same company
- No obligation to fill the limit
- Previously analyzed jobs are omitted unless materially changed
- Previously applied jobs cannot return as recommendations
