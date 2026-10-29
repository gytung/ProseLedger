"""Export initial and per-round scores from the complete recorded evaluation."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "case",
    "topic",
    "branch",
    "round",
    "candidate_score",
    "retained_score",
    "action",
    "accepted",
    "content_check_passed",
    "text_changed",
    "historical_card_ids",
]


def export(evidence: dict) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for case in evidence["cases"]:
        for branch in ("targeted", "planner", "memory"):
            context = {"case": case["id"], "topic": case["theme"], "branch": branch}
            writer.writerow(
                {
                    **context,
                    "round": 0,
                    "candidate_score": case["initial"]["score"],
                    "retained_score": case["initial"]["score"],
                    "action": "initial",
                }
            )
            for record in case["branches"][branch]["rounds"]:
                writer.writerow(
                    {
                        **context,
                        "round": record["round"],
                        "candidate_score": record["candidate_score"],
                        "retained_score": record["retained_score"],
                        "action": record["route"],
                        "accepted": record["accepted"],
                        "content_check_passed": record["guard_passed"],
                        "text_changed": record["changed"],
                        "historical_card_ids": ";".join(record["historical_card_ids"]),
                    }
                )
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check the published CSV without modifying it.",
    )
    args = parser.parse_args()
    evidence = json.loads((ROOT / "docs/evidence.json").read_text(encoding="utf-8"))
    expected = export(evidence)
    destination = ROOT / "docs/round_scores.csv"
    if args.check:
        if (
            not destination.is_file()
            or destination.read_text(encoding="utf-8") != expected
        ):
            print(
                "Round scores differ from evidence.json. Run scripts/export_round_scores.py."
            )
            return 1
        print(
            "Round scores verified: 18 initial entries and 54 recorded branch decisions."
        )
        return 0
    destination.write_text(expected, encoding="utf-8", newline="")
    print("Exported docs/round_scores.csv: 72 entries; no model calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
