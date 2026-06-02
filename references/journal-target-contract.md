# Journal Target Contract

Use this gate before drafting a deliverable manuscript. The goal is to prevent a scientifically sound draft from missing journal-specific requirements.

If the user has not named a target journal, create a provisional contract for the most likely deliverable path and mark journal-specific items as author-confirmation needed.

## Default Rule

Do not add a table of contents to a manuscript or article DOCX unless the user explicitly asks for it or the target journal requires it.

## Required Output Template

```md
# Journal Target Contract

## Target

- Target journal / venue:
- Article type:
- Language:
- Intended audience:
- Submission stage: internal draft / collaborator review / journal-format manuscript / submission-ready package

## Format Requirements

| Item | Requirement | Current status | Action |
|---|---|---|---|
| Title |  | ok / missing / needs revision |  |
| Running title |  | ok / missing / not required |  |
| Chinese abstract |  | ok / missing / not required |  |
| English abstract |  | ok / missing / not required |  |
| Structured abstract headings |  | yes / no / unknown |  |
| Keywords |  | ok / missing |  |
| Word count |  | ok / over / under / unknown |  |
| Main-text word count |  | ok / over / under / unknown |  |
| Introduction length budget |  | ok / review / journal override / unknown |  |
| Discussion length budget |  | ok / review / journal override / unknown |  |
| Conclusion length budget |  | ok / review / journal override / unknown |  |
| Heading levels |  | ok / needs formatting |  |
| Figures in text or separate files |  | in text / separate / unknown |  |
| Tables in text or separate files |  | in text / separate / unknown |  |
| Reference style |  | author-year / numbered / journal-specific / unknown |  |
| Table of contents | default no | omitted / required / accidentally added |  |

## Provisional Section-Length Budget

Use `section-length-quality-gate.md` when the journal does not provide section-level limits.

| Section | Provisional budget | Journal override | Current status | Action |
|---|---:|---|---|---|
| Introduction | 700-1,200 words for a standard 6,000-9,000 word English empirical article |  | ok / review / underdeveloped / overextended / unknown |  |
| Discussion | 1,400-2,400 words for a standard 6,000-9,000 word English empirical article |  | ok / review / underdeveloped / overextended / unknown |  |
| Conclusion | 150-350 words for a standard 6,000-9,000 word English empirical article |  | ok / review / underdeveloped / overextended / unknown |  |

## Required Statements

| Statement | Requirement | Current status | Author action |
|---|---|---|---|
| Ethics / permits |  | provided / missing / not applicable |  |
| Data availability |  | provided / missing / restricted |  |
| Code availability |  | provided / missing / restricted |  |
| Sensitive-location policy |  | provided / missing |  |
| Funding |  | provided / missing |  |
| Conflicts of interest |  | provided / missing |  |
| Author contributions |  | provided / missing |  |
| AI-use disclosure |  | provided / missing / journal dependent |  |

## Output Files

- Manuscript DOCX:
- Clean no-TOC manuscript DOCX:
- Figures:
- Tables:
- Supplementary material:
- Cover letter:
- Response/revision notes:
```

## Passing Standard

A manuscript is not "journal-format" unless this contract is filled and all required format and statement items are either provided or explicitly marked as author-confirmation needed.

A manuscript is not "submission-ready" unless every required item is provided, verified, and formatted for the target journal.
