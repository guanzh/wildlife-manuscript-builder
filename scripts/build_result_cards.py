#!/usr/bin/env python3
"""Create result-card markdown from a CSV file or blank templates."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


FIELDS = [
    "label",
    "result_sentence",
    "figure_table",
    "data_source",
    "survey_effort_or_sample_size",
    "model_or_statistic",
    "estimate_or_effect_size",
    "uncertainty",
    "supported_claim",
    "unsupported_claim",
    "needed_caveat",
    "discussion_entry_point",
    "nearest_comparison_papers",
]


def card(row: dict[str, str], index: int) -> str:
    label = row.get("label") or f"Result {index}"
    lines = [
        f"## Result Card: {label}",
        "",
        f"- Result sentence: {row.get('result_sentence', '')}",
        f"- Figure/table: {row.get('figure_table', '')}",
        f"- Data source: {row.get('data_source', '')}",
        f"- Survey effort / sample size: {row.get('survey_effort_or_sample_size', '')}",
        f"- Model or statistic: {row.get('model_or_statistic', '')}",
        f"- Estimate / effect size: {row.get('estimate_or_effect_size', '')}",
        f"- Uncertainty: {row.get('uncertainty', '')}",
        f"- Supported claim: {row.get('supported_claim', '')}",
        f"- Unsupported claim: {row.get('unsupported_claim', '')}",
        f"- Needed caveat: {row.get('needed_caveat', '')}",
        f"- Discussion entry point: {row.get('discussion_entry_point', '')}",
        f"- Nearest comparison papers: {row.get('nearest_comparison_papers', '')}",
        "",
    ]
    return "\n".join(lines)


def blank_cards(count: int) -> str:
    return "\n".join(card({}, i) for i in range(1, count + 1))


def cards_from_csv(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for i, row in enumerate(reader, start=1):
            normalized = {key.strip(): (value or "").strip() for key, value in row.items() if key}
            rows.append(card(normalized, i))
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build wildlife manuscript result cards.")
    parser.add_argument("--csv", help="Optional CSV with result-card fields.")
    parser.add_argument("--blank", type=int, default=3, help="Number of blank cards when no CSV is supplied.")
    parser.add_argument("-o", "--output", help="Optional markdown output path.")
    args = parser.parse_args()

    content = cards_from_csv(Path(args.csv)) if args.csv else blank_cards(args.blank)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)


if __name__ == "__main__":
    main()
