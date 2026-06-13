# Acoustic Validation Statistical Enhancements

Reusable patterns for adding statistical rigor to acoustic/automated-recognition validation manuscripts during rewriting. Add these before claiming submission-readiness (Gate 5).

## Wilson 95% Confidence Intervals

All proportion metrics (recall, precision, specificity, accuracy) must report Wilson CIs, not just point estimates. If `scipy.stats` is unavailable, implement manually:

```python
import math

Z_95 = 1.959963984540054  # stats.norm.ppf(0.975)

def wilson_ci(numerator, denominator):
    """Wilson score interval for binomial proportion.
    Returns (center, lower_bound, upper_bound)."""
    if denominator == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = numerator / denominator
    z2 = Z_95 ** 2
    denom = 1 + z2 / denominator
    center = (p + z2 / (2 * denominator)) / denom
    margin = Z_95 * math.sqrt((p * (1 - p) + z2 / (4 * denominator)) / denominator) / denom
    return (center, max(0.0, center - margin), min(1.0, center + margin))

# Usage:
recall_ci = wilson_ci(TP, TP + FN)
precision_ci = wilson_ci(TP, TP + FP)
specificity_ci = wilson_ci(TN, TN + FP)
accuracy_ci = wilson_ci(TP + TN, total)
```

Report as: "Recall 93.7% (95% CI: 90.6–95.8%)"

## Matching Threshold Sensitivity

Re-run event matching at tolerances [0, 5, 10, 15, 20, 30] minutes:

```python
sensitivity_results = []
for tol in [0, 5, 10, 15, 20, 30]:
    human_m, machine_m = event_match(human, machine, tolerance=tol)
    tp = int(machine_m["matched"].sum())
    fn = int((~human_m["matched"]).sum())
    fp = int((~machine_m["matched"]).sum())
    sensitivity_results.append({
        "tolerance_min": tol,
        "TP": tp, "FN": fn, "FP": fp,
        "recall": tp / (tp + fn),
        "precision": tp / (tp + fp),
    })
```

**Interpretation**: If TP varies by ≤2 events across tolerances, the matching rule is stable. Report: "Adjusting tolerance from 0 to 30 min changed TP by only 1-2 events, indicating insensitivity to the matching rule."

## Recorder-Level Wilson CIs

Apply Wilson CIs to each recorder's day-level metrics. For recorders with <10 positive days, CI width will exceed 40pp:

```python
for rid in recorders:
    day_tp = ...; day_fn = ...; day_fp = ...
    recall_ci = wilson_ci(day_tp, day_tp + day_fn)
    precision_ci = wilson_ci(day_tp, day_tp + day_fp)
    # Flag: if (day_tp + day_fn) < 10, add caveat
```

Report with caveat: "SG0011: recall 75.0% [30.1–95.4%], n=4 positive days — wide CI, interpret cautiously"

## Old-vs-New Comparison Table

When re-running analysis reveals data changes between draft versions:

```markdown
| Metric | v5 (old) | v6 (new) | Change |
|---|---|---|---|
| Machine events | 392 | 437 | +45 |
| FP (event) | 38 | 78 | +40 ⚠️ |
| Day precision | 91.9% | 85.2% | -6.7pp ⚠️ |
| Day FP | 27 | 54 | +27 ⚠️ |
```

The comparison table is the evidence basis for claim narrowing in the ledger.

## Excel Reading Quirks in Chinese Research Data

Machine-recognition or field-data `.xlsx` files often have a merged title row:

```
Row 0: "电子长臂猿识别记录" (title, merged across all columns)
Row 1: 序号 | 录音机编号 | 监测群体 | 日期 | ...
```

Always inspect first:
```python
df = pd.read_excel(path)
print(df.head(3))  # Check if row 0 is a title
print(df.columns)  # If 'Unnamed: 1', use header=1
```

Fix: `pd.read_excel(path, header=1)`
