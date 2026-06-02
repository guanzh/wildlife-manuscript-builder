#!/usr/bin/env python3
"""First-pass completeness audit for a Markdown claim ledger.

This script checks whether the ledger uses the required columns and whether
major claims have evidence, strength, caveat, and status fields. It does not
replace expert review.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_COLUMNS = [
    "Claim ID",
    "Manuscript Location",
    "Claim",
    "Evidence Source",
    "Evidence ID",
    "Claim Strength",
    "Boundary / Caveat",
    "Status",
]

VALID_SOURCES = {
    "data-contract",
    "result-card",
    "literature",
    "method",
    "author-confirmed",
    "assumption",
}

VALID_STRENGTHS = {
    "observed fact",
    "derived metric",
    "model-supported association",
    "literature context",
    "interpretation",
    "management implication",
    "causal claim",
    "unsupported",
}

VALID_STATUS = {"keep", "narrow", "remove", "needs verification"}

RISKY_WORDS = [
    "cause",
    "caused",
    "driven by",
    "effectiveness",
    "density",
    "abundance",
    "avoidance",
    "sensitivity",
    "导致",
    "造成",
    "驱动",
    "保护成效",
    "密度",
    "种群数量",
    "回避",
    "敏感性",
]


def normalize_header(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.strip().lower())


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip().strip("`") for cell in line.split("|")]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def extract_tables(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        if "|" in line:
            current.append(split_row(line))
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def find_ledger_table(text: str) -> tuple[list[str], list[list[str]]] | None:
    required = {normalize_header(col) for col in REQUIRED_COLUMNS}
    for table in extract_tables(text):
        if len(table) < 2:
            continue
        header = table[0]
        if not required.issubset({normalize_header(col) for col in header}):
            continue
        rows = table[2:] if len(table) > 1 and is_separator("|".join(table[1])) else table[1:]
        return header, rows
    return None


def contains_any(text: str, choices: set[str]) -> bool:
    normalized = text.strip().lower()
    return any(choice in normalized for choice in choices)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Markdown claim ledger.")
    parser.add_argument("ledger", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    text = args.ledger.read_text(encoding="utf-8")
    table = find_ledger_table(text)
    issues: list[str] = []
    warnings: list[str] = []

    if table is None:
        issues.append("No ledger table found with all required columns.")
        rows: list[list[str]] = []
        header: list[str] = []
        index: dict[str, int] = {}
    else:
        header, rows = table
        index = {normalize_header(col): i for i, col in enumerate(header)}
        for required in REQUIRED_COLUMNS:
            if normalize_header(required) not in index:
                issues.append(f"Missing required column: {required}")

    def cell(row: list[str], column: str) -> str:
        i = index.get(normalize_header(column), -1)
        return row[i].strip() if 0 <= i < len(row) else ""

    audited_rows = 0
    for row_number, row in enumerate(rows, start=1):
        if not any(cell.strip() for cell in row):
            continue
        audited_rows += 1
        claim_id = cell(row, "Claim ID") or f"row {row_number}"
        claim = cell(row, "Claim")
        source = cell(row, "Evidence Source")
        evidence_id = cell(row, "Evidence ID")
        strength = cell(row, "Claim Strength").lower()
        caveat = cell(row, "Boundary / Caveat")
        status = cell(row, "Status").lower()

        if not claim:
            issues.append(f"{claim_id}: missing claim text.")
        if not source or not contains_any(source, VALID_SOURCES):
            issues.append(f"{claim_id}: missing or invalid evidence source.")
        if not evidence_id:
            issues.append(f"{claim_id}: missing evidence ID.")
        if strength not in VALID_STRENGTHS:
            issues.append(f"{claim_id}: invalid claim strength `{strength}`.")
        if status not in VALID_STATUS:
            issues.append(f"{claim_id}: invalid status `{status}`.")
        if strength in {"interpretation", "management implication", "causal claim"} and not caveat:
            issues.append(f"{claim_id}: interpretive or high-strength claim lacks a boundary/caveat.")
        if strength == "unsupported" and status == "keep":
            issues.append(f"{claim_id}: unsupported claim is marked keep.")
        if strength == "causal claim":
            causal_text = f"{source} {evidence_id} {caveat}"
            has_causal_support = re.search(
                r"counterfactual|experiment|before[- ]after[- ]control|baci|control|causal design|因果设计|对照|实验",
                causal_text,
                re.I,
            )
            states_missing_design = re.search(
                r"(no|without|lack(?:s|ing)?|not available|unavailable).{0,40}"
                r"(counterfactual|causal design|experiment|control|baci)|"
                r"(缺乏|没有|无).{0,20}(反事实|因果设计|对照|实验)",
                caveat,
                re.I,
            )
            if "assumption" in source.lower():
                issues.append(f"{claim_id}: causal claim cannot be supported by assumption as the evidence source.")
            if states_missing_design and status == "keep":
                issues.append(f"{claim_id}: causal claim is marked keep while the caveat states causal design is missing.")
            elif not has_causal_support:
                issues.append(f"{claim_id}: causal claim lacks explicit causal-design support.")
        if status == "needs verification":
            warnings.append(f"{claim_id}: still needs author verification.")
        if any(word.lower() in claim.lower() for word in RISKY_WORDS) and strength not in {
            "model-supported association",
            "interpretation",
            "management implication",
            "causal claim",
        }:
            warnings.append(f"{claim_id}: risky wording may need a stronger evidence link or narrower phrasing.")

    report = [
        "# Claim Ledger Audit",
        "",
        f"- Ledger: `{args.ledger}`",
        f"- Rows audited: {audited_rows}",
        f"- Issues: {len(issues)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Issues",
        "",
        *[f"- {issue}" for issue in issues],
        "",
        "## Warnings",
        "",
        *[f"- {warning}" for warning in warnings],
        "",
        "## Note",
        "",
        "This is a first-pass heuristic audit. Human review is required for ecological interpretation, causal design, citation validity, and journal-specific standards.",
        "",
    ]
    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
