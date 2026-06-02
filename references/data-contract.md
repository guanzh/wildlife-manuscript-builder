# Data Contract

Use this gate after data readiness and before manuscript direction selection. The goal is to freeze what the dataset can safely say, what is derived, what is modeled, and what is still uncertain.

A data contract is not a full analysis. It is a manuscript-facing evidence map. If a number, variable, gradient, sampling rule, species count, or model estimate is not traceable here or in a later result card, it should not appear as a manuscript claim.

## Fact Types

Classify every important fact as one of:

- Observed: read directly from raw records, survey metadata, field logs, device metadata, or verified project notes.
- Derived: produced by filtering, grouping, cleaning, distance calculation, effort standardization, or independent-event rules.
- Modeled: produced by a statistical model, with model file, coefficient table, uncertainty, and covariates recorded.
- Literature-supported: supported by verified publications, reports, databases, or official lists.
- Author-confirmed: supplied by the author but not visible in the data package.
- Unresolved: contradictory, unclear, or missing; cannot be used as a manuscript claim until resolved.

## Required Output Template

```md
# Data Contract

## Source Inventory

| Source file / note | Type | What it contributes | Trust status | Issues |
|---|---|---|---|---|
|  | raw / cleaned / metadata / model / figure / author note / literature |  | usable / usable with caveat / unresolved |  |

## Raw Observed Facts

| Fact ID | Fact | Source | Extraction rule | Manuscript-safe wording |
|---|---|---|---|---|
| F001 |  |  |  |  |

## Derived Analysis Facts

| Fact ID | Derived fact | Inputs | Transformation / filter | Reproducibility status | Manuscript-safe wording |
|---|---|---|---|---|---|
| D001 |  |  |  | reproducible / partially reproducible / not reproducible |  |

## Count Reconciliation

| Quantity | Value A | Source A | Value B | Source B | Reconciled value | Reason | Manuscript wording |
|---|---:|---|---:|---|---:|---|---|
|  |  |  |  |  |  |  |  |

## Variable Provenance

| Variable | Meaning | Unit / coding | Source | Derived from | Valid scale | What it can support | What it cannot support |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  | site / record / species / season / landscape |  |  |

For every core predictor or response variable, add a manuscript definition:

- Edge or spatial gradient: exact calculation, sign/direction, whether it is a true distance, inside/outside status, coordinate axis, ordination axis, or proxy.
- Human RAI or disturbance metric: included event types, excluded event types, standardization denominator, zero structure, and interpretation boundary.
- Site-scale diversity: species pool, taxonomic filters, effort standardization, and whether values are observed or modeled.
- Occurrence/recorded presence: independent-event rule, site-time scale, and whether detection probability is modeled.

## Model-Output Inventory

| Model / output | File | Response | Predictors | Estimate field | Uncertainty field | Can be cited in Results? | Issues |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  | yes / no / after export |  |

## Manuscript-Safe Facts

- 

## Unresolved Facts Not To Use As Claims

- 

## Data-to-Claim Boundary

- Strongest defensible claim:
- Claims requiring narrower wording:
- Claims requiring new data or analysis:
```

## Count Reconciliation Rules

- Prefer reproducible values from raw or cleaned data over values copied from prose, unless the prose value has a documented filtering rule missing from the data.
- If two values differ, name both, identify the likely reason, and choose the most reproducible manuscript value.
- Do not silently average, round away, or select the value that makes the story cleaner.
- If an independent-event rule is not visible, describe the resulting records as "available independent-event table" rather than claiming the full rule is verified.
- If a spatial variable is a proxy, name the proxy. Do not rename it as a true ecological distance unless the calculation supports that wording.

## Camera-Trap Specific Checks

- Camera sites, camera days, sampling dates, and inactive periods.
- Raw detections, empty records, independent records, and target-taxon records.
- Species list, taxonomy, protected status, and uncertain identifications.
- Human, livestock, vehicle, staff, and other disturbance categories.
- Effort standardization used for RAI or detection rates.
- Whether occupancy or abundance claims require detection-probability modeling.
- Whether time-to-independence rules are documented.
- Whether exact sensitive-species coordinates need masking.

## Downgrade Rule

If the data contract cannot freeze survey effort, response variables, key predictors, or species/count totals, do not draft a standard research article. Produce a readiness report, a data-cleaning task list, a monitoring baseline, or a local conservation report.
