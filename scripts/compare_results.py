"""Per-pet comparison of estimated vs true monthly price from Inspect eval logs.

Usage: uv run python scripts/compare_results.py [log.eval ...]
With no arguments, uses the newest log for each task in results/logs.
Writes results/comparison.csv (gitignored) and prints a table.
"""

import csv
import sys
from pathlib import Path

from inspect_ai.log import read_eval_log

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "results/logs"
OUT = ROOT / "results/comparison.csv"


def latest_per_task(log_dir: Path) -> list[Path]:
    newest: dict[str, tuple[float, Path]] = {}
    for path in log_dir.glob("*.eval"):
        task = read_eval_log(str(path), header_only=True).eval.task
        if task not in newest or path.stat().st_mtime > newest[task][0]:
            newest[task] = (path.stat().st_mtime, path)
    return [p for _, p in sorted(newest.values(), key=lambda t: t[1].name)]


def rows_from(path: Path) -> list[dict]:
    log = read_eval_log(str(path))
    out = []
    for sample in log.samples or []:
        score = next(iter(sample.scores.values()))
        meta = score.metadata or {}
        out.append(
            {
                "task": log.eval.task,
                "pet_id": sample.id,
                "true_gbp": meta.get("truth"),
                "estimate_gbp": meta.get("estimate"),
                "pct_error": meta.get("pct_error"),
                "within_tolerance": score.value,
            }
        )
    return out


TASK_ORDER = ["simple", "moderate", "detailed", "control", "with_skill"]


def summarise(rows: list[dict], tasks: list[str]) -> None:
    print(f"\n{'task':<11}{'n':>3}{'in tol':>8}{'MAPE':>7}{'bias':>8}{'unparsed':>10}")
    for task in tasks:
        mine = [r for r in rows if r["task"] == task]
        parsed = [r for r in mine if r["pct_error"] is not None]
        hits = sum(r["within_tolerance"] == "C" for r in mine)
        mape = sum(r["pct_error"] for r in parsed) / len(parsed) if parsed else float("nan")
        bias = (
            sum(r["estimate_gbp"] - r["true_gbp"] for r in parsed) / len(parsed)
            if parsed
            else float("nan")
        )
        print(
            f"{task:<11}{len(mine):>3}{hits:>5}/{len(mine):<2}{mape:>6.0%}{bias:>+8.2f}"
            f"{len(mine) - len(parsed):>10}"
        )
    print("MAPE = mean absolute % error; bias = mean (estimate - true) in GBP, over parsed answers")


def main(paths: list[Path]) -> None:
    rows = [r for p in paths for r in rows_from(p)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    tasks = sorted({r["task"] for r in rows}, key=lambda t: TASK_ORDER.index(t) if t in TASK_ORDER else 99)
    by_pet: dict[str, dict] = {}
    for r in rows:
        by_pet.setdefault(r["pet_id"], {"true": r["true_gbp"]})[r["task"]] = r["estimate_gbp"]

    print(f"{'pet':<8}{'true':>8}" + "".join(f"{t:>11}" for t in tasks))
    for pet, d in by_pet.items():
        cells = "".join(f"{('-' if d.get(t) is None else format(d[t], '.2f')):>11}" for t in tasks)
        print(f"{pet:<8}{d['true']:>8.2f}{cells}")
    summarise(rows, tasks)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    args = [Path(a) for a in sys.argv[1:]]
    main(args or latest_per_task(LOG_DIR))
