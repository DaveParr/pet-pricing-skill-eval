from pathlib import Path

import pytest

from eval.data import holdout_dataset, record_to_sample

FIXTURE = Path(__file__).parent / "fixtures" / "holdout_synthetic.csv"


def test_loads_one_sample_per_row():
    ds = holdout_dataset(FIXTURE)
    assert len(ds) == 5
    first = ds[0]
    assert first.id == "fake-1"
    assert first.target == "28.50"
    assert first.metadata == {"species": "dog", "age": "3", "prior_conditions": "false"}


def test_features_rendered_and_price_not_leaked():
    for sample in holdout_dataset(FIXTURE):
        assert "- species:" in sample.input
        assert "- age:" in sample.input
        assert sample.target not in sample.input
        assert "monthly_price_gbp" not in sample.input


def test_missing_column():
    with pytest.raises(ValueError, match="missing column"):
        record_to_sample({"pet_id": "x", "species": "dog"})


@pytest.mark.parametrize("price", ["abc", "", "0", "-5"])
def test_bad_price(price):
    with pytest.raises(ValueError):
        record_to_sample({"pet_id": "x", "monthly_price_gbp": price})


def test_duplicate_ids(tmp_path):
    csv = tmp_path / "dup.csv"
    csv.write_text("pet_id,species,monthly_price_gbp\na,dog,10\na,cat,12\n")
    with pytest.raises(ValueError, match="duplicate"):
        holdout_dataset(csv)
