#!/usr/bin/env python3
"""Create a wildlife manuscript draft package skeleton."""

from __future__ import annotations

import argparse
from pathlib import Path


FILES = {
    "00_readiness_report.md": "# Readiness Report\n\n",
    "01_journal_target_contract.md": "# Journal Target Contract\n\n",
    "02_submission_metadata_contract.md": "# Submission Metadata Contract\n\n",
    "03_data_contract.md": "# Data Contract\n\n",
    "04_author_knowledge_integration.md": "# Author-Knowledge Integration\n\n",
    "05_manuscript_potential_grade.md": "# Manuscript Potential Grade\n\n",
    "06_deliverable_direction.md": "# Deliverable Direction\n\n",
    "07_deep_research_plan.md": "# Deep Research Plan\n\n",
    "08_deep_literature_matrix.md": "# Deep Literature Matrix\n\n",
    "09_answerable_unanswered_question.md": "# Answerable Unanswered Question Check\n\n",
    "10_argument_terminology_contract.md": "# Argument and Terminology Contract\n\n",
    "11_research_question_map.md": "# Research Question Map\n\n",
    "12_analysis_plan.md": "# Analysis Plan\n\n",
    "13_statistical_delivery_gate.md": "# Statistical Delivery Gate\n\n",
    "14_result_cards.md": "# Result Cards\n\n",
    "15_figure_table_assembly.md": "# Figure and Table Assembly\n\n",
    "16_data_availability_source_data.md": "# Data Availability and Source-Data Gate\n\n",
    "17_literature_matrix.md": "# Literature Matrix\n\n",
    "18_section_length_quality_gate.md": "# Section Length Quality Gate\n\n",
    "19_introduction_quality_gate.md": "# Introduction Quality Gate\n\n",
    "20_claim_ledger.md": "# Claim Ledger\n\n",
    "21_manuscript_draft.md": None,
    "22_discussion_conclusion_quality_gate.md": "# Discussion and Conclusion Quality Gate\n\n",
    "23_reviewer_objection_simulation.md": "# Reviewer-Objection Simulation\n\n",
    "24_reference_verification.md": "# Reference Verification\n\n",
    "25_integrity_checklist.md": "# Integrity Checklist\n\n",
    "26_delivery_readiness_score.md": "# Delivery Readiness Score\n\n",
    "27_author_decision_list.md": "# Author Decision List\n\n",
    "28_ai_use_statement.md": None,
    "29_revision_tasks.md": "# Revision Tasks\n\n",
}

MANUSCRIPT = """# {title}

## Abstract

## Introduction

## Methods

### Study Area

### Data Collection

### Data Processing

### Statistical Analysis

### Ethics, Permits, and Sensitive Data Handling

## Results

## Discussion

### Conservation Implications

### Limitations and Future Work

## Conclusion

## Data and Code Availability

## AI Use Statement

## References
"""

AI_USE = """# AI Use Statement

During manuscript preparation, AI tools were used to assist with [describe uses]. The authors reviewed and verified all AI-assisted content, including factual claims, citations, statistical interpretations, and conservation conclusions. AI tools were not used to make final research judgments, verify permits, determine authorship, or replace human responsibility for manuscript accuracy and integrity. Sensitive species locations and confidential project data were [not shared / shared only within approved systems].
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a wildlife manuscript package skeleton.")
    parser.add_argument("output_dir", help="Directory to create or populate.")
    parser.add_argument("--title", default="[Working Title]", help="Working manuscript title.")
    args = parser.parse_args()

    out = Path(args.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    for name, content in FILES.items():
        path = out / name
        if path.exists():
            continue
        if name == "21_manuscript_draft.md":
            content = MANUSCRIPT.format(title=args.title)
        elif name == "28_ai_use_statement.md":
            content = AI_USE
        path.write_text(content or "", encoding="utf-8")

    print(f"Created manuscript package skeleton: {out}")


if __name__ == "__main__":
    main()
