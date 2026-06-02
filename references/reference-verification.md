# Reference Verification Gate

Use this gate after citation coverage and before final delivery. Citation coverage checks whether references are used; reference verification checks whether they are real and accurate.

## Principle

Do not confuse a matched citation with a verified reference. A reference can be cited in text and still have the wrong title, journal, year, DOI, author list, status, or URL.

## Required Output Template

```md
# Reference Verification

## Verification Table

| Citation key | Reference entry | Source checked | DOI / URL | Status | Action |
|---|---|---|---|---|---|
|  |  | publisher / Crossref / PubMed / official report / journal website / author manuscript / not checked |  | verified / partial / needs correction / remove |  |

## Special Cases

| Reference | Issue | Action |
|---|---|---|
| In press / 2026 / ahead of print |  | author confirmation / update citation / mark in press |
| Chinese journal reference |  | check title, volume, issue, pages, DOI if available |
| Official report |  | check issuing body, year, URL, access date |
| Software/package |  | check version, citation recommendation |
| Database |  | check access date and version |
```

## Minimum Checks

- Author-year in text matches reference list.
- Title is accurate.
- Journal/book/report name is accurate.
- Year, volume, issue, pages, article number, DOI, and URL are correct where available.
- Official lists and databases have access date or version.
- In press or future-year references are marked and require author confirmation.
- References from original manuscripts are not assumed correct; they must be checked or flagged.

## Passing Standard

For internal drafts, unverified references may remain if clearly marked.

For journal-format manuscripts, all central background, method, and discussion references must be verified or flagged as author-confirmation needed.

For submission-ready packages, all references must be verified and formatted for the target journal.
