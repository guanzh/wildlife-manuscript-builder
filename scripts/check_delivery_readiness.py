#!/usr/bin/env python3
"""First-pass delivery readiness audit for a manuscript package directory."""

from __future__ import annotations

import argparse
from pathlib import Path


LEVEL_REQUIREMENTS = {
    1: [
        "data_contract",
        "answerable_unanswered_question",
        "argument_terminology_contract",
        "result_cards",
        "claim_ledger",
        "manuscript_draft",
    ],
    2: [
        "deep_literature_matrix",
        "citation",
        "claim_ledger",
        "section_length",
        "manuscript_language",
        "information_gap",
        "conclusion_strength",
        "method_completeness",
        "reviewer_objection",
    ],
    3: [
        "journal_target_contract",
        "submission_metadata_contract",
        "author_knowledge_integration",
        "statistical_delivery_gate",
        "statistical_enhancement",
        "figure_table_assembly",
        "data_availability_source_data",
        "sensitive_species_security",
        "layout_qa",
        "reference_verification",
    ],
    4: [
        "delivery_readiness_score",
        "integrity_checklist",
    ],
}


def package_files(package_dir: Path) -> list[Path]:
    return [p for p in package_dir.iterdir() if p.is_file()]


def has_token(files: list[Path], token: str) -> bool:
    token = token.lower()
    return any(token in p.stem.lower() for p in files)


def content_nontrivial(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return path.stat().st_size > 0
    body = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
    return len(body.strip()) >= 80


def find_token_file(files: list[Path], token: str) -> Path | None:
    token = token.lower()
    for path in files:
        if token in path.stem.lower():
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit manuscript package delivery readiness.")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    package_dir = args.package_dir.expanduser().resolve()
    files = package_files(package_dir)

    issues: list[str] = []
    warnings: list[str] = []
    level_status: dict[int, list[str]] = {}

    warned_skeletal: set[str] = set()
    for level, tokens in LEVEL_REQUIREMENTS.items():
        missing: list[str] = []
        for token in tokens:
            path = find_token_file(files, token)
            if path is None:
                missing.append(token)
            elif path.suffix.lower() in {".md", ".txt"} and not content_nontrivial(path):
                missing.append(f"{token} (skeletal)")
                if path.name not in warned_skeletal:
                    warned_skeletal.add(path.name)
                    warnings.append(f"{path.name}: appears skeletal or too short for delivery evidence.")
        level_status[level] = missing

    assigned = 0
    for level in sorted(LEVEL_REQUIREMENTS):
        if level_status[level]:
            break
        assigned = level

    docx_files = [p for p in files if p.suffix.lower() == ".docx"]
    toc_suspects = [p.name for p in docx_files if "目录" in p.name and "无目录" not in p.name]
    if toc_suspects:
        issues.append(
            "Possible manuscript DOCX with table of contents or TOC naming detected: "
            + ", ".join(toc_suspects)
            + ". Manuscripts should omit TOC unless required."
        )

    if not docx_files:
        warnings.append("No DOCX output found. Package may be an internal Markdown draft only.")

    report = [
        "# Delivery Readiness Audit",
        "",
        f"- Package: `{package_dir}`",
        f"- Suggested maximum level from file evidence: Level {assigned}",
        f"- DOCX files found: {len(docx_files)}",
        f"- Issues: {len(issues)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Level Missing Items",
        "",
    ]
    for level in sorted(LEVEL_REQUIREMENTS):
        missing = level_status[level]
        report.append(f"### Level {level}")
        report.append("")
        if missing:
            report.extend(f"- missing: {item}" for item in missing)
        else:
            report.append("- required file evidence present")
        report.append("")

    report.extend(["## Issues", ""])
    report.extend(f"- {issue}" for issue in issues)
    report.extend(["", "## Warnings", ""])
    report.extend(f"- {warning}" for warning in warnings)
    report.extend(
        [
            "",
            "## Note",
            "",
            "This is a first-pass file-level audit. Human review is required to decide whether each file is substantively complete and whether the package truly meets the target journal's requirements.",
            "",
        ]
    )

    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
