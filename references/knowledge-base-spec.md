# Knowledge Base Spec

> 从 AutoResearchClaw 的结构化 KB 吸收。每次 manuscript build 输出结构化 KB，可直接被 RWKM v2.0 的 registry 吸收。

## deliverable/kb/ 目录结构

```
deliverables/
├── kb/
│   ├── decisions.jsonl
│   ├── findings.jsonl
│   ├── literature.jsonl
│   └── reviews.jsonl
├── manuscript.docx
├── figures/
└── ...
```

## decisions.jsonl

记录所有 gate 决策：

```json
{"decision_id": "D20260608001", "gate": "Gate 2: Answerable Question", "decision": "PROCEED", "rationale": "Deep research confirmed gap in gibbon occupancy-habitat relationship at fine scale.", "timestamp": "2026-06-08T10:30:00Z"}
```

## findings.jsonl

记录每条 evidence 的最终状态（直接对接到 RWKM evidence_matrix）：

```json
{"finding_id": "F20260608001", "evidence_id": "E001", "claim_id": "C001", "status": "included", "strength": "medium", "manuscript_section": "Results", "figure_ref": "Fig 2"}
```

## literature.jsonl

引用矩阵：

```json
{"source_id": "F20260607_ref_012", "title": "...", "function": "method_decision", "verification": "verified", "used_in_sections": ["Introduction", "Methods", "Discussion"]}
```

## reviews.jsonl

Reviewer objection 及处理：

```json
{"objection_id": "R001", "objection": "Sample size too small for occupancy model", "severity": "high", "resolution": "Added explicit caveat in Limitations; downgraded claim strength from 'strong' to 'moderate'"}
```

## RWKM 对接

```
WMB kb/decisions.jsonl → RWKM decision_log.md
WMB kb/findings.jsonl  → RWKM evidence_matrix.jsonl + claim_matrix.jsonl
WMB kb/literature.jsonl → RWKM source_registry.jsonl (source_type=literature_pdf)
WMB kb/reviews.jsonl    → RWKM conflict_log.md (reviewer objections as conflicts)
```
