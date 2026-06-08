# Pre-Submission Review Gates

Use this reference when a wildlife manuscript is being prepared for collaborator review, journal formatting, or submission. The goal is to make the skill behave like a pre-submission reviewer, not only a draft writer.

## 1. Missing-Information Handling

Do not scatter unresolved placeholders through the formal manuscript body when they can be separated into a review appendix.

Classify every missing item as one of:

- Submission metadata: authors, affiliations, correspondence, funding, conflicts, author contributions.
- Responsibility metadata: permits, ethics, data authorization, sensitive-location policy.
- Study context: study area, species status, protected-area background, climate, habitat, field logistics.
- Methods-critical: sampling design, effort, exclusion rules, annotator workflow, model identity, thresholds, diagnostics.
- Interpretation-critical: model outputs, uncertainty, sensitivity checks, figures/tables, reference verification.

Rules:

- Keep title-page and statement placeholders outside the scientific narrative whenever possible.
- Put missing items in a "Pre-submission information gap list" or cover memo.
- In the formal Methods, include only the minimum transparent caveat needed to avoid misleading readers.
- If a missing methods-critical item affects the central inference, label the manuscript as "method-validation draft" or "reviewable draft", not "journal-format" or "submission-ready".
- If the missing item is not needed to interpret current Results, do not interrupt the Results/Discussion with a placeholder.

## 2. Conclusion-Strength Gate

Strong terms must trace to direct evidence. If the evidence is indirect, narrow the wording.

| Strong wording | Requires direct evidence of | Safer wording when indirect |
|---|---|---|
| replace / substitute / 替代 | Direct comparison with the replaced method, same target, effort, detection process, and outcome | reduce reliance on, support part of the workflow, replace the field-sampling step only |
| prove / demonstrate / 证明 | Design able to rule out key alternatives | show, indicate, support, are consistent with |
| reliable / 可靠判断 | Accuracy with uncertainty, validated against an appropriate reference, and clear scope | identified most positive recorder-days under this design |
| standard protocol / 标准方案 | Repeated validation across seasons/sites or management adoption requirement | practical working protocol, candidate protocol, preliminary standard |
| optimal sampling window / 最优窗口 | Data outside the window or independent evidence covering the full daily cycle | effective within the sampled window, covered most recorded events in this dataset |
| management effectiveness / 保护成效 | Intervention design or before-after-control evidence | monitoring relevance, management support, prioritization information |

Required output:

- Strong claim.
- Direct supporting evidence.
- Missing direct evidence.
- Revised claim wording.
- Manuscript location.

## 3. Acoustic / Automated-Recognition Method Completeness

> 完整检查清单见 `references/domain/method-checks/acoustic.md`。
> 核心要求：human annotator count, double review, disagreement handling, annotation software, event definition, model name/version, model architecture, training data source, threshold, confidence output, post-processing, runtime environment, event matching rule, matching-threshold sensitivity, 95% CI。

Before calling a machine-recognition validation manuscript journal-format, load and complete the checklist in `references/domain/method-checks/acoustic.md`.
If model name/version, training data, threshold, or post-processing are missing, frame the draft as a black-box application validation or method-validation draft.

## 4. Statistical Enhancement Suggestions

Automatically suggest the smallest useful additions, not a complex model by default.

For classification/detection validation:

- Add Wilson or exact binomial 95% confidence intervals for recall, precision, specificity, accuracy, and F1 where appropriate.
- Report denominators next to each metric.
- Run event-matching sensitivity at 3, 5, 10, and 15 minutes when event-level TP/FN/FP depends on a tolerance.
- If machine confidence scores exist, add precision-recall curve, threshold sensitivity, or at least metrics across several thresholds.
- For recorder/site differences, report sample sizes and avoid ranking claims when positive days are few.
- Use bootstrap by recorder/site only when it matches the sampling hierarchy and sample size is adequate.
- If records are restricted to a fixed sampling window, do not infer all-day calling patterns.

## 5. Sampling-Window Logic

If the data were collected or filtered to a human-defined time window:

- The manuscript may claim patterns within that window.
- The manuscript may compare methods within that window.
- The manuscript may recommend the window as a candidate operational window if supported by local practice or literature.
- The manuscript may not claim the window is optimal, complete, or covers nearly all daily activity unless there are outside-window data or strong independent citations.

Required wording:

- "Within the sampled morning window..."
- "Under the fixed 06:30-09:30 design..."
- "This dataset cannot evaluate activity outside the sampled window."

## 6. DOCX Layout QA

Before delivering a Word manuscript as journal-format, inspect:

- No accidental table of contents.
- Title not duplicated by filename-derived title.
- Tables are not broken into unreadable fragments.
- Table columns fit page width or are moved to supplement.
- Figures are embedded, referenced in text, and followed by captions.
- Figure text is readable at manuscript size.
- Captions include sample size, units, uncertainty when relevant, and sensitive-location handling.
- Chinese quotes, hyphens, minus signs, and percent signs render normally.
- No "待补充", "TODO", "请补充", or raw internal comments remain in the main manuscript unless the deliverable is explicitly a marked review draft.
- Sensitive species maps are masked or generalized.

If layout QA fails, deliver the manuscript as an internal/reviewable draft, not journal-format.

## 7. Sensitive-Species Data Security

For threatened, traded, poached, or otherwise sensitive wildlife:

- Do not expose exact coordinates in the manuscript text.
- Use relative, blurred, gridded, or generalized coordinates in figures.
- Do not publish raw point files as supplements unless the author confirms permission and masking.
- Separate data availability by data type:
  - Raw audio/photo/video: usually restricted or available on reasonable request.
  - Event table: share only with site fields generalized or removed.
  - Point/site metadata: restricted or masked.
  - Analysis code: usually shareable after paths and coordinates are removed.
- Include a sensitive-location statement and permit/data-authorization confirmation.
- If exact coordinates appear in the draft or public package, block submission-ready status.

## 8. Required Pre-Submission Review Outputs

For a reviewable manuscript:

- Information gap list.
- Conclusion-strength audit.
- Method-completeness audit for the relevant data type.
- Statistical enhancement recommendation list.
- Sensitive-species security check when applicable.

For a journal-format manuscript:

- All methods-critical gaps resolved or explicitly narrowed.
- Central metrics include uncertainty or a clear reason for point estimates only.
- Strong claims revised to match direct evidence.
- DOCX/layout QA completed.
- Figure/table and sensitive-location checks completed.

For a submission-ready package:

- All metadata, ethics/permits, data policy, reference verification, and layout checks are confirmed.
- No unresolved author placeholders remain in the manuscript body.
