#!/usr/bin/env python3
"""Audit soft section-length fit for wildlife manuscript drafts."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
MD_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
PLAIN_HEADING_RE = re.compile(r"^\s*(.+?)\s*$")


@dataclass(frozen=True)
class SectionRule:
    target_min: int
    target_max: int
    review_min: int
    review_max: int
    pct_min: float | None = None
    pct_max: float | None = None
    pct_review_min: float | None = None
    pct_review_max: float | None = None


PROFILES: dict[str, dict[str, SectionRule]] = {
    "standard": {
        "introduction": SectionRule(700, 1200, 550, 1400, 0.10, 0.15, 0.08, 0.18),
        "discussion": SectionRule(1400, 2400, 1000, 2800, 0.20, 0.30, 0.16, 0.35),
        "conclusion": SectionRule(150, 350, 100, 500),
    },
    "brief": {
        "introduction": SectionRule(300, 650, 250, 800, 0.09, 0.17, 0.07, 0.20),
        "discussion": SectionRule(600, 1100, 450, 1300, 0.18, 0.33, 0.14, 0.38),
        "conclusion": SectionRule(100, 250, 60, 350),
    },
    "data-note": {
        "introduction": SectionRule(350, 750, 250, 900, 0.10, 0.18, 0.07, 0.22),
        "discussion": SectionRule(700, 1300, 500, 1600, 0.20, 0.35, 0.15, 0.40),
        "conclusion": SectionRule(100, 300, 60, 400),
    },
    "extended": {
        "introduction": SectionRule(850, 1300, 650, 1500, 0.09, 0.15, 0.07, 0.18),
        "discussion": SectionRule(1800, 2700, 1300, 3200, 0.20, 0.32, 0.16, 0.38),
        "conclusion": SectionRule(180, 400, 100, 550),
    },
}


CANONICAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("abstract", re.compile(r"^abstract$", re.I)),
    ("introduction", re.compile(r"^(introduction|introduction and objectives)$", re.I)),
    (
        "methods",
        re.compile(
            r"^(methods|materials and methods|methodology|study area and methods)$",
            re.I,
        ),
    ),
    ("results", re.compile(r"^results$", re.I)),
    ("discussion", re.compile(r"^(discussion|discussion and conclusion|discussion and conclusions)$", re.I)),
    ("conclusion", re.compile(r"^(conclusion|conclusions)$", re.I)),
    ("references", re.compile(r"^(references|literature cited|bibliography|参考文献)$", re.I)),
    (
        "back_matter",
        re.compile(
            r"^(acknowledg(e)?ments|data availability|data and code availability|"
            r"code availability|ethics statement|author contributions|ai use statement)$",
            re.I,
        ),
    ),
]


SECTION_ORDER = ["introduction", "methods", "results", "discussion", "conclusion"]
AUDIT_SECTIONS = ["introduction", "discussion", "conclusion"]


def clean_heading(raw: str) -> str:
    heading = re.sub(r"[*_`]+", "", raw).strip()
    heading = re.sub(r"^\d+(\.\d+)*\.?\s+", "", heading)
    heading = heading.rstrip(":").strip()
    return heading


def canonical_heading(line: str) -> str | None:
    if not line.strip():
        return None
    md_match = MD_HEADING_RE.match(line)
    if md_match:
        candidate = clean_heading(md_match.group(2))
    else:
        if len(line.strip()) > 80:
            return None
        plain_match = PLAIN_HEADING_RE.match(line)
        if not plain_match:
            return None
        candidate = clean_heading(plain_match.group(1))
    for canonical, pattern in CANONICAL_PATTERNS:
        if pattern.match(candidate):
            return canonical
    return None


def extract_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        heading = canonical_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        if MD_HEADING_RE.match(line):
            continue
        if current and current not in {"references", "back_matter"}:
            sections.setdefault(current, []).append(line)
        if current in {"references", "back_matter"}:
            current = None
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def counts(text: str) -> tuple[int, int, int]:
    english_words = len(WORD_RE.findall(text))
    cjk_chars = len(CJK_RE.findall(text))
    word_equivalent = english_words + round(cjk_chars / 2)
    return english_words, cjk_chars, word_equivalent


def pct(value: int, denominator: int | None) -> float | None:
    if not denominator:
        return None
    return value / denominator


def classify(section: str, value: int, proportion: float | None, rule: SectionRule) -> tuple[str, str, str]:
    if value == 0:
        article = "an" if section[0].lower() in {"a", "e", "i", "o", "u"} else "a"
        return "missing", "section not detected or empty", f"add {article} {section} section if required by the article type"
    if value < rule.review_min:
        return (
            "underdeveloped",
            f"below review zone minimum ({rule.review_min})",
            "add only the missing writing functions; do not pad with generic background",
        )
    if value > rule.review_max:
        return (
            "overextended",
            f"above review zone maximum ({rule.review_max})",
            "remove repetition, unsupported interpretation, or material belonging elsewhere",
        )
    if value < rule.target_min or value > rule.target_max:
        return (
            "review",
            f"outside functional target ({rule.target_min}-{rule.target_max}) but inside review zone",
            "keep if the section is functionally complete and journal-compliant",
        )
    if (
        proportion is not None
        and rule.pct_review_min is not None
        and rule.pct_review_max is not None
        and (proportion < rule.pct_review_min or proportion > rule.pct_review_max)
    ):
        return (
            "review",
            f"proportion {proportion:.1%} is outside soft proportion review zone",
            "check whether total manuscript balance or section boundaries are unusual",
        )
    if (
        proportion is not None
        and rule.pct_min is not None
        and rule.pct_max is not None
        and (proportion < rule.pct_min or proportion > rule.pct_max)
    ):
        return (
            "review",
            f"proportion {proportion:.1%} is outside typical target proportion",
            "keep if the absolute length and section function are justified",
        )
    return "ok", "within soft target", "no length-driven revision needed"


def markdown_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    header = rows[0]
    sep = ["---"] * len(header)
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Introduction, Discussion, and Conclusion section lengths.")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument(
        "--article-type",
        choices=sorted(PROFILES),
        default="standard",
        help="Length profile to apply. Default: standard.",
    )
    parser.add_argument(
        "--target-main-words",
        type=int,
        help="Target main-text word count for proportion checks. If omitted, detected main sections are used.",
    )
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Return non-zero when a section is missing, underdeveloped, overextended, or review.",
    )
    args = parser.parse_args()

    text = args.manuscript.read_text(encoding="utf-8")
    sections = extract_sections(text)
    section_counts = {name: counts(sections.get(name, "")) for name in SECTION_ORDER}
    detected_main_words = sum(section_counts[name][2] for name in SECTION_ORDER)
    denominator = args.target_main_words or detected_main_words or None
    denominator_source = "target-main-words" if args.target_main_words else "detected main sections"

    rows = [["Section", "English words", "CJK chars", "Word-equivalent", "Proportion", "Status", "Reason", "Action"]]
    statuses: list[str] = []
    for section in AUDIT_SECTIONS:
        english_words, cjk_chars, word_equivalent = section_counts[section]
        proportion = pct(word_equivalent, denominator)
        status, reason, action = classify(section, word_equivalent, proportion, PROFILES[args.article_type][section])
        statuses.append(status)
        rows.append(
            [
                section.title(),
                str(english_words),
                str(cjk_chars),
                str(word_equivalent),
                f"{proportion:.1%}" if proportion is not None else "n/a",
                status,
                reason,
                action,
            ]
        )

    report = [
        "# Section Length Quality Gate",
        "",
        f"- Manuscript: `{args.manuscript}`",
        f"- Article type profile: {args.article_type}",
        f"- Detected main-text word-equivalent: {detected_main_words}",
        f"- Proportion denominator: {denominator if denominator is not None else 'n/a'} ({denominator_source})",
        "",
        "## Section Lengths",
        "",
        *markdown_table(rows),
        "",
        "## Interpretation",
        "",
        "- These are soft thresholds. A warning means review the section function, not automatically expand or cut text.",
        "- For a standard empirical article, the profile assumes roughly 6,000-9,000 English words in main text.",
        "- If the target journal has a different word limit, use the journal target contract as the override.",
        "",
    ]

    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    if args.fail_on_review and any(status != "ok" for status in statuses):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
