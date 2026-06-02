# Answerable Unanswered Question Check

Use this gate after data readiness, manuscript potential grading, and initial direction selection, but before drafting a research article. The goal is to prevent "literature-decorated" manuscripts that do not actually answer a meaningful gap.

Deep research must answer one central question:

> Is there a question that published literature has not sufficiently answered, and that the current dataset can answer within honest claim boundaries?

If the answer is no, downgrade the deliverable to a monitoring baseline, species inventory, local conservation report, data note, methods/workflow note, or revision task list.

## Required Deep Research Search

For each candidate direction, search for:

- Nearest-neighbor studies: same taxon group, method, region, habitat, disturbance type, or management context.
- Broader benchmark studies: global or regional syntheses that may already answer the broad claim.
- Method-standard papers: what the field expects for occupancy, abundance, activity, density, community response, or management-effectiveness claims.
- Target venue examples: what article type and claim strength similar datasets have supported.

Do not treat "few studies exist" as a sufficient gap. The gap must be specific.

## Four-Part Test

### 1. Published Answer Check

Ask what has already been answered.

Output:

- Broad question:
- Closest papers:
- What they already answered:
- What would be repetitive:
- What remains unresolved:

If the current project only repeats a well-established broad conclusion, narrow the question or downgrade.

### 2. Gap Specificity Check

Convert the remaining gap into a precise form. Good gaps are specific by:

- Geography: underrepresented protected area, landscape, mountain range, corridor, buffer zone, or community forest.
- System: taxon group, threatened-species landscape, agroforest matrix, edge system, or management regime.
- Scale: site, season, gradient, community, species, temporal activity, or detection process.
- Method: paired gradients, multi-species model, occupancy with detection, activity overlap, or decision-priority framework.
- Management decision: what action, monitoring improvement, or risk prioritization the result can inform.

Weak gap:

- "There are few studies on this topic."

Better gap:

- "Existing studies show protected areas can maintain mammal diversity, but fewer studies compare a protected-area edge spatial gradient with local camera-recorded human activity in this specific community-forest transition landscape."

## 3. Data Fit Check

Map the gap to the actual dataset.

Use the data contract as the source of truth. Do not treat a candidate question as answerable if its required response variable, predictor, effort term, model output, or metadata is unresolved in the data contract.

Output:

| Candidate question | Required evidence | Current data has | Current data lacks | Verdict |
|---|---|---|---|---|
|  |  |  |  | answerable / narrower only / not answerable |

Use conservative verdicts:

- Answerable: current data directly support the response, predictors, scale, and uncertainty.
- Narrower only: the broad question is too strong, but a descriptive or association claim is possible.
- Not answerable: the data lack essential design, effort, detectability, counterfactual, validation, or metadata.

## 4. Contribution Statement Check

Before drafting a research article, write one sentence:

> This study contributes [specific new evidence] by using [dataset/method] to answer [answerable gap] in [study system], while limiting inference to [claim boundary].

If this sentence cannot be written without vague novelty language, downgrade or redesign the question.

## Required Output Template

```md
# Answerable Unanswered Question Check

## Direction

## Published Answer Check

- Broad question:
- Closest studies:
- Already answered:
- Repetitive angle to avoid:
- Remaining unresolved part:

## Gap Specificity

- Geography:
- System:
- Scale:
- Method:
- Management decision:
- Specific gap statement:

## Data Fit

| Candidate question | Required evidence | Current data has | Current data lacks | Verdict |
|---|---|---|---|---|

## Best Answerable Question

## One-Sentence Contribution

## Downgrade Rule

- If no answerable unanswered question exists:
- Best downgraded deliverable:
- What new data/analysis would make a research article possible:
```

## Common Outcomes

High article potential:

- A specific literature gap exists.
- Current data have enough design strength and metadata.
- The result can go beyond local description without overclaiming.

Medium article potential:

- A specific gap exists, but the data answer only a narrower association or monitoring question.
- Write a short empirical article with explicit limitations.

Low article potential:

- The broad topic is already well answered, or the data cannot answer the remaining gap.
- Write a monitoring baseline, data note, local report, or methods note.

## Reviewer-Risk Prompts

Before finalizing the direction, ask:

- Would a reviewer say this is just another local species list?
- Would a reviewer say the key question has already been answered elsewhere?
- Would a reviewer say the data cannot support the claimed mechanism?
- Would a reviewer ask for occupancy/detection modeling, stronger effort control, or a counterfactual?
- Would a reviewer question whether the disturbance metric actually measures the claimed disturbance?

If yes, narrow the claim before drafting.
