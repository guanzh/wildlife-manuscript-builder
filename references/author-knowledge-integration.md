# Author-Knowledge Integration Gate

Use this gate when the user provides an existing manuscript, notes, thesis chapter, field protocol, appendix, map, analysis script, or review comments. The goal is to preserve useful author knowledge without inheriting unsupported claims.

This gate is especially important after a data-only rewrite. Data-only testing is useful for evaluating the skill, but deliverable manuscripts should re-integrate author-confirmed local knowledge.

## Classification

Classify author-provided material into four bins:

- Adopt: factual, verifiable, and useful for manuscript completeness.
- Adopt with verification: useful but needs confirmation, citation, or source check.
- Rewrite/narrow: scientifically useful but overclaims the data or uses risky wording.
- Exclude: unsupported, confidential, contradictory, outdated, or irrelevant.

## Required Output Template

```md
# Author-Knowledge Integration

## Source Materials Reviewed

| Source | Type | Used? | Notes |
|---|---|---|---|
|  | manuscript / appendix / protocol / script / review / map / author note | yes / no / partial |  |

## Adopt

| Material | Source | Why adopt | Destination |
|---|---|---|---|
|  |  | confirmed factual detail | Study Area / Methods / Metadata / Figure caption / Acknowledgement |

## Adopt With Verification

| Material | Source | Needed verification | Temporary wording |
|---|---|---|---|
|  |  | author confirmation / DOI / permit / data dictionary / official source |  |

## Rewrite Or Narrow

| Original wording | Problem | Safer wording | Destination |
|---|---|---|---|
|  | causal / density / mechanism / refuge / unsupported management claim |  |  |

## Exclude

| Material | Reason |
|---|---|
|  | confidential / unsupported / duplicate / not relevant |
```

## Common Adoptable Materials

- Study-area geography, climate, elevation, vegetation, and management context.
- Camera model, placement height, trigger settings, deployment dates, spacing, and independent-event rule.
- Funding, author list, affiliations, author notes, and acknowledgements.
- Figure labels, map sources, appendix descriptions, and local place names.
- Target-journal structure, bilingual abstracts, and required sections.

## Common Rewrite/Narrow Materials

- "human activity caused diversity decline" -> "diversity metrics were associated with..."
- "refuge/core habitat" -> "record concentration area" unless separately supported.
- "protected-area effectiveness" -> "record pattern consistent with..."
- "RAI abundance/density" -> "record index" or "relative recording rate".

## Passing Standard

Before final delivery, every useful author-provided factual item should either be integrated, flagged for verification, or explicitly excluded with a reason.
