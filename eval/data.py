"""Holdout ingestion: one CSV row per pet, one Inspect Sample per row."""

from pathlib import Path

from inspect_ai.dataset import MemoryDataset, Sample, csv_dataset

ROOT = Path(__file__).resolve().parent.parent  # inspect chdirs into eval/, so anchor paths here
HOLDOUT_PATH = ROOT / "data/holdout/holdout.csv"
ID_COLUMN = "pet_id"
PRICE_COLUMN = "monthly_price_gbp"
RESERVED = {ID_COLUMN, PRICE_COLUMN}

QUESTION = "How much will it cost to insure my dog?"
# prompt level -> holdout feature columns injected after the question
LEVELS: dict[str, list[str]] = {
    "simple": [],
    "moderate": ["pet_age_yrs", "pet_sex"],
    "detailed": [
        "pet_age_yrs",
        "pet_sex",
        "pet_type",
        "breed_size",
        "preexisting_illness_signs",
        "preexisting_cover_requested",
        "preexisting_cover_route",
    ],
}
LABELS = {
    "pet_age_yrs": "Age (years)",
    "pet_sex": "Sex",
    "pet_type": "Pet type",
    "breed_size": "Breed / size",
    "preexisting_illness_signs": "Pre-existing conditions or illness signs?",
    "preexisting_cover_requested": "Cover for pre-existing conditions requested?",
    "preexisting_cover_route": "Pre-existing cover route",
}


def render_level(features: dict, level: str) -> str:
    """The question alone, plus only the features this level allows."""
    columns = LEVELS[level]
    absent = [c for c in columns if c not in features]
    if absent:
        raise ValueError(f"holdout CSV lacks column(s) needed for {level!r}: {absent}")
    lines = [f"{LABELS[c]}: {features[c]}" for c in columns]
    return "\n".join([QUESTION, *lines])


def record_to_sample(record: dict, level: str | None = None) -> Sample:
    """level=None shows every feature; otherwise one of LEVELS."""
    missing = RESERVED - record.keys()
    if missing:
        raise ValueError(f"holdout CSV is missing column(s): {sorted(missing)}")

    pet_id = str(record[ID_COLUMN]).strip()
    try:
        price = float(record[PRICE_COLUMN])
    except (TypeError, ValueError):
        raise ValueError(f"pet {pet_id}: non-numeric {PRICE_COLUMN}: {record[PRICE_COLUMN]!r}")
    if price <= 0:
        raise ValueError(f"pet {pet_id}: {PRICE_COLUMN} must be positive, got {price}")

    # every non-reserved column is a feature; the price must never reach the prompt
    features = {k: v for k, v in record.items() if k not in RESERVED}
    lines = "\n".join(f"- {name}: {value}" for name, value in features.items())
    if level is None:
        prompt = f"Estimate the monthly insurance price for this pet:\n{lines}"
    else:
        prompt = render_level(features, level)
    return Sample(
        id=pet_id,
        input=prompt,
        target=f"{price:.2f}",
        metadata=features,
    )


def holdout_dataset(path: str | Path = HOLDOUT_PATH, level: str | None = None) -> MemoryDataset:
    if level is not None and level not in LEVELS:
        raise ValueError(f"unknown prompt level {level!r}; choose from {list(LEVELS)}")
    samples = list(
        csv_dataset(str(ROOT / path), sample_fields=lambda r: record_to_sample(r, level))
    )
    ids = [s.id for s in samples]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate {ID_COLUMN} values: {duplicates}")
    return MemoryDataset(samples, name="holdout")
