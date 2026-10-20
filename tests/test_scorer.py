import asyncio
from types import SimpleNamespace

import pytest
from inspect_ai.scorer import CORRECT, INCORRECT, Target

from eval.scorer import parse_estimate, within_tolerance


@pytest.mark.parametrize(
    "text,expected",
    [
        ("ANSWER: £28.50", 28.5),
        ("answer: 28", 28.0),
        ("ANSWER: £1,234.50 per month", 1234.5),
        ("ANSWER: £10\nactually\nANSWER: £12", 12.0),
        ("no answer here", None),
    ],
)
def test_parse_estimate(text, expected):
    assert parse_estimate(text) == expected


def run(completion, truth="100.00", tolerance=0.10):
    state = SimpleNamespace(output=SimpleNamespace(completion=completion))
    return asyncio.run(within_tolerance(tolerance)(state, Target(truth)))


def test_within_tolerance():
    assert run("ANSWER: £110").value == CORRECT  # exactly at the edge
    assert run("ANSWER: £90").value == CORRECT
    assert run("ANSWER: £111").value == INCORRECT


def test_unparseable_is_incorrect():
    score = run("I think about a hundred")
    assert score.value == INCORRECT
    assert score.metadata["pct_error"] is None
