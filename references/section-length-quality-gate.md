# Section Length Quality Gate

Use this gate after the journal target contract is drafted and again after the manuscript draft is assembled. It sets a soft length budget for Introduction, Discussion, and Conclusion without treating word count as a substitute for scientific quality.

## Core Principle

Length is a diagnostic, not a target to pad toward. If a section is too short, identify the missing writing function. If a section is too long, remove background repetition, unsupported interpretation, or material that belongs in Methods, Results, supplementary material, or limitations.

For wildlife conservation and biodiversity manuscripts, a standard empirical article often has a main-text body of about 6,000-9,000 English words, excluding references and usually excluding abstract. When the target journal has a stricter limit, the journal target contract overrides this gate.

For a standard Chinese ecology research article, target 12,000-16,000 Chinese characters in the main text. Unless the journal specifies otherwise, exclude the abstract, references, figure/table captions, and appendices from this count. A short communication, data note, or journal-specific format may use a shorter target only when that pathway is explicitly selected in the journal target contract.

## Standard Empirical Article Budget

For a 6,000-9,000 word English manuscript:

| Section | Functional target | Review zone | Typical proportion |
|---|---:|---:|---:|
| Introduction | 700-1,200 words | <550 or >1,400 words | 10-15% of main text |
| Discussion | 1,400-2,400 words | <1,000 or >2,800 words | 20-30% of main text |
| Conclusion | 150-350 words | <100 or >500 words | shorter than Discussion |

Use the functional target for drafting and the review zone for warnings. A section outside the review zone can still pass if the journal format, article type, or evidence structure justifies it.

## Standard Chinese Empirical Article Budget

For a 12,000-16,000-character Chinese manuscript:

| Section | Functional target | Review signal |
|---|---:|---:|
| Introduction | 1,500-2,500 Chinese characters | missing gap, definitions, or objective-to-method link |
| Discussion | 3,000-5,000 Chinese characters | missing result-linked interpretation or padded speculation |
| Conclusion | 500-800 Chinese characters | missing evidence boundary or repeated Discussion content |

Treat a standard Chinese manuscript below 12,000 characters as under target and one above 16,000 as over target unless the journal contract or selected article type justifies the deviation. Diagnose the missing or excessive writing function; never add generic background merely to reach the target.

## Other Deliverable Paths

| Deliverable path | Introduction target | Discussion target | Notes |
|---|---:|---:|---|
| Brief report or short communication | 300-650 words | 600-1,100 words | Keep literature selective and results-centered. |
| Monitoring baseline or data note | 350-750 words | 700-1,300 words | Emphasize design, data value, limitations, and reuse. |
| Strong extended article | 850-1,300 words | 1,800-2,700 words | Only for complex datasets with multiple defensible result streams. |

Weak or low-potential data should normally use shorter, clearer sections. Do not increase section length to simulate novelty or explanatory depth.

## Introduction Length Diagnostics

If the Introduction is too short, check whether it lacks:

- field-level conservation problem,
- method and inference boundary,
- regional or comparable-system foundation,
- specific answerable gap,
- operational definitions,
- objectives matched to analyses.

If the Introduction is too long, check for:

- generic biodiversity or threat background not used by the study question,
- a literature review that does not narrow the gap,
- repeated method justification better placed in Methods,
- regional description that belongs in Study Area,
- objectives that appear only after excessive setup.

For a standard article, a useful paragraph budget is four to five paragraphs:

1. Field and conservation context.
2. Method and inference boundary.
3. Regional foundation and specific gap.
4. Operational definitions and objectives.
5. Optional bridge paragraph only when the literature gap requires it.

## Discussion Length Diagnostics

If the Discussion is too short, check whether each central result has:

- effect direction and estimate or uncertainty,
- comparison with nearest literature,
- cautious ecological or monitoring interpretation,
- explicit boundary,
- conservation or monitoring meaning.

If the Discussion is too long, check for:

- broad background repeated from Introduction,
- mechanism speculation not supported by result cards or literature,
- multiple interpretations of the same weak result,
- management prescriptions stronger than the evidence,
- limitations repeated without changing the claim boundary,
- conclusion material duplicated in the final section.

For a standard article, a useful Discussion budget is:

- opening synthesis: 150-250 words,
- each central result paragraph or subsection: 250-450 words,
- management implications: 200-400 words,
- limitations: 250-500 words,
- future data or monitoring needs: 150-300 words.

## Soft-Threshold Decisions

Classify section length issues as:

- OK: length and proportion fit the article type and the section passes its functional gate.
- Review: length is outside the functional target but scientifically justified.
- Underdeveloped: section is short because one or more required writing functions are missing.
- Overextended: section is long because it repeats, speculates, or exceeds the data boundary.
- Journal override: target journal requires a different length.

## Required Output

```md
# Section Length Quality Gate

## Manuscript Body Budget

- Target article type:
- Target main-text length:
- Detected or estimated main-text length:
- Journal override:

## Section Lengths

| Section | Words / Chinese characters | Proportion | Soft status | Reason | Action |
|---|---:|---:|---|---|---|
| Introduction |  |  | ok / review / underdeveloped / overextended / journal override |  |  |
| Discussion |  |  | ok / review / underdeveloped / overextended / journal override |  |  |
| Conclusion |  |  | ok / review / underdeveloped / overextended / journal override |  |  |

## Revision Decision

- Expand because:
- Condense because:
- Keep as is because:
- Do not pad with:
```

## Passing Standard

The gate passes when section lengths fit the target article type or when any deviation has a functional explanation. A draft should not be expanded merely to reach a number, and a concise section should not be shortened if it is already complete and journal-compliant.
