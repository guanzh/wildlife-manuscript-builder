#!/usr/bin/env python3
"""First-pass audit for wildlife manuscript data packages."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


DATA_EXTS = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".parquet", ".rds", ".rdata", ".json", ".geojson", ".gpkg", ".shp"}
ANALYSIS_EXTS = {".r", ".py", ".ipynb", ".qmd", ".rmd", ".stan", ".jags", ".bugs"}
FIGURE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svg", ".pdf"}
LIT_EXTS = {".bib", ".ris", ".enl"}

KEYWORDS = {
    "dictionary": ["dictionary", "metadata", "codebook", "data_dict", "字段", "变量", "说明", "元数据"],
    "design": ["design", "protocol", "sampling", "effort", "survey", "method", "样点", "样线", "采样", "努力量", "方案"],
    "permit": ["permit", "ethic", "approval", "license", "许可", "伦理", "审批", "授权"],
    "literature": ["reference", "literature", "citation", "文献", "参考"],
}

COLUMN_PATTERNS = {
    "species": r"species|scientific|taxon|物种|种名",
    "site": r"site|station|camera|point|transect|样点|位点|相机|样线",
    "date": r"date|day|日期|年月日",
    "time": r"time|hour|时间|时刻",
    "effort": r"effort|camera.?day|trap.?night|duration|length|努力量|相机日|工作日",
    "latitude": r"lat|latitude|纬度",
    "longitude": r"lon|lng|longitude|经度",
    "detection": r"detection|detect|presence|absence|count|event|记录|检测|出现|数量",
    "covariate": r"elevation|altitude|road|village|forest|habitat|disturb|海拔|道路|村寨|森林|生境|干扰",
}


def match_any(name: str, words: list[str]) -> bool:
    lower = name.lower()
    return any(word.lower() in lower for word in words)


def read_delimited_header(path: Path) -> list[str]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            return next(reader, [])
    except UnicodeDecodeError:
        with path.open("r", encoding="gbk", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            return next(reader, [])
    except Exception:
        return []


def detect_columns(headers: list[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for label, pattern in COLUMN_PATTERNS.items():
        regex = re.compile(pattern, re.IGNORECASE)
        hits = [header for header in headers if regex.search(header)]
        if hits:
            found[label] = hits
    return found


def bullet(items: list[str]) -> str:
    if not items:
        return "- None detected"
    return "\n".join(f"- {item}" for item in items)


def audit(package: Path) -> str:
    files = [p for p in package.rglob("*") if p.is_file()]
    data_files = [p for p in files if p.suffix.lower() in DATA_EXTS]
    analysis_files = [p for p in files if p.suffix.lower() in ANALYSIS_EXTS]
    figure_files = [p for p in files if p.suffix.lower() in FIGURE_EXTS]
    literature_files = [p for p in files if p.suffix.lower() in LIT_EXTS or match_any(p.name, KEYWORDS["literature"])]
    dictionary_files = [p for p in files if match_any(p.name, KEYWORDS["dictionary"])]
    design_files = [p for p in files if match_any(p.name, KEYWORDS["design"])]
    permit_files = [p for p in files if match_any(p.name, KEYWORDS["permit"])]

    column_hits: dict[str, list[str]] = {}
    sampled_headers: list[str] = []
    for path in data_files:
        if path.suffix.lower() in {".csv", ".tsv", ".txt"}:
            headers = read_delimited_header(path)
            if headers:
                sampled_headers.append(f"{path.name}: {', '.join(headers[:20])}")
                detected = detect_columns(headers)
                for key, hits in detected.items():
                    column_hits.setdefault(key, [])
                    column_hits[key].extend([f"{path.name}.{hit}" for hit in hits])

    essentials = {
        "data files": bool(data_files),
        "data dictionary/metadata": bool(dictionary_files),
        "sampling design/effort notes": bool(design_files) or "effort" in column_hits,
        "species/taxon field": "species" in column_hits,
        "site/station field": "site" in column_hits,
        "date or time field": "date" in column_hits or "time" in column_hits,
        "detection/count field": "detection" in column_hits,
        "analysis code or model output": bool(analysis_files),
        "literature/citation file": bool(literature_files),
        "permit/ethics/authorization notes": bool(permit_files),
    }
    score = sum(essentials.values())

    missing = [name for name, ok in essentials.items() if not ok]
    coordinate_sensitive = "latitude" in column_hits and "longitude" in column_hits

    lines = [
        "# Wildlife Manuscript Data Package Audit",
        "",
        f"Package: `{package}`",
        f"Files scanned: {len(files)}",
        f"Readiness score: {score}/{len(essentials)}",
        "",
        "## Detected Files",
        "",
        "### Data files",
        bullet([str(p.relative_to(package)) for p in data_files[:30]]),
        "",
        "### Data dictionary / metadata candidates",
        bullet([str(p.relative_to(package)) for p in dictionary_files[:20]]),
        "",
        "### Sampling design / effort candidates",
        bullet([str(p.relative_to(package)) for p in design_files[:20]]),
        "",
        "### Analysis files",
        bullet([str(p.relative_to(package)) for p in analysis_files[:20]]),
        "",
        "### Figure files",
        bullet([str(p.relative_to(package)) for p in figure_files[:20]]),
        "",
        "### Literature files",
        bullet([str(p.relative_to(package)) for p in literature_files[:20]]),
        "",
        "### Permit / ethics / authorization candidates",
        bullet([str(p.relative_to(package)) for p in permit_files[:20]]),
        "",
        "## Column Signals From Delimited Files",
        "",
    ]

    if sampled_headers:
        lines.extend(f"- {item}" for item in sampled_headers[:10])
    else:
        lines.append("- No readable CSV/TSV/TXT headers detected.")

    lines.extend(["", "## Essential Checks", ""])
    for name, ok in essentials.items():
        lines.append(f"- [{'x' if ok else ' '}] {name}")

    lines.extend(["", "## Missing or Needs Confirmation", ""])
    lines.extend(f"- {item}" for item in missing) if missing else lines.append("- No first-pass missing essentials detected.")

    lines.extend(["", "## Sensitive Location Warning", ""])
    if coordinate_sensitive:
        lines.append("- Latitude and longitude columns were detected. Mask or generalize coordinates for threatened species and public drafts.")
    else:
        lines.append("- No obvious latitude/longitude pair detected in delimited headers.")

    lines.extend(["", "## Suggested Next Step", ""])
    if score < 6:
        lines.append("Do not draft a manuscript yet. Complete the missing metadata, sampling design, and responsibility materials first.")
    elif score < 9:
        lines.append("Draft a research question map and analysis plan before writing manuscript prose.")
    else:
        lines.append("Proceed to data-type routing, question-method mapping, and result cards.")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a wildlife manuscript data package.")
    parser.add_argument("package_dir", help="Directory containing data, metadata, analysis, and literature files.")
    parser.add_argument("-o", "--output", help="Optional markdown output path.")
    args = parser.parse_args()

    package = Path(args.package_dir).expanduser().resolve()
    if not package.exists() or not package.is_dir():
        raise SystemExit(f"Package directory not found: {package}")

    report = audit(package)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
