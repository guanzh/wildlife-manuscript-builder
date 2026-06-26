# Reviewer-Objection Simulator

Use this gate after a complete draft exists and before final integrity review. The goal is to make likely peer-review objections visible while they can still be fixed, narrowed, or disclosed.

This is not a hostile review. It is a stress test of novelty, data design, inference strength, method fit, citation support, and manuscript positioning.

## Reviewer Lenses

Simulate at least five reviewer roles:

- Novelty reviewer: asks whether the manuscript answers a specific under-answered question rather than another local species list.
- Introduction reviewer: asks whether the research gap, core definitions, and objective-method links are explicit.
- Data-design reviewer: checks sampling design, effort, site independence, missingness, and whether the study scale matches the claims.
- Method reviewer: checks whether the selected analysis matches the response variable, uncertainty, detectability, and assumptions.
- Conservation reviewer: checks whether management implications follow from the evidence without causal overreach.
- Citation reviewer: checks nearest literature, method citations, regional context, and reference-list integrity.
- Sensitive-data reviewer: checks permits, ethics, confidential locations, threatened species, and data-sharing limits.

## Required Objection Table

```md
# Reviewer-Objection Simulation

## Manuscript Position Tested

- Article type:
- Target venue type:
- Best answerable unanswered question:
- One-sentence contribution:

## Objection Table

| Reviewer lens | Likely objection | Severity | Evidence behind objection | Required response | Route back to gate | Repair artifact | Manuscript action | Status |
|---|---|---|---|---|---|---|---|---|
| novelty / data design / method / conservation / citation / sensitive data |  | low / medium / high / fatal | data contract / result card / claim ledger / literature matrix / missing metadata | revise / narrow / add limitation / add citation / run analysis / downgrade / author verification | Gate number/name | file or gate output to update |  | open / addressed / disclosed / blocks submission |

## High-Risk Claims To Rewrite

| Claim | Why reviewer may object | Safer wording |
|---|---|---|

## Missing Evidence Or Author Decisions

- 

## Downgrade Decision

- Keep research article:
- Downgrade to short communication / data note / monitoring report / methods note:
- Reason:
```

## Severity Rules

- Low: clarity, wording, or citation can fix it.
- Medium: limitation, additional explanation, or minor reanalysis is needed.
- High: the current claim is too strong or a key method/data issue must be fixed before submission.
- Fatal: the selected article type or central claim is not supported by the dataset.

## Required Responses

For each medium, high, or fatal objection, choose one:

- revise: change manuscript wording or structure.
- narrow: reduce claim strength in title, abstract, results, or discussion.
- add limitation: explicitly state what the data cannot show.
- add citation: add verified nearest literature or method support.
- run analysis: produce new results before keeping the claim.
- downgrade: change deliverable type.
- author verification: require permit, ethics, metadata, or project decision from the author.

## Route-Back Rules

Reviewer objections must not become generic "polish" tasks. Route each medium, high, or fatal objection back to the earliest gate that owns the missing evidence or decision, then name the repair artifact that must change.

| Objection pattern | Route back to | Repair artifact |
|---|---|---|
| Novelty is weak, local-only, or the gap is merely "few studies exist" | Gate 3 / Gate 3.5 | `answerable-unanswered-question.md` output; one-sentence contribution; possible downgrade decision |
| Introduction lacks a specific gap, definitions, or objective-method alignment | Gate 7.5 | Introduction argument plan and citation placement |
| Literature coverage is shallow, outdated, or missing nearest-neighbor comparisons | Gate 7 | Literature matrix with source function and A/B/C/D use depth |
| Statistical result cannot support the central claim | Gate 5.5 / ADP-2 | Statistical delivery gate verdict and result-card status |
| Claim is causal, mechanistic, replacement, or management-effectiveness language without support | Gate 6.5 / ADP-3 | Claim ledger narrowing and claim-boundary wording |
| Figure or table is planned but not assembled, unreadable, or not referenced in text | Gate 8.7 | Figure/table inventory, caption checklist, layout QA |
| Caption asserts a stronger claim than the statistics or result card supports | Gate 8.72 | Figure-claim trace; narrowed caption or removed central figure |
| Data/code availability, source data, or sensitive-data restrictions are unclear | Gate 8.75 / Gate 8.8 | Data availability/source-data map; sensitive-data security decision |
| Citation mismatch, unverifiable source, or reference-list drift | Gate 9 | Citation coverage check and reference verification |
| Metadata, permits, ethics, authorship, or data authorization is missing | Gate 1.6 / Gate 1.8 | Submission metadata contract and information-gap list |

## Common Objections By Data Type

按当前数据类型加载对应 objection 清单。文件位于 `references/domain/objections/`。

| 数据类型 | Objection 文件 |
|---------|---------------|
| Camera trap | `references/domain/objections/camera-trap.md` |
| Acoustic monitoring | `references/domain/objections/acoustic.md` |
| Transect / point survey | `references/domain/objections/transect.md` |
| Occupancy / distribution | `references/domain/objections/occupancy-distribution.md` |
| Remote sensing / habitat | `references/domain/objections/remote-sensing.md` |
| Patrol / threat / management | `references/domain/objections/patrol-threat.md` |
| Multi-source | `references/domain/objections/multi-source.md` |

其他数据类型（植物群落、种群生态、淡水生态等）的 objection 文件在 `references/domain/objections/` 下持续扩展。

加载规则：根据 `data-type-routing.md` 中匹配的当前数据类型，加载对应的 objection 文件。

## Final Rule

Do not treat reviewer-objection simulation as optional polish. If a high or fatal objection remains open, either fix it, downgrade the deliverable, or disclose it as a limitation before finalizing. If a medium, high, or fatal objection has no route-back gate and repair artifact, the simulation is incomplete.
