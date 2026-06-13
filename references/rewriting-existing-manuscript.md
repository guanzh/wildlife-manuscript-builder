# Rewriting Existing Manuscripts

Full adaptation of the 31-step pipeline for rewriting an existing ecology manuscript rather than building from scratch. Use when the user provides a draft (DOCX, Rmd, LaTeX) plus data/analysis code and says the current version "isn't good enough" or asks you to "rewrite" or "improve".

## Context Switch: From Builder to Auditor

The default pipeline assumes you are the builder: you choose the direction, run the analyses, and draft de novo. When rewriting, you are an auditor and editor: the direction is set, the analyses are done, and the prose exists. Your job is to:

1. **Audit** the analysis quality against each gate
2. **Identify** gaps between what the analysis supports and what the prose claims
3. **Narrow** overclaims to match the evidence
4. **Rewrite** the prose to follow IMRAD quality gates

Do NOT re-run the pipeline from scratch. Do NOT propose new research directions unless the existing ones are fatally flawed.

## Phase-by-Phase Adaptation

### Phase A: Discovery (Steps 1–4) — 1 turn

| Step | Default | Rewrite Adaptation |
|------|---------|-------------------|
| 1: Inspect data | Ask user for files | User already provided everything; audit what's there |
| 2: audit_data_package.py | Run script | Run but ignore xlsx/PDF failures — extract column info from analysis code instead |
| 3: Journal target | Ask user | Build provisional contract; mark "待确认" for unknown fields |
| 4: Submission metadata | Ask user | Build skeleton from draft author list; mark everything else "待确认" |

Key insight: the audit script scores low (2/10) for xlsx packages because it only reads delimited files. Do not treat this as a real failure — extract the data dictionary and sampling design from the Rmd analysis code instead.

### Phase B: Data Readiness (Steps 5–9) — 1–2 turns

| Step | Default | Rewrite Adaptation |
|------|---------|-------------------|
| 5: Data contract | Build from raw data | Build from Rmd code: extract raw facts, derived variables, model outputs, and variable provenance from the analysis chunks |
| 6: Info-gap list | Full audit | Light pass — most gaps are "author-confirmation needed" (funding, ethics, etc.) |
| 7: Author knowledge | Classify existing materials | **Critical step.** Scan the entire draft. Classify every factual paragraph as adopt/verify/narrow/exclude. This is the bridge between the old draft and the new evidence chain. |
| 8: Manuscript potential | Full rubric | Quick pass — the draft exists so it's at least medium potential. Note: "existing doesn't mean good" |
| 9: Deliverable pathway | Choose path | Default: journal-format manuscript (rewrite target). Downgrade only if Gate 3 shows fatal flaws. |

### Phase C: Direction (Steps 10–14) — 1 turn

Skip deep research (step 12) — the direction is chosen and the references exist. Focus on:

| Step | Adaptation |
|------|-----------|
| 10: Data type routing | Quick classification — already in the draft |
| 11: Question-method map | Extract from existing Introduction/Methods |
| 12: Deep research | **SKIP** — but note if reference count < 30 as a delivery-readiness blocking issue |
| 13: Answerable-unanswered | Quick check — does the Introduction state a specific gap? If not, this is a rewrite target |
| 14: Terminology contract | **Critical.** Build from the draft's terminology but standardize. This contract will enforce consistency in the rewrite. |

### Phase D: Analysis & Evidence (Steps 15–19) — 2–3 turns

**This is the anchor phase for rewrites.**

| Step | Adaptation |
|------|-----------|
| 15: Claim boundaries | Scan draft for known overclaim patterns (causal language, qualitative labels, management imperatives) |
| 16: Statistical delivery gate | **THE critical deliverable.** Read the analysis code line by line. For each model: check distribution family, random effect structure, diagnostics run, sensitivity checks, and whether the prose claims match the statistical output. Output the gate report even if it's a clean pass. |
| 17: Method completeness | Only if acoustic/automated-recognition |
| 18: Result cards | Build from the statistical gate report + existing Results section |
| 19: Literature matrix | Light pass — classify existing references by function. Note gaps. |

#### ⚠️ Before auditing: check if data has actually changed

The rule "audit, don't re-run" assumes the data is unchanged. **Before auditing, verify this assumption:**

1. **Find the actual data path**: Read the analysis code to find the hardcoded `DATA_DIR`. The data may have moved after workspace reorganization (e.g., `goal-driven-research-system` moves files to `sources/`).
2. **Check if the data directory still exists at that path**: If not, search for the data files elsewhere (typically `sources/` or `inbox/`).
3. **Compute checksums on the current data files and compare to the registry**: If checksums differ, the data HAS changed — you must re-run the analysis, not just audit it. If identical, audit only.
4. **If re-running is needed**: Fix the data path in the analysis code, re-run, then systematically compare old-vs-new results (TP/FN/FP/TN, recall, precision, etc.) to understand the direction and magnitude of change. A doubling of FP (e.g., 27→54) fundamentally changes the manuscript's conclusions and must drive claim narrowing.

**Pitfall — Excel header rows in Chinese research data**: Machine-recognition or field-data Excel files often have a title/merged row (row 0) with actual column headers on row 1. Always inspect column names before reading: `pd.read_excel(path).head(3)` to check if headers are shifted. Use `header=1` when needed. Common symptom: column names like `'Unnamed: 1'` indicate the header row was not parsed correctly.

**Pitfall — Data path mismatch after workspace reorganization**: When `goal-driven-research-system` reorganizes a workspace, analysis code that hardcodes relative paths (e.g., `DATA_DIR = ROOT / "鸣叫记录表(1)(1)"`) will break. Search for the data files in `sources/`, `inbox/`, or the project root, then update `DATA_DIR` accordingly. Do not assume the old path still works.

#### Statistical Enhancements for Acoustic Validation Manuscripts

When re-running analysis on acoustic/automated-recognition validation data, add these enhancements before claiming submission-readiness:

1. **Wilson 95% confidence intervals** on all proportion metrics (recall, precision, specificity, accuracy). Implement manually if `scipy` is unavailable:
   ```python
   Z_95 = 1.959963984540054  # qnorm(0.975)
   def wilson_ci(num, den):
       if den == 0: return (float("nan"),)*3
       p = num/den; z2 = Z_95**2
       d = 1 + z2/den
       c = (p + z2/(2*den))/d
       m = Z_95*math.sqrt((p*(1-p)+z2/(4*den))/den)/d
       return (c, max(0.0, c-m), min(1.0, c+m))
   ```
2. **Matching threshold sensitivity**: Re-run event matching at tolerances [0, 5, 10, 15, 20, 30] minutes. Report TP variation — if it changes by ≤2 events, the matching rule is stable.
3. **Recorder-level Wilson CIs**: For recorders with <10 positive days, CI width will exceed 40pp — flag these as "small sample, interpret cautiously" rather than ranking them.
4. **Old-vs-new comparison table**: When data changes between draft versions, produce a side-by-side table showing what shifted (e.g., "FP: 38→78, day precision: 91.9%→85.2%"). This is the evidence for claim narrowing.

Full implementation patterns (Wilson CI, threshold sensitivity, recorder-level CIs, old-vs-new comparison, Excel reading quirks) are in `references/acoustic-validation-enhancements.md`.

#### Statistical Gate Audit Pattern (Step 16 detail)

When auditing without re-running code, check:

1. **Model specification**: family, link, random effects. Are they appropriate? (e.g., count data → Poisson/nbinom2, proportions → binomial)
2. **Sample size vs. model complexity**: random effects with <5 levels are borderline; <3 are suspect
3. **Diagnostics reported**: does the code produce residual plots, QQ plots, convergence status, overdispersion tests?
4. **Sensitivity analysis**: are binary classifications tested at alternative thresholds? Are there unexamined confounders?
5. **Prose-model alignment**: for every claim in Results/Discussion that uses a number or "significant", trace it back to a specific model output. Flag mismatches.

Common findings in existing drafts:
- **Missing diagnostics**: the code runs models but produces no diagnostic plots
- **Over-interpreted null results**: "no difference" claimed when p>0.1 with low power
- **Qualitative labels without tests**: "hard boundary" used as if it were a statistical result
- **Ghost analyses**: methods mention analyses never performed (e.g., "sampling sufficiency was assessed with iNEXT" when the code chunk is commented out)
- **Distribution mismatches**: methods say "Gamma GLMM" but code uses Gaussian

### Phase E: Drafting & Quality (Steps 20–28) — 3–4 turns

This is where the actual rewrite happens. Order matters.

| Step | Adaptation |
|------|-----------|
| 20: Introduction plan | Rewrite to meet Gate 7.5: specific gap, operational definitions, objective-to-method map. Remove process language. |
| 21: Claim ledger | **Critical.** Build before writing a single word of Discussion. Every claim in the old draft gets classified. The "Removed or Narrowed Claims" table is the rewrite compass. |
| 22: Draft order | Methods → Results → Discussion → Introduction → Abstract → Title |
| 23: Discussion quality gate | Apply Gate 8.2 patterns to the new Discussion |
| 24: Conclusion strength | Run check_conclusion_strength.py or manual audit |
| 25–28: Figures, data, revision | Quick pass — existing figures likely need only caption updates |

#### The Claim Narrowing Table

This is the single most valuable output of a rewrite. Template:

```markdown
| Original claim (初稿) | Problem | Rewritten as |
|---|---|---|
| "硬边界" / "软边界" | 定性判断未经统计检验 | "道路边界相似性最低且波动小，村庄边界变异极大" |
| "边界可渗透性越高，差距越小" | 相关性不显著 | "呈负相关趋势但未达统计显著" |
| "显著优于" (多处) | 未全部经统计检验 | 仅在GLMM显著处保留"显著" |
```

Patterns to catch:
- **Qualitative → quantitative**: replace labels with numbers from the result cards
- **Causal → associative**: "导致/造成/决定" → "与……存在差异/相关"
- **Unsigned null → explicit null**: "没有差异" → "未检测到显著差异(p=X.XX, n=Y)"
- **Imperative → hypothesis**: "应采取措施" → "可能有助于……但需进一步验证"
- **Ghost → deleted**: remove methods/results that were described but never run

### Phase F: Finalization (Steps 29–31) — 1–2 turns

Same as new build but with these adaptations:

| Step | Adaptation |
|------|-----------|
| 29: Reviewer simulation | Critical. The existing draft already has weaknesses — simulate what reviewers would attack. Convert serious objections into revision tasks. |
| 30: Citation check | Verify existing references (DOI/title match). Target 30+. If under, note as blocking issue but don't fabricate citations. |
| 31: Delivery readiness | Score honestly. Most rewrites land at Level 2 (reviewable) with blocking issues noted for Level 3/4. |

## Deliverable Shape

A rewrite produces the same documents as a new build (data contract, statistical gate, claim ledger, result cards, manuscript draft, reviewer objections, delivery score), but the emphasis differs:

| Document | New Build Emphasis | Rewrite Emphasis |
|----------|-------------------|-----------------|
| Data contract | Extracting from raw data | Extracting from analysis code |
| Statistical gate | Building the analysis | Auditing the analysis |
| Claim ledger | Planning claims | Narrowing existing claims |
| Result cards | Generating from outputs | Reconstructing from existing results |
| Manuscript | Writing fresh | Rewriting with quality gates |
| Reviewer objections | Anticipating from scratch | Attacking existing weaknesses |

## Common Rewrite Scenarios

### Scenario A: "Good analysis, weak writing"
The Rmd code is solid but the prose over-claims or is unstructured.
- Fast-pass Phase A–D (analysis is fine)
- Focus 90% of effort on Phase E: claim narrowing + quality-gate rewrite

### Scenario B: "Good writing, weak analysis"
The prose is clean but the statistics have issues (missing diagnostics, ghost analyses, distribution errors).
- Fast-pass Phase A–C
- Invest heavily in Phase D: audit every model, flag every mismatch
- Phase E: update Results to match actual statistical output, add limitations

### Scenario C: "Everything needs work"
The user says "不够好" with no specifics.
- Full pipeline, but skip deep research (Phase C step 12)
- Statistical gate (Phase D) + claim narrowing (Phase E) share the weight equally
- Output: Level 2 (reviewable) with clear P0/P1/P2 revision tasks

## Pitfall — Automated checkers on Chinese manuscripts

The bundled checker scripts (`check_acoustic_method_completeness.py`, `check_conclusion_strength.py`, `check_manuscript_language.py`, etc.) use regex patterns designed for English academic prose. On Chinese manuscripts they produce **false negatives** — they cannot parse Chinese numbers ("4 名"), Chinese phrases ("交叉核验"), model names embedded in Chinese paragraphs, or Chinese section headers. Common failures:

- `human_annotator_count`: will report "placeholder only" even when "4 名具有……经验的人员" is in the text
- `double_review`: will miss "经交叉核验后对分歧样本协商取得一致意见"
- `model_name_version`: may miss "CBSkyNet" if surrounded by Chinese characters without whitespace
- `model_architecture`: may miss "PCEN + PANN-CNN10 + CBAM + BiLSTM" if described inline

**Rule**: Run the automated checker, but **manually verify every "missing" item** against the actual manuscript text before reporting gaps to the user. If the text contains the information but the checker didn't detect it, mark it as "✅ present (checker limitation)" and do not report it as a real gap.
