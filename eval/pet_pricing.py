"""Pet insurance price eval: the same holdout run with and without the skill."""

from inspect_ai import Task, task
from inspect_ai.solver import generate, system_message

from eval.data import HOLDOUT_PATH, holdout_dataset
from eval.prompts import system_prompt
from eval.scorer import within_tolerance


def _pet_pricing(use_skill: bool, tolerance: float, holdout: str) -> Task:
    return Task(
        dataset=holdout_dataset(holdout),
        solver=[system_message(system_prompt(use_skill)), generate()],
        scorer=within_tolerance(tolerance),
    )


@task
def control(tolerance: float = 0.10, holdout: str = str(HOLDOUT_PATH)) -> Task:
    return _pet_pricing(False, tolerance, holdout)


@task
def with_skill(tolerance: float = 0.10, holdout: str = str(HOLDOUT_PATH)) -> Task:
    return _pet_pricing(True, tolerance, holdout)
