# Data Availability and Source-Data Gate

Use this gate before calling a manuscript journal-format or submission-ready. The goal is to make data/code availability, repository routes, figure source data, sensitive-species restrictions, and reuse metadata explicit instead of leaving them as a generic statement.

## Core Principle

Every central conclusion should have a traceable data route. "Data available upon request" is weak unless legal, ethical, third-party, sensitive-location, or institutional restrictions justify it and an access process is described.

## Dataset Inventory

Inventory every file or dataset that supports main text, figures, tables, supplements, and statistical outputs:

- raw monitoring data,
- cleaned event or detection table,
- effort table,
- site or sampling metadata,
- environmental, remote-sensing, patrol, or threat covariates,
- model outputs and diagnostics,
- figure source data,
- supplementary species list or coefficient tables,
- code, scripts, notebooks, or workflow files,
- reused public datasets and third-party restricted data.

## Access Route

Classify each dataset into one route:

- public repository,
- controlled-access repository,
- within paper or supplement,
- reused public source,
- third-party restricted,
- available on justified request,
- not shareable publicly due to sensitive species or patrol-sensitive locations,
- not applicable.

For sensitive wildlife data, separate:

- public summary data,
- generalized or masked spatial data,
- exact coordinates and raw media,
- patrol-sensitive or enforcement-sensitive information,
- code that can be shared without exposing sensitive locations.

## Source-Data Mapping

Every central figure/table should have source data or a clear reason why the data cannot be public.

| Output | Source data file | Variables / units | Sensitive risk | Access route | Status |
|---|---|---|---|---|---|
| Figure 1 / Table 1 |  |  | low / medium / high |  | ready / needs masking / restricted / missing |

If a figure is based on a model, include the model-output table, uncertainty table, or script that regenerates the panel.

## FAIR and Reuse Metadata

Check whether shareable datasets have:

- stable identifier or planned repository record,
- clear title and description,
- file manifest,
- variable definitions, units, allowed values, and missing-value codes,
- methods and provenance notes,
- software/package versions or script references,
- licence or access terms,
- spatial/temporal coverage at a safe resolution,
- citation or preferred acknowledgement.

## Data Availability Statement Pattern

Draft the statement by mapping datasets to routes:

```text
The [summary/processed] data supporting [figures/tables/results] are available in [repository/supplement] at [identifier/link, if confirmed]. Exact locations and raw media for sensitive species are not publicly released because [reason]; requests for restricted data may be directed to [access route/authority] subject to [conditions]. Code used to reproduce [analyses/figures] is available at [repository] or will be provided [route], excluding files that expose sensitive locations.
```

Do not invent repository names, DOIs, accession numbers, licences, embargo dates, permits, or access committees.

## Required Output

```md
# Data Availability and Source-Data Gate

## Dataset Inventory

| Dataset | Supports | File / location | Access route | Sensitive risk | Status | Author action |
|---|---|---|---|---|---|---|
|  | Figure / Table / Result / Supplement / Code |  | public repository / controlled access / supplement / restricted / request / not applicable | low / medium / high | ready / missing / needs masking / author confirmation |  |

## Source-Data Mapping

| Output | Source data | Reproducibility route | Sensitive handling | Status |
|---|---|---|---|---|
|  |  | script / table / supplement / repository / restricted |  | ready / missing / blocked |

## FAIR Metadata Check

| Item | Status | Action |
|---|---|---|
| Identifier or repository route | ok / missing / restricted |  |
| Data dictionary and units | ok / missing |  |
| Provenance and processing notes | ok / missing |  |
| Licence or access terms | ok / missing / restricted |  |
| Code availability | ok / missing / restricted |  |

## Draft Data Availability Statement

[ready-to-paste text or marked draft]

## Blocking Issues

- 
```

## Passing Standard

Reviewable manuscript: data routes and sensitive-data restrictions are identified, even if author confirmation remains.

Journal-format manuscript: source-data mapping exists for central figures/tables and the data/code availability statement is drafted.

Submission-ready package: repository/access routes, identifiers if applicable, source data, code availability, metadata, licences/access terms, and sensitive-data restrictions are confirmed.
