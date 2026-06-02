#!/usr/bin/env python3
"""Score manuscript potential for wildlife conservation datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DIMENSIONS = [
    ("sampling_design", "Sampling design"),
    ("sample_size_effort", "Sample size / effort"),
    ("data_completeness", "Data completeness"),
    ("observation_process", "Observation process"),
    ("method_question_fit", "Method-question fit"),
    ("novelty_gap", "Novelty / literature gap"),
    ("conservation_relevance", "Conservation relevance"),
    ("reproducibility", "Reproducibility"),
    ("ethics_permits_sensitivity", "Ethics / permits / sensitivity"),
]


def grade(score: int) -> str:
    if score <= 7:
        return "low"
    if score <= 13:
        return "medium"
    return "high"


def path_for(grade_name: str) -> str:
    if grade_name == "low":
        return "monitoring baseline, species inventory/update, data descriptor, methods note, local conservation report, or modest short communication"
    if grade_name == "medium":
        return "narrow empirical manuscript, short communication, habitat/occupancy association paper, activity/disturbance analysis, or management-priority article"
    return "full empirical article, integrated monitoring paper, management effectiveness paper with defensible design, or methodological paper"


def load_scores(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scores: dict[str, int] = {}
    for key, _label in DIMENSIONS:
        value = int(data.get(key, 0))
        if value < 0 or value > 2:
            raise SystemExit(f"Score for {key} must be 0, 1, or 2.")
        scores[key] = value
    return scores


def report(scores: dict[str, int]) -> str:
    total = sum(scores.values())
    grade_name = grade(total)
    lines = [
        "# Manuscript Potential Score",
        "",
        f"Total score: {total}/18",
        f"Potential grade: {grade_name}",
        f"Recommended deliverable path: {path_for(grade_name)}",
        "",
        "## Dimension Scores",
        "",
    ]
    for key, label in DIMENSIONS:
        lines.append(f"- {label}: {scores.get(key, 0)}/2")

    low_dims = [label for key, label in DIMENSIONS if scores.get(key, 0) == 0]
    lines.extend(["", "## Limiting Factors", ""])
    if low_dims:
        lines.extend(f"- {label}" for label in low_dims)
    else:
        lines.append("- No zero-score dimensions, but verify assumptions before drafting.")

    lines.extend(["", "## Guidance", ""])
    if grade_name == "low":
        lines.append("Do not frame this as a high-claim research article. Choose a modest deliverable and make limitations visible.")
    elif grade_name == "medium":
        lines.append("Proceed with a narrowed question, result cards, conservative claims, and explicit limitations.")
    else:
        lines.append("Proceed to deep research and robust analysis checks before using a stronger narrative.")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Score manuscript potential from a JSON rubric file.")
    parser.add_argument("scores_json", help="JSON file containing 0-2 scores for rubric dimensions.")
    parser.add_argument("-o", "--output", help="Optional markdown output path.")
    args = parser.parse_args()

    scores = load_scores(Path(args.scores_json))
    content = report(scores)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)


if __name__ == "__main__":
    main()
