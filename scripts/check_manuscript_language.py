#!/usr/bin/env python3
"""First-pass language-boundary audit for wildlife manuscript drafts.

The script flags process-language traces and over-strong ecological wording.
It is intentionally conservative: a flagged phrase may be acceptable in a
methods limitation, but it should be reviewed before finalizing the manuscript.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REF_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*(参考文献|references)\s*$", re.I | re.M)

PATTERNS = [
    (
        "process-language",
        [
            r"数据包",
            r"纯数据包",
            r"从零重构",
            r"证据链重构",
            r"当前包",
            r"skill",
            r"workflow",
            r"available files",
            r"data package",
            r"from scratch",
        ],
        "Formal manuscript text should not contain internal workflow or package language.",
    ),
    (
        "strong-causal-language",
        [
            r"检验",
            r"导致",
            r"造成",
            r"驱动",
            r"证明",
            r"决定了",
            r"\bcause[ds]?\b",
            r"\bdriven by\b",
            r"\bprove[sd]?\b",
            r"\bdemonstrate[sd]?\b",
            r"\bdetermine[sd]?\b",
        ],
        "Observational monitoring data usually need cautious association language unless causal or hypothesis-testing design is documented.",
    ),
    (
        "camera-trap-overclaim",
        [
            r"RAI.{0,12}(密度|种群数量|真实数量)",
            r"(相对多度指数|记录率).{0,12}(密度|种群数量|真实数量)",
            r"(RAI|relative abundance index|record rate).{0,30}(density|abundance|population size|true number)",
            r"(density|abundance).{0,30}(RAI|relative abundance index|record rate)",
            r"(absence|不存在).{0,20}(camera|相机|红外)",
        ],
        "RAI, record rate, and camera-trap non-detections should not be treated as density, abundance, or true absence without stronger design.",
    ),
    (
        "hmsc-response-overclaim",
        [
            r"HMSC.{0,40}(真实分布|栖息地偏好|种群下降|回避|密度|保护成效)",
            r"(HMSC|occupancy).{0,40}(true distribution|habitat preference|population decline|avoidance|density|management effectiveness)",
        ],
        "HMSC wording should match the modeled response, often recorded occurrence or site-level recording tendency.",
    ),
    (
        "centroid-overclaim",
        [
            r"(质心|centroid).{0,40}(核心栖息地|庇护地|家域|长期利用|种群核心)",
            r"(质心|二维|ordination|PCA|NMDS|centroid).{0,40}(利用空间|use space)",
            r"(centroid|ordination|PCA|NMDS).{0,40}(core habitat|refuge|home range|long-term use|population core)",
            r"(core habitat|refuge|home range).{0,40}(centroid|ordination|PCA|NMDS)",
        ],
        "Centroid or ordination analyses describe record positions in gradient space, not core habitat or home range unless separately supported.",
    ),
    (
        "undefined-gradient-risk",
        [
            r"保护区边缘空间梯度",
            r"edge spatial gradient",
            r"human RAI",
            r"二维梯度",
            r"two-dimensional gradient",
        ],
        "Core terms should be operationally defined in Introduction or Methods.",
    ),
]


def body_without_refs(text: str) -> str:
    match = REF_HEADING.search(text)
    return text[: match.start()] if match else text


def line_number(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def excerpt(text: str, start: int, end: int, width: int = 70) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    snippet = text[left:right].replace("\n", " ")
    return re.sub(r"\s+", " ", snippet).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit manuscript language boundaries.")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    text = args.manuscript.read_text(encoding="utf-8")
    body = body_without_refs(text)
    findings: list[tuple[str, int, str, str]] = []

    for category, patterns, note in PATTERNS:
        for pattern in patterns:
            for match in re.finditer(pattern, body, flags=re.I):
                findings.append(
                    (
                        category,
                        line_number(body, match.start()),
                        excerpt(body, match.start(), match.end()),
                        note,
                    )
                )

    # Reduce duplicate undefined-term reminders by category/line/excerpt.
    deduped = []
    seen = set()
    for finding in findings:
        key = (finding[0], finding[1], finding[2])
        if key not in seen:
            seen.add(key)
            deduped.append(finding)

    report = [
        "# Manuscript Language Boundary Audit",
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
                "",
            ]
        )
    report.extend(
        [
            "## Note",
            "",
            "This is a first-pass heuristic audit. Human review should decide whether each phrase is acceptable, should be narrowed, or needs a definition.",
            "",
        ]
    )

    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    blocking = [f for f in deduped if f[0] != "undefined-gradient-risk"]
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
