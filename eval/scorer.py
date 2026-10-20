"""Deterministic scoring: is the estimate within a tolerance of the true monthly price?"""

import re

from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Target,
    accuracy,
    metric,
    scorer,
)
from inspect_ai.solver import TaskState

_ANSWER = re.compile(r"ANSWER:\s*£?\s*([0-9][0-9,]*(?:\.[0-9]+)?)", re.IGNORECASE)


def parse_estimate(completion: str) -> float | None:
    """Return the last `ANSWER: £<number>` in the completion, or None."""
    matches = _ANSWER.findall(completion)
    if not matches:
        return None
    return float(matches[-1].replace(",", ""))


@metric
def mean_abs_pct_error():
    def compute(scores: list) -> float:
        errors = [
            s.score.metadata["pct_error"]
            for s in scores
            if s.score.metadata and s.score.metadata.get("pct_error") is not None
        ]
        return sum(errors) / len(errors) if errors else float("nan")

    return compute


@scorer(metrics=[accuracy(), mean_abs_pct_error()])
def within_tolerance(tolerance: float = 0.10):
    async def score(state: TaskState, target: Target) -> Score:
        truth = float(target.text)
        estimate = parse_estimate(state.output.completion)
        if estimate is None:
            return Score(
                value=INCORRECT,
                answer=None,
                explanation="no `ANSWER: £<number>` line found",
                metadata={"estimate": None, "truth": truth, "pct_error": None},
            )
        pct_error = abs(estimate - truth) / truth
        return Score(
            value=CORRECT if pct_error <= tolerance else INCORRECT,
            answer=f"{estimate:.2f}",
            explanation=f"estimate £{estimate:.2f} vs true £{truth:.2f} ({pct_error:.1%} error)",
            metadata={"estimate": estimate, "truth": truth, "pct_error": pct_error},
        )

    return score
