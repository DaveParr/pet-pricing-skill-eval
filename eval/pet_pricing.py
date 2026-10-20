"""Pet insurance price eval: the same holdout run with and without the skill."""

from inspect_ai import Task, task
from inspect_ai.solver import generate, system_message

from eval.data import HOLDOUT_PATH, holdout_dataset
from eval.prompts import system_prompt
from eval.scorer import within_tolerance


def _pet_pricing(use_skill: bool, tolerance: float, holdout: str, level: str | None = None) -> Task:
    return Task(
        dataset=holdout_dataset(holdout, level),
        solver=[system_message(system_prompt(use_skill)), generate()],
        scorer=within_tolerance(tolerance),
    )


@task
def control(tolerance: float = 0.10, holdout: str = str(HOLDOUT_PATH)) -> Task:
    return _pet_pricing(False, tolerance, holdout)


@task
def with_skill(tolerance: float = 0.10, holdout: str = str(HOLDOUT_PATH)) -> Task:
    return _pet_pricing(True, tolerance, holdout)


# Prompt-detail ladder: same question, increasing pet details. Pass -T use_skill=true to add the skill.
@task
def simple(
    use_skill: bool = False, tolerance: float = 0.10, holdout: str = str(HOLDOUT_PATH)
) -> Task:
    return _pet_pricing(use_skill, tolerance, holdout, "simple")


@task
def moderate(
    use_skill: bool = False, tolerance: float = 0.10, holdout: str = str(HOLDOUT_PATH)
) -> Task:
    return _pet_pricing(use_skill, tolerance, holdout, "moderate")


@task
def detailed(
    use_skill: bool = False, tolerance: float = 0.10, holdout: str = str(HOLDOUT_PATH)
) -> Task:
    return _pet_pricing(use_skill, tolerance, holdout, "detailed")
