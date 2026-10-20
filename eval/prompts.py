"""System prompts. The skill arm is the base prompt plus the SKILL.md body."""

from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent / "skills/pet-pricing-estimate/SKILL.md"

BASE_PROMPT = """\
You are estimating the monthly price, in British pounds (GBP), of insuring a pet \
for one fixed level of cover. You will be given a question and whatever details of the pet \
are available. Always give your best single estimate, even if details are missing. \
Reason briefly, then finish with a single line in exactly this form:
ANSWER: £<monthly price as a number>"""


def load_skill_text(path: Path = SKILL_PATH) -> str:
    """SKILL.md body with any YAML frontmatter removed."""
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    return text.strip()


def system_prompt(use_skill: bool) -> str:
    if not use_skill:
        return BASE_PROMPT
    return f"{BASE_PROMPT}\n\n# Skill\n\n{load_skill_text()}"
