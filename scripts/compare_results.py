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


def main(paths: list[Path]) -> None:
    rows = [r for p in paths for r in rows_from(p)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    def fmt(v, spec):
        return "-" if v is None else format(v, spec)

    print(f"{'task':<11}{'pet':<8}{'true':>8}{'estimate':>10}{'error':>8}  ok")
    for r in rows:
        print(
            f"{r['task']:<11}{r['pet_id']:<8}{fmt(r['true_gbp'], '.2f'):>8}"
            f"{fmt(r['estimate_gbp'], '.2f'):>10}{fmt(r['pct_error'], '.0%'):>8}  {r['within_tolerance']}"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    args = [Path(a) for a in sys.argv[1:]]
    main(args or latest_per_task(LOG_DIR))
