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

| Reviewer lens | Likely objection | Severity | Evidence behind objection | Required response | Manuscript action | Status |
|---|---|---|---|---|---|---|
| novelty / data design / method / conservation / citation / sensitive data |  | low / medium / high / fatal | data contract / result card / claim ledger / literature matrix / missing metadata | revise / narrow / add limitation / add citation / run analysis / downgrade / author verification |  | open / addressed / disclosed / blocks submission |

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

Do not treat reviewer-objection simulation as optional polish. If a high or fatal objection remains open, either fix it, downgrade the deliverable, or disclose it as a limitation before finalizing.
