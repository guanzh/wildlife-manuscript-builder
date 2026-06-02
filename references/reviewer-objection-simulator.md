# Reviewer-Objection Simulator

Use this gate after a complete draft exists and before final integrity review. The goal is to make likely peer-review objections visible while they can still be fixed, narrowed, or disclosed.

This is not a hostile review. It is a stress test of novelty, data design, inference strength, method fit, citation support, and manuscript positioning.

## Reviewer Lenses

Simulate at least five reviewer roles:

- Novelty reviewer: asks whether the manuscript answers a specific under-answered question rather than another local species list.
- Introduction reviewer: asks whether the research gap, core definitions, and objective-method links are explicit.
- Data-design reviewer: checks sampling design, effort, site independence, missingness, and whether the study scale matches the claims.
- Method reviewer: checks whether the selected analysis matches the response variable, uncertainty, detectability, and assumptions.
- Conservation reviewer: checks whether management implications follow from the evidence without causal overreach.
- Citation reviewer: checks nearest literature, method citations, regional context, and reference-list integrity.
- Sensitive-data reviewer: checks permits, ethics, confidential locations, threatened species, and data-sharing limits.

## Required Objection Table

```md
# Reviewer-Objection Simulation

## Manuscript Position Tested

- Article type:
- Target venue type:
- Best answerable unanswered question:
- One-sentence contribution:

## Objection Table

| Reviewer lens | Likely objection | Severity | Evidence behind objection | Required response | Manuscript action | Status |
|---|---|---|---|---|---|---|
| novelty / data design / method / conservation / citation / sensitive data |  | low / medium / high / fatal | data contract / result card / claim ledger / literature matrix / missing metadata | revise / narrow / add limitation / add citation / run analysis / downgrade / author verification |  | open / addressed / disclosed / blocks submission |

## High-Risk Claims To Rewrite

| Claim | Why reviewer may object | Safer wording |
|---|---|---|

## Missing Evidence Or Author Decisions

- 

## Downgrade Decision

- Keep research article:
- Downgrade to short communication / data note / monitoring report / methods note:
- Reason:
```

## Severity Rules

- Low: clarity, wording, or citation can fix it.
- Medium: limitation, additional explanation, or minor reanalysis is needed.
- High: the current claim is too strong or a key method/data issue must be fixed before submission.
- Fatal: the selected article type or central claim is not supported by the dataset.

## Required Responses

For each medium, high, or fatal objection, choose one:

- revise: change manuscript wording or structure.
- narrow: reduce claim strength in title, abstract, results, or discussion.
- add limitation: explicitly state what the data cannot show.
- add citation: add verified nearest literature or method support.
- run analysis: produce new results before keeping the claim.
- downgrade: change deliverable type.
- author verification: require permit, ethics, metadata, or project decision from the author.

## Common Objections By Data Type

Camera trap:

- Detection/non-detection not modeled, so occupancy or absence claims are too strong.
- RAI or photo rate is being interpreted as abundance or density.
- Independent-event rules are unclear or inconsistent.
- Human activity metrics are zero-inflated or confounded with camera placement.
- Spatial gradients are proxies rather than measured ecological distances.
- Effort differs across sites or seasons.
- Introduction does not define whether the edge gradient is boundary distance, inside/outside status, spatial ordering, ordination axis, or a composite proxy.
- Discussion describes HMSC or centroid results as distribution, habitat preference, refuge, or utilization space rather than record-level patterns.

Remote sensing:

- Land-cover product resolution does not match the ecological process claimed.
- Temporal mismatch between habitat data and biological observations.
- Classification accuracy is not reported.

Patrol/threat:

- Patrol effort biases apparent threat hotspots.
- Management-effectiveness claims lack counterfactual design.

## Final Rule

Do not treat reviewer-objection simulation as optional polish. If a high or fatal objection remains open, either fix it, downgrade the deliverable, or disclose it as a limitation before finalizing.
