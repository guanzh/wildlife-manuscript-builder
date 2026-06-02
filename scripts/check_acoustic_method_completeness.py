#!/usr/bin/env python3
"""Check method completeness for acoustic automated-recognition manuscripts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIREMENTS = [
    ("human_annotator_count", "Human annotator count", [r"识别者.{0,12}(人数|名|个)", r"(annotator|listener)s?.{0,20}(number|count|two|independent)"], True),
    ("double_review", "Independent double review or repeat listening", [r"双人", r"独立复听", r"double.{0,12}(review|listening|annotation)", r"independent.{0,12}(review|annotation)"], True),
    ("disagreement_handling", "Disagreement/adjudication rule", [r"分歧", r"一致性", r"adjudicat", r"disagreement", r"consensus"], True),
    ("annotation_software", "Human annotation software/platform", [r"软件", r"Raven", r"Audacity", r"Kaleidoscope", r"Praat", r"annotation software"], False),
    ("event_definition", "Call/event definition", [r"事件定义", r"一次鸣叫", r"one call event", r"event definition"], True),
    ("model_name_version", "Machine model name and version", [r"模型.{0,10}(名称|版本|version)", r"model.{0,12}(name|version)", r"v\d+(?:\.\d+)?"], True),
    ("model_architecture", "Model architecture", [r"CNN|卷积|transformer|Random Forest|SVM|spectrogram|声谱"], True),
    ("training_data", "Training data source/composition", [r"训练数据", r"训练集", r"training data", r"training set"], True),
    ("threshold", "Score/probability threshold", [r"阈值", r"threshold", r"cutoff", r"score"], True),
    ("confidence_output", "Confidence/probability output", [r"置信度", r"概率", r"confidence", r"probability"], False),
    ("postprocessing", "Post-processing/clip merging rule", [r"后处理", r"合并", r"去重", r"post[- ]processing", r"merge"], True),
    ("runtime_environment", "Runtime environment/software", [r"运行环境", r"Python|R语言|R |Torch|PyTorch|TensorFlow", r"runtime"], False),
    ("event_matching_rule", "Event matching rule", [r"匹配规则", r"开始时间差", r"时间重叠", r"matching rule", r"overlap"], True),
    ("matching_sensitivity", "Event matching threshold sensitivity", [r"敏感性", r"3.{0,4}5.{0,4}10.{0,4}15", r"sensitivity.{0,20}(3|5|10|15)"], True),
    ("confidence_interval", "95% confidence intervals for key metrics", [r"95\s*%|95%|置信区间|confidence interval|Wilson|Clopper"], True),
]

PLACEHOLDER_PATTERNS = [
    r"待补充",
    r"请补充",
    r"TODO",
    r"待作者",
    r"需要补充",
    r"补充：",
    r"尚未",
    r"未提供",
    r"缺失",
    r"下一步",
    r"建议",
    r"是否",
    r"如果",
    r"\[.*补充.*\]",
    r"【.*补充.*】",
]


def confirmed_match(text: str, pattern: str) -> bool:
    for match in re.finditer(pattern, text, flags=re.I):
        context = text[max(0, match.start() - 140) : min(len(text), match.end() + 140)]
        if any(re.search(p, context, flags=re.I) for p in PLACEHOLDER_PATTERNS):
            continue
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit acoustic automated-recognition method completeness.")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    text = args.manuscript.read_text(encoding="utf-8", errors="ignore")
    rows = []
    missing_critical = 0
    for key, label, patterns, critical in REQUIREMENTS:
        placeholder_only = any(re.search(pattern, text, flags=re.I) for pattern in patterns)
        found = any(confirmed_match(text, pattern) for pattern in patterns)
        if critical and not found:
            missing_critical += 1
        status = "yes" if found else ("placeholder only" if placeholder_only else "no")
        rows.append((key, label, status, "critical" if critical else "recommended"))

    report = [
        "# Acoustic Automated-Recognition Method Completeness Audit",
        "",
        f"- Manuscript: `{args.manuscript}`",
        f"- Items checked: {len(rows)}",
        f"- Missing critical items: {missing_critical}",
        "",
        "| Key | Method item | Found? | Priority |",
        "|---|---|---|---|",
    ]
    for key, label, found, priority in rows:
        report.append(f"| {key} | {label} | {found} | {priority} |")
    report.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If model name/version, training data, threshold, or post-processing are missing, describe the draft as an application validation or method-validation draft rather than a reproducible model paper.",
            "- If double review and disagreement handling are missing, avoid treating human annotations as absolute truth.",
            "- If matching sensitivity or confidence intervals are missing, report current metrics as point estimates and add a statistical enhancement task.",
            "",
        ]
    )

    output = "\n".join(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 1 if missing_critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
