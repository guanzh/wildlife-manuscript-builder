#!/usr/bin/env python3
"""Suggest statistical additions for wildlife monitoring validation manuscripts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


METRIC_PATTERNS = [
    r"召回率",
    r"精确率",
    r"特异度",
    r"准确率",
    r"\brecall\b",
    r"\bprecision\b",
    r"\bspecificity\b",
    r"\baccuracy\b",
]


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit statistical enhancement opportunities.")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    text = args.manuscript.read_text(encoding="utf-8", errors="ignore")
    recs: list[tuple[str, str, str]] = []

    if has_any(text, METRIC_PATTERNS) and not has_any(text, [r"95\s*%|95%|置信区间|confidence interval|Wilson|Clopper"]):
        recs.append(
            (
                "classification-metric-uncertainty",
                "Key detection/classification metrics appear without uncertainty.",
                "Add Wilson or exact binomial 95% confidence intervals for recall, precision, specificity, and accuracy; report denominators.",
            )
        )

    if has_any(text, [r"10\s*(分钟|min)", r"match.{0,12}tolerance", r"开始时间差"]) and not has_any(text, [r"敏感性", r"sensitivity", r"3\s*(分钟|min)", r"5\s*(分钟|min)", r"15\s*(分钟|min)"]):
        recs.append(
            (
                "event-matching-sensitivity",
                "Event-level matching uses a tolerance but no sensitivity analysis is visible.",
                "Recalculate event-level TP/FN/FP under 3, 5, 10, and 15 minute tolerances, or explain why event-level results are secondary.",
            )
        )

    if has_any(text, [r"点位差异", r"recorder-level", r"site-level"]) and not has_any(text, [r"样本量", r"bootstrap", r"置信区间", r"sample size"]):
        recs.append(
            (
                "site-level-uncertainty",
                "Site/recorder differences are discussed without visible uncertainty or sample-size caveat.",
                "Report positive days/events per recorder, add a small-sample caveat, and consider recorder-level bootstrap only if the sampling hierarchy supports it.",
            )
        )

    if has_any(text, [r"置信度", r"confidence", r"probability", r"score"]) and not has_any(text, [r"PR 曲线", r"precision-recall", r"阈值敏感性", r"threshold sensitivity"]):
        recs.append(
            (
                "threshold-curve",
                "Machine confidence output appears available but threshold analysis is not visible.",
                "Add a precision-recall curve or metrics across several score thresholds.",
            )
        )

    if has_any(text, [r"06[:：]30.{0,12}09[:：]30", r"固定.{0,8}窗口", r"fixed.{0,12}window"]) and not has_any(text, [r"窗口外", r"outside.{0,12}window", r"全天", r"full.{0,12}day"]):
        recs.append(
            (
                "sampling-window-boundary",
                "A fixed sampling window is central, but outside-window inference boundary is not visible.",
                "State that the data support patterns within the sampled window and cannot evaluate outside-window calling activity unless additional data are available.",
            )
        )

    report = [
        "# Statistical Enhancement Suggestions",
        "",
        f"- Manuscript: `{args.manuscript}`",
        f"- Recommendations: {len(recs)}",
        "",
        "## Recommendations",
        "",
    ]
    if recs:
        for key, issue, action in recs:
            report.extend([f"### {key}", "", f"- Issue: {issue}", f"- Suggested addition: {action}", ""])
    else:
        report.append("- No first-pass enhancement recommendations found.")
        report.append("")

    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 1 if recs else 0


if __name__ == "__main__":
    raise SystemExit(main())
