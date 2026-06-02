# Delivery Readiness Score

Use this gate at the end of the workflow to label what has actually been delivered. This prevents overstating an internal draft as a submission-ready manuscript.

## Levels

### Level 1: Internal Scientific Draft

The manuscript has a coherent scientific argument and bounded claims, but may lack journal formatting, figures/tables, metadata, or verified references.

Minimum:

- Data contract.
- Answerable question.
- Argument and terminology contract.
- Result cards.
- Draft manuscript.
- Claim boundary check.

### Level 2: Reviewable Manuscript

The manuscript is ready for advisor, coauthor, or collaborator review.

Minimum:

- Level 1 requirements.
- Literature matrix.
- Citation coverage pass.
- Claim ledger pass.
- Language/overclaim audit pass.
- Main figures/tables planned or attached.
- Author tasks clearly listed.

### Level 3: Journal-Format Manuscript

The manuscript follows a target venue's article format, but may still require author confirmation or final reference verification.

Minimum:

- Level 2 requirements.
- Journal target contract.
- Submission metadata contract.
- Author-knowledge integration completed.
- Main figures/tables assembled or prepared according to journal rules.
- Data availability and source-data gate completed with unresolved items flagged.
- Reference verification completed for central references or issues flagged.
- No table of contents unless required.

### Level 4: Submission-Ready Package

The package can be submitted after author approval.

Minimum:

- Level 3 requirements.
- All metadata confirmed.
- All references verified and formatted.
- Figures/tables final and sensitive data handled.
- Data/code availability routes, source data, repository identifiers or justified restrictions, and FAIR metadata confirmed.
- Ethics, permits, data authorization, conflicts, funding, and author contributions complete.
- Supplementary files, cover letter, and AI-use statement included if required.

## Required Output Template

```md
# Delivery Readiness Score

## Level Assigned

- Level:
- Reason:

## Checklist

| Domain | Level needed | Current status | Blocking issues |
|---|---|---|---|
| Data contract |  |  |  |
| Literature and references |  |  |  |
| Statistical outputs |  |  |  |
| Claim ledger |  |  |  |
| Figures and tables |  |  |  |
| Data/code availability and source data |  |  |  |
| Journal target contract |  |  |  |
| Submission metadata |  |  |  |
| Sensitive data / ethics |  |  |  |
| DOCX/package formatting |  |  |  |

## Upgrade Tasks

| To reach next level | Required task | Owner |
|---|---|---|
|  |  | AI / author / analyst / coauthor |
```

## Final Rule

Do not call a manuscript "submission-ready" unless it reaches Level 4. Use precise wording such as "reviewable manuscript" or "journal-format draft" when appropriate.
