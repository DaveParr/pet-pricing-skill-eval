"""Build the holdout CSV from the first tab of Pet_Insurance_Quotes.xlsx.

Usage: uv run python scripts/xlsx_to_csv.py [xlsx] [out_csv]
"""

import csv
import datetime as dt
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = ROOT / "Pet_Insurance_Quotes.xlsx"
DEFAULT_OUT = ROOT / "data/holdout/holdout.csv"
HEADER_ROW = 4  # rows 1-3 are a title, a description and group banners

ID_HEADER = "Quote ID"
TARGET_HEADER = "Monthly (£)"

# spreadsheet header -> csv column; the pet and owner inputs (sheet columns E-AC)
FEATURES = {
    "Species": "species",
    "Pet Type": "pet_type",
    "Breed / Size": "breed_size",
    "Pet Sex": "pet_sex",
    "Pet Age (yrs)": "pet_age_yrs",
    "Purchase Price (£)": "purchase_price_gbp",
    "Neutered?": "neutered",
    "Microchipped?": "microchipped",
    "Vaccines Up To Date?": "vaccines_up_to_date",
    "Pre-existing / Illness Signs?": "preexisting_illness_signs",
    "Cover for Pre-existing Requested?": "preexisting_cover_requested",
    "Pre-existing Cover Route": "preexisting_cover_route",
    "Aggressive Tendencies?": "aggressive_tendencies",
    "Complaint / Legal Action (5 yrs)?": "complaint_legal_action_5yrs",
    "Breeding / Racing / Business Use?": "breeding_racing_business_use",
    "Premises Where Alcohol Sold?": "premises_alcohol_sold",
    "Multi-pet?": "multi_pet",
    "Cover Scope": "cover_scope",
    "Treatment Type Sought": "treatment_type_sought",
    "Owner Age (yrs)": "owner_age_yrs",
    "Postcode District": "postcode_district",
    "Pet Kept At Address?": "pet_kept_at_address",
    "Owner Full-time UK Resident?": "owner_full_time_uk_resident",
    "Standard Assumptions Agreed?": "standard_assumptions_agreed",
}
OUT_ID = "pet_id"
OUT_TARGET = "monthly_price_gbp"


def _cell(value):
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return "" if value is None else value


def convert(xlsx: Path, out: Path) -> int:
    wb = load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(min_row=HEADER_ROW, values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(rows)]

    wanted = [ID_HEADER, *FEATURES, TARGET_HEADER]
    missing = [h for h in wanted if h not in header]
    if missing:
        raise SystemExit(f"{ws.title!r}: header row {HEADER_ROW} is missing {missing}")
    index = {h: header.index(h) for h in wanted}

    kept, no_id, no_price = [], 0, 0
    for row in rows:
        pet_id = row[index[ID_HEADER]]
        if pet_id in (None, ""):
            no_id += 1
            continue
        price = row[index[TARGET_HEADER]]
        if price in (None, ""):
            no_price += 1
            continue
        kept.append(
            [str(pet_id).strip()]
            + [_cell(row[index[h]]) for h in FEATURES]
            + [_cell(price)]
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([OUT_ID, *FEATURES.values(), OUT_TARGET])
        writer.writerows(kept)

    print(f"{ws.title!r}: wrote {len(kept)} rows to {out}")
    print(f"dropped: {no_id} with no {ID_HEADER}, {no_price} with no {TARGET_HEADER}")
    return len(kept)


if __name__ == "__main__":
    args = sys.argv[1:]
    convert(Path(args[0]) if args else DEFAULT_XLSX, Path(args[1]) if len(args) > 1 else DEFAULT_OUT)
