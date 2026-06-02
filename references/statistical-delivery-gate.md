# Statistical Delivery Gate

Use this gate after the analysis plan and before final Results/Discussion. The goal is to decide whether the available analyses are strong enough for the intended article type and what caveats or additional analyses are required.

## Principle

Writing can be polished only after the statistical delivery level is known. A manuscript can be scientifically honest yet still not submission-ready if the statistical outputs are incomplete.

## Required Output Template

```md
# Statistical Delivery Gate

## Analysis Inventory

| Analysis | Response | Predictors | Sample / effort | Output available? | Submission status |
|---|---|---|---|---|---|
|  |  |  |  | yes / partial / no | ready / usable with caveat / needs analysis / not usable |

## Model Diagnostics

| Check | Result | Interpretation | Action |
|---|---|---|---|
| Effort handling |  | offset / covariate / sensitivity / unhandled |  |
| Overdispersion |  | ok / concern / not checked |  |
| Zero inflation |  | ok / concern / not checked |  |
| Detection probability |  | modeled / not modeled / not applicable |  |
| Spatial autocorrelation |  | modeled / checked / not checked |  |
| Convergence |  | ok / concern / not checked |  |
| Low-record species |  | retained / pooled / supplement / excluded |  |
| Sensitivity analysis |  | done / needed / not feasible |  |

## Claim Strength From Statistics

| Result | Statistical strength | Allowed wording | Not allowed |
|---|---|---|---|
|  | clear / directional / uncertain / descriptive |  |  |

## Required Tables/Figures

| Output | Required fields | Status |
|---|---|---|
| Model coefficient table | estimate, uncertainty, test/posterior support, sample size | ready / needs export |
| HMSC species table | species, covariate, mean, interval, posterior probability | ready / needs export |
| Diagnostic table | overdispersion, convergence, sensitivity | ready / needs export |
```

## Camera-Trap Specific Checks

- Are camera days used as an offset, covariate, stratification factor, or sensitivity check?
- Is RAI interpreted only as a record index?
- Is detection probability modeled? If not, all occurrence language must stay record-level.
- Are low-record species retained in model outputs but interpreted cautiously?
- Are high-zero disturbance metrics described as limited?
- Are independent-event rules documented?
- Are effort and sample size reported in every central figure/table?

## Automated-Recognition Validation Checks

For acoustic, camera-image, or other machine-recognition validation manuscripts:

- Are recall, precision, specificity, accuracy, and F1 reported with denominators?
- Are Wilson, exact binomial, bootstrap, or other justified 95% confidence intervals reported for central metrics?
- If event matching uses a time/space tolerance, is a sensitivity analysis reported for alternative thresholds?
- If machine confidence scores are available, is a precision-recall curve or threshold sensitivity table provided?
- Are site/recorder-level differences reported with sample sizes and small-sample caveats?
- Are human annotations described as a reference standard rather than absolute truth unless independent validation supports stronger language?
- If the analysis is restricted to a fixed sampling window, is outside-window inference explicitly ruled out or supported by additional evidence?

## Delivery Levels

- Ready: diagnostics and outputs are sufficient for the target article type.
- Usable with caveat: analysis can support a bounded manuscript but needs limitations.
- Needs analysis: central claim should not appear until a missing analysis is done.
- Not usable: remove or downgrade the result.

## Passing Standard

For journal-format manuscripts, every central result must be at least "usable with caveat" and have a table/figure-ready output.

For submission-ready packages, every central result must be "ready" or be explicitly justified by target-journal norms.
