#!/usr/bin/env python3
"""First-pass citation coverage audit for Markdown manuscripts.

This is intentionally conservative. It flags likely missing or unused
author-year citations, but it does not replace human reference checking.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REF_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*(参考文献|references)\s*$", re.I | re.M)
YEAR = r"(?:19|20)\d{2}"
CITATION_PARENS = re.compile(r"[（(]([^()（）]*" + YEAR + r"[^()（）]*)[）)]")


def split_body_refs(text: str) -> tuple[str, str]:
    match = REF_HEADING.search(text)
    if not match:
        return text, ""
    return text[: match.start()], text[match.end() :]


def normalize_token(token: str) -> str:
    token = re.sub(r"\s+", " ", token.strip())
    token = token.replace("，", ",")
    return token.lower()


def normalize_author(author: str) -> str:
    author = author.strip()
    author = re.sub(r"\bet\s+al\.?", "", author, flags=re.I)
    author = author.replace("等", "")
    author = re.split(r"\s+and\s+|[,，;；、&]", author, flags=re.I)[0].strip()
    if re.search(r"[\u4e00-\u9fff]", author):
        return author
    parts = author.split()
    return parts[0] if parts else author


def citation_key_from_ref(line: str) -> str | None:
    line = line.strip().lstrip("-*0123456789.[] ")
    if not line:
        return None
    year_match = re.search(YEAR, line)
    if not year_match:
        return None
    year = year_match.group(0)
    before = line[: year_match.start()].strip()
    if not before:
        return None

    author = normalize_author(before)
    if author:
        return normalize_token(f"{author} {year}")

    return None


def extract_inline_citations(body: str) -> set[str]:
    found: set[str] = set()
    body = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", body)
    body = re.sub(r"\[[^\]]+\]\([^)]+\)", "", body)
    for paren in CITATION_PARENS.finditer(body):
        content = paren.group(1)
        for segment in re.split(r"[;；]", content):
            year_match = re.search(YEAR, segment)
            if not year_match:
                continue
            year = year_match.group(0)
            author = normalize_author(segment[: year_match.start()])
            if author:
                found.add(normalize_token(f"{author} {year}"))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Markdown citation coverage.")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--min-references", type=int, default=0, help="Optional minimum reference count for the chosen deliverable.")
    args = parser.parse_args()

    text = args.manuscript.read_text(encoding="utf-8")
    body, refs = split_body_refs(text)
    inline = extract_inline_citations(body)
    ref_lines = [line for line in refs.splitlines() if line.strip()]
    ref_keys = {key for line in ref_lines if (key := citation_key_from_ref(line))}

    unused_refs = sorted(ref_keys - inline)
    missing_refs = sorted(inline - ref_keys)
    too_few_refs = args.min_references > 0 and len(ref_keys) < args.min_references

    report = [
        "# Citation Coverage Audit",
        "",
        f"- Manuscript: `{args.manuscript}`",
        f"- In-text citation keys found: {len(inline)}",
        f"- Reference keys found: {len(ref_keys)}",
        f"- Minimum reference threshold: {args.min_references if args.min_references else 'not set'}",
        f"- Below minimum threshold: {'yes' if too_few_refs else 'no'}",
        f"- Reference keys not cited in text: {len(unused_refs)}",
        f"- In-text citation keys missing from references: {len(missing_refs)}",
        "",
        "## Reference Keys Not Cited in Text",
        "",
        *[f"- {x}" for x in unused_refs],
        "",
        "## In-Text Citation Keys Missing from References",
        "",
        *[f"- {x}" for x in missing_refs],
        "",
        "## Reference Count Threshold",
        "",
        f"- Required: {args.min_references if args.min_references else 'not set'}",
        f"- Found: {len(ref_keys)}",
        f"- Status: {'below threshold' if too_few_refs else 'pass'}",
        "",
        "## Note",
        "",
        "This is a first-pass heuristic audit. Human verification is required for multi-author citations, non-standard styles, translated names, software citations, reports, URLs, and DOI metadata.",
        "",
    ]
    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 1 if unused_refs or missing_refs or too_few_refs else 0


if __name__ == "__main__":
    raise SystemExit(main())
