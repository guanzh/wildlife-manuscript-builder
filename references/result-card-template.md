# Result Card Template

Create one card for every major result before drafting Results.

```md
## Result Card: [R001 short label]

- Result sentence:
- Data-contract fact IDs:
- Figure/table:
- Data source:
- Survey effort / sample size:
- Model or statistic:
- Estimate / effect size:
- Uncertainty:
- Interpretation strength: clear / directional but uncertain / no clear association / descriptive only
- Direction and ecological meaning:
- Supported claim:
- Unsupported claim:
- Needed caveat:
- Discussion entry point:
- Nearest comparison papers:
- Claim-ledger IDs supported:
```

## Discussion Evidence Rule

When a result card supports a central Discussion claim, the Discussion should mention the estimate/effect direction and uncertainty in compact form. If the result is directional but uncertain, Discussion language must use "suggests", "is consistent with", or "directional pattern" rather than definitive wording.

## Literature Matrix

```md
| Function | Citation | Why it matters | Manuscript location | Used in text? | Verified from original? |
|---|---|---|---|---|---|
| Background anchor |  |  | Introduction | No | No |
| Nearest-neighbor problem |  |  | Introduction/Discussion | No | No |
| Method decision |  |  | Methods | No | No |
| Discussion comparison |  |  | Discussion | No | No |
| Regional/species context |  |  | Introduction/Discussion | No | No |
| Software/data citation |  |  | Methods | No | No |
```

## Claim Link Rule

Every result card should support at least one claim-ledger row unless it is only exploratory or supplementary. Every Results claim should point back to a result-card ID.

## Figure/Table Plan

```md
| Display item | Purpose | Data source | Key message | Draft caption | Status |
|---|---|---|---|---|---|
| Figure 1 | Study area/sampling design |  |  |  | planned |
| Figure 2 | Main result |  |  |  | planned |
| Table 1 | Survey effort/data summary |  |  |  | planned |
```
