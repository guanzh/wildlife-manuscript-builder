#!/usr/bin/env python3
"""First-pass DOCX layout QA for manuscript drafts."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


def para_text(p: ET.Element) -> str:
    parts = []
    for t in p.findall(".//w:t", NS):
        if t.text:
            parts.append(t.text)
    return "".join(parts)


def para_has_drawing(p: ET.Element) -> bool:
    return p.find(".//w:drawing", NS) is not None


def table_column_count(tbl: ET.Element) -> int:
    cols = tbl.findall(".//w:tblGrid/w:gridCol", NS)
    if cols:
        return len(cols)
    first_row = tbl.find(".//w:tr", NS)
    return len(first_row.findall("./w:tc", NS)) if first_row is not None else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit DOCX layout quality.")
    parser.add_argument("docx", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    issues: list[str] = []
    warnings: list[str] = []

    with zipfile.ZipFile(args.docx) as z:
        names = set(z.namelist())
        media = [n for n in names if n.startswith("word/media/")]
        content_types = z.read("[Content_Types].xml").decode("utf-8", errors="ignore") if "[Content_Types].xml" in names else ""
        if media and 'Extension="png"' not in content_types and any(n.lower().endswith(".png") for n in media):
            issues.append("PNG images are embedded but [Content_Types].xml lacks a PNG declaration.")
        if "word/document.xml" not in names:
            issues.append("word/document.xml missing.")
            document_xml = b""
        else:
            document_xml = z.read("word/document.xml")

    if document_xml:
        root = ET.fromstring(document_xml)
        paragraphs = root.findall(".//w:p", NS)
        texts = [para_text(p) for p in paragraphs]
        full_text = "\n".join(texts)
        tables = root.findall(".//w:tbl", NS)
        drawings = [i for i, p in enumerate(paragraphs) if para_has_drawing(p)]

        if re.search(r"^\s*(目录|Table of Contents)\s*$", full_text, flags=re.I | re.M):
            issues.append("Possible table of contents detected; manuscript DOCX should omit TOC unless required.")
        for placeholder in ["待补充", "TODO", "请补充", "待作者补充"]:
            if placeholder in full_text:
                warnings.append(f"Placeholder text remains in DOCX: {placeholder}")
        if re.search(r"\d{1,3}\.\d{3,}\s*[°º]?\s*[NSEW]", full_text):
            issues.append("Exact-coordinate-like text appears in DOCX.")

        for idx in drawings:
            nearby = "\n".join(texts[max(0, idx - 1) : min(len(texts), idx + 3)])
            if not re.search(r"(图|Figure|Fig\.)\s*\d+", nearby, flags=re.I):
                warnings.append(f"Image near paragraph {idx + 1} has no nearby figure caption.")

        for i, tbl in enumerate(tables, start=1):
            cols = table_column_count(tbl)
            if cols >= 7:
                warnings.append(f"Table {i} has {cols} columns; check page width and readability.")

        if media and len(drawings) == 0:
            issues.append("Media files exist but no drawing references were found in document.xml.")
        if len(media) < len(drawings):
            warnings.append("There are more drawing references than media files; check external/linked images.")

    report = [
        "# DOCX Layout QA",
        "",
        f"- DOCX: `{args.docx}`",
        f"- Issues: {len(issues)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Issues",
        "",
    ]
    report.extend(f"- {issue}" for issue in issues)
    report.extend(["", "## Warnings", ""])
    report.extend(f"- {warning}" for warning in warnings)
    report.extend(
        [
            "",
            "## Manual Checks Still Required",
            "",
            "- Open the DOCX and inspect table page breaks, caption placement, figure text size, Chinese punctuation, and journal-specific formatting.",
            "- Check that sensitive maps are masked or generalized.",
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
