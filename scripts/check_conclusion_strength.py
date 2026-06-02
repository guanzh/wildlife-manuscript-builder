#!/usr/bin/env python3
"""Audit conclusion strength against common evidence boundaries."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REF_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*(参考文献|references)\s*$", re.I | re.M)

PATTERNS = [
    (
        "replacement-claim",
        [r"替代", r"\breplac(e|es|ed|ing)\b", r"\bsubstitut(e|es|ed|ing)\b"],
        "Direct replacement claims require direct comparison with the method being replaced. If only recorder-derived annotations were compared, narrow to 'reduce reliance on field listening' or 'replace the field-sampling step only'.",
    ),
    (
        "proof-claim",
        [r"证明", r"验证了", r"\bprove[sd]?\b", r"\bdemonstrate[sd]?\b"],
        "Use 'support', 'indicate', or 'are consistent with' unless the design rules out major alternatives.",
    ),
    (
        "reliability-claim",
        [r"可靠判断", r"可靠识别", r"\breliabl(e|y)\b"],
        "Reliability claims should name the scope, reference standard, denominators, and uncertainty.",
    ),
    (
        "standard-protocol-claim",
        [r"标准方案", r"标准流程", r"\bstandard protocol\b", r"\bstandard scheme\b"],
        "Standard-protocol claims require repeated validation, management adoption, or explicit framing as a candidate/working protocol.",
    ),
    (
        "optimal-window-claim",
        [r"最优窗口", r"最佳窗口", r"\boptimal window\b", r"\bbest window\b"],
        "Optimal sampling-window claims require outside-window data or strong independent evidence.",
    ),
    (
        "management-effectiveness-claim",
        [r"保护成效", r"管理成效", r"\bmanagement effectiveness\b", r"\bconservation effectiveness\b"],
        "Management effectiveness requires an intervention design. Otherwise use monitoring relevance or management support.",
    ),
]

WINDOW_TERMS = [r"06[:：]30.{0,12}09[:：]30", r"固定.{0,8}窗口", r"fixed.{0,12}window"]
WINDOW_OVERREACH = [
    r"覆盖.{0,12}主要.{0,8}(鸣叫|活动|calling|activity)",
    r"覆盖.{0,12}(全部|所有|全天|全日).{0,12}(鸣叫活动|日活动|calling activity|daily activity)",
    r"(全天|全日|完整日).{0,12}(鸣叫|活动|calling|activity)",
    r"最优",
    r"最佳",
    r"\bwhole[- ]day\b",
    r"\ball daily\b",
]
WINDOW_SAFETY = [r"窗口外", r"全天", r"outside.{0,12}window", r"full.{0,12}day", r"cannot evaluate activity outside"]
NEGATING_CONTEXT = [r"不应", r"不能", r"并不", r"不是", r"未用于", r"无需", r"not ", r"cannot", r"should not", r"did not"]


def body_without_refs(text: str) -> str:
    match = REF_HEADING.search(text)
    return text[: match.start()] if match else text


def line_number(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def excerpt(text: str, start: int, end: int, width: int = 90) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    snippet = text[left:right].replace("\n", " ")
    return re.sub(r"\s+", " ", snippet).strip()


def add_matches(findings: list[tuple[str, int, str, str]], body: str) -> None:
    for category, patterns, note in PATTERNS:
        for pattern in patterns:
            for match in re.finditer(pattern, body, flags=re.I):
                context = body[max(0, match.start() - 42) : min(len(body), match.end() + 42)]
                if category in {"replacement-claim", "proof-claim"} and any(re.search(p, context, flags=re.I) for p in NEGATING_CONTEXT):
                    continue
                findings.append((category, line_number(body, match.start()), excerpt(body, match.start(), match.end()), note))

    window_lines_reported: set[int] = set()
    for match in re.finditer("|".join(WINDOW_TERMS), body, flags=re.I):
        context = body[max(0, match.start() - 220) : min(len(body), match.end() + 220)]
        has_overreach = any(re.search(p, context, flags=re.I) for p in WINDOW_OVERREACH)
        has_safety = any(re.search(p, context, flags=re.I) for p in WINDOW_SAFETY)
        line = line_number(body, match.start())
        if has_overreach and not has_safety and line not in window_lines_reported:
            window_lines_reported.add(line)
            findings.append(
                (
                    "sampling-window-overreach",
                    line,
                    excerpt(body, match.start(), match.end()),
                    "A fixed-window dataset supports within-window patterns, not all-day or optimal-window claims unless outside-window evidence is provided.",
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit strong conclusion wording in a manuscript.")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    text = args.manuscript.read_text(encoding="utf-8", errors="ignore")
    body = body_without_refs(text)
    findings: list[tuple[str, int, str, str]] = []
    add_matches(findings, body)

    deduped = []
    seen = set()
    for finding in findings:
        key = (finding[0], finding[1], finding[2])
        if key not in seen:
            seen.add(key)
            deduped.append(finding)

    report = [
        "# Conclusion Strength Audit",
        "",
        f"- Manuscript: `{args.manuscript}`",
        f"- Findings: {len(deduped)}",
        "",
        "## Findings",
        "",
    ]
    for category, line, snippet, note in deduped:
        report.extend(
            [
                f"### {category} at line {line}",
                "",
                f"- Excerpt: {snippet}",
                f"- Review note: {note}",
                "- Required action: identify the direct evidence, then narrow or keep the claim.",
                "",
            ]
        )
    report.extend(
        [
            "## Suggested Wording",
            "",
            "- Use 'reduce reliance on field listening' when recorder data did not directly compare against field listening.",
            "- Use 'identified most positive recorder-days under this design' instead of unrestricted 'reliable'.",
            "- Use 'candidate working protocol' instead of 'standard protocol' until repeated validation or adoption is documented.",
            "",
        ]
    )

    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 1 if deduped else 0


if __name__ == "__main__":
    raise SystemExit(main())
