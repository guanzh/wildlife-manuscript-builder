# Claim Boundaries

Use this file before drafting title, abstract, Results, and Discussion.

## Replace Overclaims

| Overclaim | Safer Alternative |
|---|---|
| Human disturbance caused biodiversity decline. | Biodiversity metrics were lower in sites with greater measured disturbance. |
| Camera-trap rate shows density. | Camera-trap rate provides a relative detection index under the sampling design. |
| Habitat suitability map shows the species distribution. | The model identifies areas predicted to be suitable or higher priority for verification. |
| The species was absent from undetected sites. | The species was not detected at those sites during the survey period. |
| Co-occurrence proves interaction. | Co-occurrence patterns suggest a hypothesis about interaction that requires further testing. |
| The conservation action was effective. | Observed changes are consistent with a positive management effect, subject to design limitations. |
| AI classification accuracy guarantees ecological reliability. | Classification uncertainty should be propagated or acknowledged in ecological inference. |
| Animal records prove forest integrity. | Animal community evidence contributes one dimension of habitat integrity assessment. |


## Domain-Specific Overclaim Patterns

按数据类型加载特化 overclaim 规则：

| 数据类型 | Overclaim 文件 |
|---------|---------------|
| Camera trap | `references/domain/overclaims/camera-trap.md` |
| Remote sensing / habitat | `references/domain/overclaims/remote-sensing.md` |

其他数据类型的 overclaim 文件在 `references/domain/overclaims/` 下持续扩展。

加载规则：根据 `data-type-routing.md` 中匹配的当前数据类型，加载对应的 overclaim 文件。

## Words That Require Evidence

Use these only when supported by design and analysis: cause, effect, mechanism, driver, recovery, degradation, collapse, restoration success, population increase, population decline, density, abundance, interaction, intactness, effectiveness.

## Result Section Rule

Results should say what was estimated or observed, with units, sample size or effort, uncertainty, and figure/table references. Save explanations, mechanisms, management implications, and comparisons for Discussion.

## Discussion Paragraph Rule

Build each main discussion paragraph in five moves:

1. Restate the specific result.
2. Compare with nearest-neighbor studies.
3. Offer the most plausible explanation.
4. State boundary or alternative explanation.
5. Explain research or management meaning.
