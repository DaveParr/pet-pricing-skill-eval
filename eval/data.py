"""Holdout ingestion: one CSV row per pet, one Inspect Sample per row."""

from pathlib import Path

from inspect_ai.dataset import MemoryDataset, Sample, csv_dataset

ROOT = Path(__file__).resolve().parent.parent  # inspect chdirs into eval/, so anchor paths here
HOLDOUT_PATH = ROOT / "data/holdout/holdout.csv"
ID_COLUMN = "pet_id"
PRICE_COLUMN = "monthly_price_gbp"
RESERVED = {ID_COLUMN, PRICE_COLUMN}


def record_to_sample(record: dict) -> Sample:
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
    return Sample(
        id=pet_id,
        input=f"Estimate the monthly insurance price for this pet:\n{lines}",
        target=f"{price:.2f}",
        metadata=features,
    )


def holdout_dataset(path: str | Path = HOLDOUT_PATH) -> MemoryDataset:
    samples = list(csv_dataset(str(ROOT / path), sample_fields=record_to_sample))
    ids = [s.id for s in samples]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate {ID_COLUMN} values: {duplicates}")
    return MemoryDataset(samples, name="holdout")
