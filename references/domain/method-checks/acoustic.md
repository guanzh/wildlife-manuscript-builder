# Acoustic / Automated-Recognition Method Completeness

For manuscripts validating machine recognition, check these items before calling the draft journal-format:

| Method item | Required detail | If missing |
|---|---|---|
| Human annotator count | Number and expertise of annotators | Add to information gap list; state human annotations are a reference standard with caveat |
| Double review | Whether independent double listening was done | Add limitation or require re-annotation |
| Disagreement handling | Consensus, adjudication, or exclusion rule | Do not overstate human reference quality |
| Annotation software | Software/version or listening platform | Add to Methods gap list |
| Event definition | What counts as one call event | Results not final until defined |
| Machine model name/version | Model identity and version | Treat as black-box application validation only |
| Model architecture | CNN, transformer, spectrogram classifier, etc. | Do not claim algorithmic contribution |
| Training data source | Region/species/date and sample composition | Add reviewer risk |
| Threshold setting | Probability/score threshold and selection basis | Metrics are not reproducible until provided |
| Confidence output | Score/probability field availability | If present, request PR curve or threshold sensitivity |
| Post-processing | Clip merging, event boundary, duplicate removal | Event-level results require caveat |
| Runtime environment | Software, package, hardware if relevant | Add reproducibility gap |
| Event matching rule | Same site/date plus overlap or tolerance | Must be in Methods |
| Matching sensitivity | Alternative thresholds such as 3, 5, 10, 15 min | Required if event-level conclusions are central |
| Uncertainty | 95% CI for recall, precision, specificity, accuracy | Required for journal-format validation paper |

## Statistical Enhancement Suggestions

- Add Wilson or exact binomial 95% CIs for recall, precision, specificity, accuracy, F1.
- Report denominators next to each metric.
- Run event-matching sensitivity at 3, 5, 10, 15 min.
- If confidence scores exist, add PR curve or threshold sensitivity.
- For recorder/site differences, report sample sizes and avoid ranking claims when positive days are few.
- Use bootstrap by recorder/site only when it matches the sampling hierarchy and sample size is adequate.
- If records are restricted to a fixed sampling window, do not infer all-day calling patterns.
