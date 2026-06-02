# Discussion and Conclusion Quality Gate

Use this gate after drafting Discussion and Conclusion, before reviewer-objection simulation. The goal is to make interpretation deeper while keeping claims inside the data boundary.

## Discussion Logic

Each major discussion subsection should follow this sequence:

```text
result -> key statistic / uncertainty -> comparison with literature -> cautious explanation -> boundary -> conservation or monitoring meaning
```

Do not write broad interpretation before reminding the reader of the actual statistical evidence.

## Length Budget

Use `section-length-quality-gate.md` to set the final budget. For a standard 6,000-9,000 word English empirical article, the Discussion normally works best at 1,400-2,400 words and the Conclusion at 150-350 words. Treat Discussion below 1,000 words or above 2,800 words, and Conclusion below 100 words or above 500 words, as review signals rather than automatic failures.

The goal is not to make Discussion long. The goal is to give every central result enough space for comparison, cautious explanation, boundary-setting, and management or monitoring meaning.

## Required Result Back-Reference

Every major finding discussed must briefly return to:

- effect direction,
- effect size or estimate where available,
- confidence interval, credible interval, standard error, posterior probability, p value, or other uncertainty,
- sample size, camera days, sites, records, or model context when relevant.

If the interval crosses zero or uncertainty is high, discussion language must shift from "showed" to "suggested", "was consistent with", or "showed a directional but uncertain pattern".

## Human Activity Metrics

When discussing human RAI or human activity indices:

- Define what event types are included.
- Define what event types are excluded or separated, such as staff, patrol, livestock, dogs, vehicles, unknown people, or community residents.
- State the zero structure and sample-size limitation when many sites have zero records.
- Interpret non-significance as "no clear statistical association detected under the current sample structure and metric definition", not "no effect".

## HMSC and Species-Level Responses

For HMSC, occupancy, or detection/non-detection models, match language to the response variable.

Use:

- "recorded occurrence",
- "site-level recording tendency",
- "camera-recorded presence",
- "records were more concentrated at...".

Avoid unless directly supported:

- "true distribution",
- "habitat preference",
- "population decline",
- "avoidance",
- "abundance response",
- "management effectiveness".

If species credible intervals differ in strength, separate them:

- stronger negative response,
- negative tendency,
- uncertain response.

## Ordination, Centroid, and Two-Dimensional Gradient Language

If using PCA, NMDS, coordinate space, species centroid, or weighted centroid:

- Define the axes before interpretation.
- State that centroids describe record locations in the chosen gradient space.
- Avoid "core habitat", "refuge", "long-term use area", or "home range" unless independent evidence supports those meanings.
- Prefer "low human RAI record concentration area" or "inner-side low human-record region" when the evidence is record-level only.

## Management Implications

Management implications should be specific and monitoring-oriented unless causal evidence is strong.

Good forms:

- "include edge and community-forest sites in continued monitoring",
- "increase sampling in high-disturbance and outer-edge locations",
- "separately record roads, understory cultivation, dogs, livestock, and human passage",
- "track connectivity and new clearing".

Avoid broad prescriptions unless supported:

- "this proves the protected area is effective",
- "human activity causes species decline",
- "the area is a refuge",
- "management should prohibit X" without policy and causal evidence.

## Limitations

Separate statistical/ecological limitations from compliance/open-data limitations.

Statistical/ecological limitations:

- site number,
- camera-day imbalance,
- detection probability,
- zero-inflated disturbance variables,
- coarse disturbance categories,
- proxy spatial gradients,
- lack of seasonal replication,
- uncertainty in taxonomic identification.

Compliance/open-data limitations:

- permits,
- ethics,
- data authorization,
- sensitive-location masking,
- protected species coordinate sharing,
- data and code availability.

## Length-Based Revision Signals

If the Discussion is under the review zone, inspect whether central results are missing:

- effect direction plus estimate or uncertainty,
- comparison with nearest literature,
- plausible but cautious explanation,
- explicit inferential boundary,
- conservation or monitoring implication.

If the Discussion is over the review zone, remove or condense:

- background already covered in Introduction,
- mechanism speculation not supported by result cards or literature,
- repeated explanation of the same weak result,
- management prescriptions stronger than the evidence,
- limitations repeated without changing claim boundaries,
- conclusion material duplicated before the Conclusion.

## Conclusion Standard

The conclusion should be shorter than the Discussion and should not introduce new citations, new results, or new interpretations.

Use three compact paragraphs when appropriate:

1. Dataset and main community-level result.
2. Species-level heterogeneity and monitoring/management implication.
3. Claim boundary and future work.

Conclusion must include:

- core sample size/effort,
- main finding with cautious interpretation,
- human-activity metric conclusion if central,
- strongest defensible management relevance,
- explicit boundary: record-level association, not density, population trend, or causal mechanism.

## Process-Language Ban

Remove internal workflow phrases from formal manuscript text:

- "data package",
- "pure data package reconstruction",
- "from scratch reconstruction",
- "current package",
- "skill",
- "this workflow",
- "evidence chain reconstruction",
- "based on the available files" unless used in a limitation note outside the manuscript.

Use formal replacements:

- "based on camera-trap monitoring data",
- "based on the available camera-trap records",
- "this study analyzed",
- "the monitoring dataset included".

## Passing Standard

Discussion and Conclusion pass only if:

- each key interpretation traces to a result card and claim-ledger row,
- effect size or uncertainty is mentioned for central results,
- section length is justified by the result structure, article type, and journal contract,
- HMSC and centroid language remains record-level,
- non-significant human RAI is interpreted cautiously,
- process-language phrases are removed,
- conclusion is concise and does not exceed the Discussion's evidence strength.
