# Submission Metadata Contract

Use this gate when the target deliverable is a manuscript, short communication, data note, report, or submission package. The goal is to separate confirmed submission metadata from items that the AI must not invent.

## Principle

Do not invent authorship, affiliation, funding, permits, ethics approval, conflicts, data authorization, sensitive-location policy, or author contributions. If a source manuscript contains these items, classify them and carry them forward only if they are author-provided or otherwise verifiable.

## Status Categories

- confirmed: explicitly provided by the user, project file, original manuscript, grant document, permit, or official source.
- needs author confirmation: present but ambiguous, outdated, incomplete, or sensitive.
- not required: target journal or article type does not require it.
- do not use: unsupported, contradictory, confidential, or likely invented.

## Required Output Template

```md
# Submission Metadata Contract

## Manuscript Identity

- Working title:
- Short title:
- Article type:
- Target journal:
- Language:

## Authors and Affiliations

| Item | Value | Source | Status | Action |
|---|---|---|---|---|
| Author list |  |  | confirmed / needs author confirmation / do not use |  |
| Author order |  |  | confirmed / needs author confirmation / do not use |  |
| Affiliations |  |  | confirmed / needs author confirmation / do not use |  |
| Corresponding author(s) |  |  | confirmed / needs author confirmation / do not use |  |
| Equal contribution notes |  |  | confirmed / needs author confirmation / do not use |  |

## Funding and Acknowledgements

| Item | Value | Source | Status | Action |
|---|---|---|---|---|
| Funding project |  |  | confirmed / needs author confirmation / do not use |  |
| Grant number |  |  | confirmed / needs author confirmation / do not use |  |
| Acknowledgements |  |  | confirmed / needs author confirmation / do not use |  |

## Compliance Statements

| Statement | Current text | Source | Status | Action |
|---|---|---|---|---|
| Survey permit |  |  | confirmed / needs author confirmation / not required / do not use |  |
| Ethics approval |  |  | confirmed / needs author confirmation / not required / do not use |  |
| Data authorization |  |  | confirmed / needs author confirmation / not required / do not use |  |
| Sensitive-location policy |  |  | confirmed / needs author confirmation / not required / do not use |  |
| Conflict of interest |  |  | confirmed / needs author confirmation / not required / do not use |  |
| Author contributions |  |  | confirmed / needs author confirmation / not required / do not use |  |
| Data availability |  |  | confirmed / needs author confirmation / restricted / do not use |  |
| Code availability |  |  | confirmed / needs author confirmation / restricted / do not use |  |
| Repository / access route |  |  | confirmed / needs author confirmation / restricted / not required |  |
| Figure/table source data |  |  | confirmed / needs author confirmation / restricted / missing |  |
| AI-use statement |  |  | confirmed / journal dependent / not required |  |
```

## Passing Standard

For internal drafts, missing metadata may remain as author tasks.

For journal-format manuscripts, required metadata must be present or clearly marked as author-confirmation needed.

For submission-ready packages, required metadata must be confirmed.
