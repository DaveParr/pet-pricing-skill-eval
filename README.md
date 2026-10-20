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

`data/holdout/holdout.csv`: one row per pet. These are the test cases. There is a single cover level,
so it is not a column. Required columns:

| column              | meaning                                          |
|---------------------|--------------------------------------------------|
| `pet_id`            | unique id                                        |
| `monthly_price_gbp` | true monthly price in GBP (the target)           |
| anything else       | a feature, shown to the model as `- name: value` |

Features can be added or dropped without code changes.

#### Building the holdout CSV

`Pet_Insurance_Quotes.xlsx` is the source. `scripts/xlsx_to_csv.py` reads its first tab
(`Real_Quotes`, header on row 4) and writes `data/holdout/holdout.csv` with the pet and owner input
columns as features and `Monthly (£)` as `monthly_price_gbp`. Rows without a Quote ID or a monthly
price are dropped. The feature list is the `FEATURES` constant at the top of the script.

```bash
uv run python scripts/xlsx_to_csv.py [xlsx] [out_csv]
```

## The skill (`skills/pet-pricing-estimate/`)

A skill designed from the feature importance in the input data. Not written yet.

## The eval (`eval/`)

Built on [Inspect AI](https://inspect.aisi.org.uk/). Two tasks in `eval/pet_pricing.py` share the
same holdout dataset, base prompt and scorer:

- `with_skill`: the `SKILL.md` body is injected into the system prompt.
- `control`: the same prompt without the skill, with every holdout feature shown.

Three further tasks vary how much the user prompt says, all asking "How much will it cost to insure
my dog?": `simple` (the question alone), `moderate` (plus pet age and sex) and `detailed` (plus breed).
They run without the skill by default; add `-T use_skill=true` to inject it.

Each sample runs independently. The scorer parses `ANSWER: £<number>` and counts it correct when
within a relative tolerance of the true price (default 10%), also reporting mean absolute % error.

The goal is for the skill to improve the LLM's ability to produce an "accurate enough" price
estimate compared with the control.

## Setup

```bash
uv sync
uv run pytest
```

## Run

Paths are relative to the project root. `PYTHONPATH=.` lets Inspect import the `eval` package.

```bash
PYTHONPATH=. uv run inspect eval eval/pet_pricing.py@control eval/pet_pricing.py@with_skill \
  --model <provider/model>
# smoke test with no API key, on the synthetic fixture:
PYTHONPATH=. uv run inspect eval eval/pet_pricing.py@with_skill \
  -T holdout=tests/fixtures/holdout_synthetic.csv --model mockllm/model
# prompt-detail ladder, then a side-by-side table of estimates vs true prices
PYTHONPATH=. uv run inspect eval eval/pet_pricing.py@simple eval/pet_pricing.py@moderate \
  eval/pet_pricing.py@detailed --model <provider/model> --log-dir results/logs
uv run python scripts/compare_results.py
# change the tolerance: -T tolerance=0.05
```
