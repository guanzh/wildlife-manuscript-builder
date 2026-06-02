# Introduction Quality Gate

Use this gate before finalizing the Introduction. It is designed for wildlife conservation manuscripts that use monitoring datasets and need a strong but honest research question.

## Core Principle

An Introduction should not be a list of related facts. It should narrow from field-level importance to a specific unanswered question that the current dataset can answer.

The required logic is:

```text
global / field context -> mechanism or conservation problem -> method and inference boundary -> regional knowledge -> specific gap -> variable definitions -> objectives matched to methods
```

## Length Budget

Use `section-length-quality-gate.md` to set the final budget. For a standard 6,000-9,000 word English empirical article, the Introduction normally works best at 700-1,200 words. Treat fewer than 550 words or more than 1,400 words as a review signal, not an automatic failure.

Length is acceptable only when the argument is complete. A short Introduction should be expanded only if a required function is missing. A long Introduction should be shortened if it contains generic background, repeated method justification, or literature that does not narrow the specific gap.

## Required Structure

### Paragraph 1: Field and Conservation Context

Include:

- Why the system matters for biodiversity or conservation.
- The broad problem: protected-area effectiveness, edge effects, disturbance, monitoring gap, or community response.
- A synthesis or official report citation plus at least one recent empirical or synthesis paper.

Avoid:

- Starting with the local dataset.
- Broad claims that are not connected to the final question.

### Paragraph 2: Method and Inference Boundary

Include:

- Why the method fits the landscape or taxon.
- What the method can measure.
- What it cannot measure without additional design.

For camera-trap studies, explicitly distinguish:

- camera records / detection events / independent records,
- record rate or RAI,
- site-scale occurrence or recording tendency,
- abundance, density, population change, and causal mechanisms.

Preferred wording:

- "describe", "evaluate", "assess", "estimate", "identify associations", "analyze record-level patterns".

Avoid unless the design supports it:

- "test" when it implies a strong causal or experimental design,
- "prove", "determine", "demonstrate", "drive", "cause".

### Paragraph 3: Regional Foundation and Specific Gap

Include:

- What has already been studied in the region or comparable systems.
- What those studies do not answer.
- Why the current dataset is suitable for the narrower question.

The gap must be specific by geography, system, scale, method, and management relevance.

Good gap pattern:

```text
Existing studies in [region/system] have addressed [known topics], but evidence remains limited on [specific response] along [defined gradient or condition] at [scale] using [method/data].
```

### Paragraph 4: Definitions and Objectives

Before listing objectives, define all core terms that carry the study:

- protected-area edge spatial gradient,
- human RAI or human activity index,
- site-scale diversity,
- occurrence / detection / record appearance,
- two-dimensional gradient or centroid space if used.

Then list objectives/questions that map one-to-one to analyses.

Example pattern:

```text
In this study, [gradient] refers to [operational definition from data contract]. Human RAI refers to [included event types] standardized by [effort]. Site-scale diversity refers to [richness and/or Shannon index] calculated from [record table]. We ask: (1) ..., corresponding to [analysis]; (2) ..., corresponding to [analysis].
```

## Required Checks

Before passing the Introduction, confirm:

- The research gap is explicit and not just "few studies exist".
- Core concepts and predictors are operationally defined.
- The final objectives match the actual response variables and methods.
- The section length is justified by function, target article type, and journal contract.
- Process language is absent, such as "data package", "from scratch reconstruction", "current dataset package", "skill", or "this analysis package".
- Cautious verbs are used for observational data.
- The final boundary sentence states what the study does not infer.
- At least 10-15 sources from the literature matrix are used in the Introduction for a standard article.

## Length-Based Revision Signals

If the Introduction is under the review zone, inspect for missing:

- conservation problem rather than only local data description,
- method/inference boundary,
- regional foundation or closest comparable studies,
- specific answerable gap,
- operational definitions,
- objective-to-method map.

If the Introduction is over the review zone, remove or move:

- broad biodiversity/threat background that does not lead to the question,
- mini-review material that belongs in Discussion,
- study-area detail that belongs in Methods,
- repeated camera-trap or monitoring justification,
- aims that appear only after excessive setup.

## Local-Wildlife Camera-Trap Reminder

For protected-area edge and camera-trap manuscripts, do not leave the reader guessing whether "edge gradient" means:

- distance to boundary,
- inside/outside status,
- spatial ordering along a coordinate axis,
- PCA/NMDS/ordination axis,
- management zone,
- human activity intensity,
- elevation or habitat structure.

Define the exact operational meaning and, if it is a proxy, call it a proxy.

## Passing Standard

The Introduction passes only if it can be summarized as:

```text
Although [closest literature has answered X], it has not yet answered [specific gap]. Our dataset can answer [bounded question] because it contains [data and methods], but conclusions are limited to [claim boundary].
```

If this sentence cannot be written cleanly, revise the Introduction before drafting Abstract or Title.
