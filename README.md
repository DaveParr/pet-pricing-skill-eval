# pet-pricing-skill-eval

A small slice of the Future Finance Hackathon, **"Can AI Give Better Insurance Answers?"**
(Cardiff, 20 Oct 2026).

This project tests whether a skill designed from feature importance improves an LLM's
ability to produce an "accurate enough" pet insurance price estimate.

## Inputs

Neither dataset exists yet, and the exact features are not decided.

### Training data (`data/train/`)

A set of pets, each described by features. Example features:

| feature          | type     |
|------------------|----------|
| species          | category |
| age              | integer  |
| prior conditions | boolean  |

### Feature importance (`data/feature_importance/`)

A dataset describing the importance of each feature, for example
`species > age > prior conditions`.

### Holdout (`data/holdout/`)

For each pet, the cost of insuring it for a specific level of cover. These are the test cases.

## The skill (`skills/pet-pricing-estimate/`)

A skill designed from the feature importance in the input data. Not written yet.

## The eval (`eval/`)

- Each pet test case runs in an isolated subagent with the skill.
- A control set runs the same cases without the skill.
- An LLM-as-judge orchestrator runs the eval and assesses the results.

The goal is for the skill to improve the LLM's ability to produce an "accurate enough" price
estimate compared with the control.

## Setup

```bash
uv sync
```
