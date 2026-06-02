#!/usr/bin/env python3
"""Audit sensitive species location/data-security risks in manuscript packages."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


COORD_PATTERNS = [
    r"\b[NS]\s*\d{1,2}\.\d{3,}",
    r"\b[EW]\s*\d{2,3}\.\d{3,}",
    r"\b\d{1,2}\.\d{3,}\s*[°º]?\s*[NS]",
    r"\b\d{2,3}\.\d{3,}\s*[°º]?\s*[EW]",
    r"(GPS|经度|纬度|longitude|latitude).{0,30}\d{1,3}\.\d{3,}",
]

SAFETY_PATTERNS = [
    r"脱敏",
    r"模糊",
    r"相对坐标",
    r"敏感",
    r"reasonable request",
    r"restricted",
    r"masked",
    r"generalized",
]

RAW_COORD_FILE_PATTERNS = [r"GPS", r"经度", r"纬度", r"longitude", r"latitude", r"坐标"]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def scan_text(path: Path, text: str) -> list[str]:
    issues = []
    for pattern in COORD_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            issues.append(f"{path}: exact-coordinate-like text detected")
            break
    if not any(re.search(pattern, text, flags=re.I) for pattern in SAFETY_PATTERNS):
        issues.append(f"{path}: no visible sensitive-location/data-restriction statement")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit sensitive species location security.")
    parser.add_argument("path", type=Path, help="Manuscript file or package directory")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    target = args.path.expanduser().resolve()
    files = [target] if target.is_file() else [p for p in target.rglob("*") if p.is_file()]
    text_files = [p for p in files if p.suffix.lower() in {".md", ".txt", ".tex", ".csv", ".tsv"}]
    public_doc_files = [p for p in files if p.suffix.lower() in {".md", ".txt", ".tex"}]

    issues: list[str] = []
    warnings: list[str] = []
    for path in public_doc_files:
        issues.extend(scan_text(path, read_text(path)))

    for path in files:
        name = path.name
        if path.suffix.lower() in {".xlsx", ".csv", ".tsv", ".geojson", ".kml", ".kmz", ".gpkg", ".shp"} and any(re.search(pattern, name, flags=re.I) for pattern in RAW_COORD_FILE_PATTERNS):
            warnings.append(f"{path}: coordinate-bearing source file may be unsafe as public supplement")

    if target.is_file() and not text_files:
        warnings.append("Binary document supplied; run a DOCX/PDF text extraction if public coordinate leakage is a concern.")

    report = [
        "# Sensitive Species Data-Security Audit",
        "",
        f"- Target: `{target}`",
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
            "## Required Policy",
            "",
            "- Do not publish exact coordinates for sensitive species.",
            "- Use relative, masked, gridded, or generalized maps.",
            "- Separate raw media, event tables, point metadata, and code in the data availability statement.",
            "- Confirm permit/data authorization before submission-ready status.",
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
