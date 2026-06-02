# Figure and Table Assembly Gate

Use this gate after result cards and before delivering a journal-format manuscript. The goal is to turn a text draft into a reviewable article package with figures, tables, captions, and supplements.

## Principle

A manuscript is not a delivery-ready article if figures and tables are only planned. Central results should appear in self-contained tables or figures unless the target venue explicitly asks for text-only reporting.

## Required Output Template

```md
# Figure and Table Assembly

## Figure/Table Inventory

| Item | File / source | Purpose | Required in main text? | Sensitive-data risk | Status |
|---|---|---|---|---|---|
| Figure 1 |  | study area / sampling design | yes / no | low / medium / high | ready / needs edit / blocked |
| Table 1 |  | sampling and species summary | yes / no | low / medium / high | ready / needs edit / blocked |

## Source-Data Link

For every central figure or table, record the source-data route in `data-availability-source-data.md`. If the source data are sensitive or restricted, state the public summary, masking/generalization method, or access process instead of leaving the route blank.

## Caption Checklist

| Item | Caption includes sample size? | Units? | Uncertainty? | Sensitive locations masked? | Status |
|---|---|---|---|---|---|
|  | yes / no / not applicable | yes / no | yes / no / not applicable | yes / no / not applicable |  |

## Required Main Outputs

For camera-trap community manuscripts, consider:

- Figure 1: study area and camera sites, with sensitive coordinates masked/generalized if needed.
- Table 1: camera effort, date range, sites, target records, species count, protected species summary.
- Table 2: model coefficients for central diversity models.
- Figure 2: main community-level response.
- Figure 3: species-level model responses.
- Figure 4: descriptive ordination/centroid/activity result, only if claim boundary is clear.
- Supplementary table: full species list, HMSC coefficients, variable definitions, diagnostics.

## Word / DOCX Rule

Do not add a table of contents to a manuscript/article DOCX unless explicitly requested or required by the journal target contract.

## Layout QA Checklist

Before calling a DOCX journal-format:

- Open or inspect the DOCX to confirm that figures are embedded rather than replaced by alt text.
- Confirm each figure is followed or preceded by its caption and is referenced in the main text.
- Check that tables fit the page or are moved to supplement when too wide.
- Check that table headers, figure text, legends, and axis labels are readable at manuscript size.
- Confirm no accidental table of contents, duplicate title, broken caption, unresolved author placeholder, or raw internal comment remains.
- Confirm sensitive-species maps are masked, generalized, or shown as relative coordinates.

Use `scripts/check_docx_layout_qa.py` as a first-pass audit, then manually inspect the exported file.

## Passing Standard

Internal draft:

- Figure/table plan is acceptable if clearly marked.

Reviewable manuscript:

- Main figures and tables are present or attached; captions are complete.

Journal-format manuscript:

- Figures/tables match target-journal placement rules, are referenced in text, and have source-data routes mapped.

Submission-ready package:

- Figures/tables are final quality, captions self-contained, source data mapped, sensitive data handled, and supplementary files prepared.
