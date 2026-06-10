# Figure-Claim Trace

Verify that every central figure/table caption is consistent with the evidence chain before submission.

## Purpose

Figure captions often drift from the statistical evidence during drafting — a caption may assert a stronger claim than the result card or statistical delivery gate supports. This gate stops that drift.

## When to Run

After figure/table assembly (Step 25) and before data availability mapping (Step 26). Also re-run during the final integrity check (Phase F, Step 30-31).

## Procedure

### 1. List Central Figures/Tables

From the manuscript draft, extract every figure/table designated as "central" (i.e., carries a main result, not supplementary material).

### 2. For Each Figure/Table, Fill the Trace Table

| Field | Source |
|---|---|
| Figure/Table ID | Manuscript (e.g., Figure 1, Table 2) |
| Caption claim (verbatim) | Manuscript caption text |
| Source result card | `references/result-card-template.md` output |
| Statistical gate verdict | `references/statistical-delivery-gate.md` output (ready / usable with caveat / needs analysis / not usable) |
| Claim-ledger entry | `references/claim-ledger.md` — which row maps to this caption? |
| Figure data in source-data map? | `references/data-availability-source-data.md` |

### 3. Flag Mismatches

| Mismatch type | Example | Action |
|---|---|---|
| Caption stronger than statistics | Caption says "significantly increased" but statistical gate says p=0.08 | Narrow caption to "showed a non-significant trend toward increase" |
| Caption contradicts result card | Caption says "occupancy declined" but result card says "no temporal trend detected" | Rewrite caption to match result card |
| Caption missing from claim ledger | Caption asserts a Discussion-level interpretation but claim ledger has no entry | Add to claim ledger or remove interpretive claim from caption |
| Figure data not in source-data map | Figure uses derived data that is not tracked in data-availability | Add source-data entry or mark figure as blocked |

### 4. Blocking Rule

If any central figure caption asserts a **causal** or **management-implication** claim AND the statistical delivery gate marks the underlying result as "needs analysis" or "not usable", **BLOCK journal-format and submission-ready status** for that figure. Options:

- Narrow the caption to descriptive language
- Add explicit caveat in caption
- Demote the figure to supplementary
- Accept the risk and document in limitations

## Output Format

```
### Figure-Claim Trace Report

| Figure | Caption Claim | Result Card | Stat Gate | Ledger | Source Data | Status |
|---|---|---|---|---|---|---|
| Fig 1 | ... | Card #3 | usable with caveat | Row 5 | ✓ | OK (caveat noted) |
| Fig 2 | ... | Card #1 | ready | Row 2 | ✓ | OK |
| Fig 3 | "...significantly reduced..." | Card #4 | needs analysis | Row 7 | ✓ | ⚠️ MISMATCH — narrow caption |

Actions:
- Fig 3: change "significantly reduced" to "tended to be lower (bc=0.32, 95% CI 0.22–0.44)"
```

## Integration with Claim Ledger

After the trace, update `references/claim-ledger.md` to reflect any caption changes. If a caption claim was removed or narrowed, the corresponding claim-ledger row should be updated or marked as "removed from figure, retained in Discussion with caveat."

## Anti-Patterns

- Do not skip this gate because "the figures look fine." Caption drift is invisible until a reviewer catches it.
- Do not accept a caption-statistics mismatch as "close enough." If the statistics don't support the wording, change the wording.
- Do not silently drop a figure whose central claim cannot be traced. Either fix the trace or disclose the gap.
