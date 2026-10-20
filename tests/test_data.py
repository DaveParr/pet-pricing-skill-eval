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


def _levels_csv(tmp_path):
    csv = tmp_path / "levels.csv"
    csv.write_text(
        "pet_id,species,pet_sex,pet_age_yrs,pet_type,breed_size,"
        "preexisting_illness_signs,preexisting_cover_requested,preexisting_cover_route,"
        "owner_age_yrs,monthly_price_gbp\n"
        "a,Dog,Female,6,Cockapoo,Cockapoo (medium),No,n/a,n/a,36,21.99\n"
    )
    return csv


def test_simple_level_is_only_the_question(tmp_path):
    sample = holdout_dataset(_levels_csv(tmp_path), "simple")[0]
    assert sample.input == "How much will it cost to insure my dog?"


def test_moderate_adds_age_and_sex_only(tmp_path):
    text = holdout_dataset(_levels_csv(tmp_path), "moderate")[0].input
    assert text.startswith("How much will it cost to insure my dog?")
    assert "Age (years): 6" in text and "Sex: Female" in text
    assert "Breed" not in text and "Cockapoo" not in text and "Pre-existing" not in text


def test_detailed_adds_breed_and_never_the_price(tmp_path):
    sample = holdout_dataset(_levels_csv(tmp_path), "detailed")[0]
    assert "Breed / size: Cockapoo (medium)" in sample.input
    assert "Pet type: Cockapoo" in sample.input
    assert "Pre-existing conditions or illness signs?: No" in sample.input
    assert "Pre-existing cover route: n/a" in sample.input
    assert "Owner" not in sample.input and "36" not in sample.input  # other features stay out
    assert "21.99" not in sample.input and sample.target == "21.99"
    assert sample.metadata["species"] == "Dog"  # full row still kept for analysis


def test_level_needs_its_columns(tmp_path):
    with pytest.raises(ValueError, match="lacks column"):
        holdout_dataset(FIXTURE, "moderate")


def test_unknown_level():
    with pytest.raises(ValueError, match="unknown prompt level"):
        holdout_dataset(FIXTURE, "extreme")
