import csv
import datetime as dt
import importlib.util
from pathlib import Path

import pytest
from openpyxl import Workbook

spec = importlib.util.spec_from_file_location(
    "xlsx_to_csv", Path(__file__).parent.parent / "scripts" / "xlsx_to_csv.py"
)
xlsx_to_csv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xlsx_to_csv)


def make_workbook(path, drop_header=None):
    wb = Workbook()
    ws = wb.active
    ws.append(["Title banner"])
    ws.append(["Description"])
    ws.append(["Group banner"])
    headers = [xlsx_to_csv.ID_HEADER, *xlsx_to_csv.FEATURES, "Provider", xlsx_to_csv.TARGET_HEADER]
    if drop_header:
        headers.remove(drop_header)
    ws.append(headers)

    def row(pet_id, price, species="Dog"):
        values = {h: "x" for h in headers}
        values.update(
            {
                xlsx_to_csv.ID_HEADER: pet_id,
                "Species": species,
                "Pet Age (yrs)": 6.0,
                "Date of Birth": dt.datetime(2020, 3, 1),
                "Provider": "SECRET PROVIDER",
                xlsx_to_csv.TARGET_HEADER: price,
            }
        )
        return [values[h] for h in headers]

    ws.append(row("RQ-001", 21.99))
    ws.append(row("RQ-002", None))  # unpriced
    ws.append([None] * len(headers))  # blank template row
    ws.append(row("RQ-003", 30))
    wb.create_sheet("Second tab").append(["ignored"])
    wb.save(path)


def test_convert(tmp_path):
    src, out = tmp_path / "q.xlsx", tmp_path / "out" / "holdout.csv"
    make_workbook(src)
    assert xlsx_to_csv.convert(src, out) == 2

    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert [r["pet_id"] for r in rows] == ["RQ-001", "RQ-003"]
    assert rows[0]["monthly_price_gbp"] == "21.99"
    assert rows[0]["pet_age_yrs"] == "6"  # 6.0 written without trailing .0
    assert rows[0]["date_of_birth"] == "2020-03-01"
    header = list(rows[0])
    assert header[0] == "pet_id" and header[-1] == "monthly_price_gbp"
    assert "provider" not in header and "SECRET PROVIDER" not in out.read_text()


def test_missing_header(tmp_path):
    src = tmp_path / "q.xlsx"
    make_workbook(src, drop_header="Species")
    with pytest.raises(SystemExit, match="Species"):
        xlsx_to_csv.convert(src, tmp_path / "out.csv")


def test_output_loads_in_eval(tmp_path):
    from eval.data import holdout_dataset

    src, out = tmp_path / "q.xlsx", tmp_path / "holdout.csv"
    make_workbook(src)
    xlsx_to_csv.convert(src, out)
    assert len(holdout_dataset(out)) == 2
