---
name: wildlife-manuscript-builder
description: Build reviewable, realistically scoped manuscript packages from ecology and biodiversity datasets. Covers 19+ data types (camera-trap, acoustic, transect, vegetation, mark-recapture, occupancy, eDNA, remote-sensing, and more — see data-type-routing.md). Use when assessing data readiness, selecting article directions, conducting deep research, drafting IMRAD sections, creating evidence-linked figures, running pre-submission QA, or assembling journal packages.
metadata:
  hermes:
    aliases: [ecology-manuscript-builder]
    tags: [ecology, biodiversity, manuscript, research-writing, conservation, data-analysis]
    related_skills: [goal-driven-research-system, academic-paper, deep-research]
---

# Ecology Manuscript Builder

## Operating Principle

Build a reviewable and deliverable manuscript draft package, not an automatic publication claim. Always start with data readiness, manuscript potential grading, permissions, sensitive-location handling, and question-method fit before drafting prose.

Final prose can be polished, but the primary deliverable is the evidence chain: readiness report, journal target contract, section length quality gate, submission metadata contract, data contract, author-knowledge integration, information-gap list, research question map, answerable-unanswered-question check, argument and terminology contract, analysis plan, statistical delivery gate, result cards, figure/table assembly, deep literature matrix, introduction quality gate, claim ledger, discussion/conclusion quality gate, conclusion-strength audit, method-completeness audit, statistical enhancement list, data-availability/source-data gate, sensitive-data security check, layout QA, reviewer-objection simulation, citation coverage check, reference verification, manuscript draft, delivery readiness score, integrity checklist, AI-use statement, and revision tasks.

Do not try to force weak data into a high-quality paper. Match the manuscript ambition to the actual carrying capacity of the data, topic novelty, methods, and literature position.

## When Rewriting an Existing Manuscript

When the user provides a complete or partial draft (IMRAD, DOCX, Rmd + data) and asks for a rewrite rather than a from-scratch build, adapt the pipeline:

**Phase A–C: Fast-pass the contracts, but NEVER skip deep research.** Data, direction, and research questions may already be decided, but the literature must still be verified and expanded. Build data contract, author-knowledge integration, and terminology ledger quickly (1-2 turns per phase). However, deep research (Phase C Step 12) is MANDATORY even for rewrites — it serves two purposes: (a) verify the existing reference list is real and sufficient (≥30 verified sources), and (b) find 5-10 additional papers that strengthen the Discussion's literature comparisons. The user expects a rewrite to be BETTER than the original — richer literature integration is how you deliver that. Skipping deep research produces an underweight manuscript (~5,000 chars) that reads like a light edit rather than a thorough rewrite. Target output: 8,000-12,000+ Chinese characters for a standard ecology research article, with at least 40-50 verified references and every Discussion subsection citing 3-5 papers.

**Phase D: Statistical delivery gate is the anchor.** This is where rewrites diverge most from new builds. You are reviewing an analysis someone else (or a prior version) already ran, not running it yourself. Read the analysis code (Rmd, .R, .py) and audit it against `references/statistical-delivery-gate.md` without re-executing. Identify: missing diagnostics (residual plots, convergence reports, overdispersion checks), unexamined assumptions (sensitivity of binary classifications, spatial autocorrelation), under-powered tests, and results that don't match the prose claims. Output the delivery gate report as the central quality document. Do NOT re-implement the analysis unless Gate 3 forces a REFINE.

**Phase E: Claim narrowing is the core rewrite activity.** The most common failure mode in existing drafts is overclaiming. Build the claim ledger (`references/claim-ledger.md`) by scanning the Discussion/Conclusion for every strong claim, then trace each one back to the statistical delivery gate and result cards. The "Removed or Narrowed Claims" table in the ledger is the single most important rewrite deliverable. Common narrowing patterns:
- Qualitative labels → descriptive comparisons: "硬边界/软边界" → "道路边界相似性最低且波动小(bc=0.32, range 0.22–0.44)，村庄边界变异极大(bc=0.03–0.61)"
- Causal → associative: "导致/造成/决定" → "与……相关/……存在差异"
- Non-significant → explicit null: "呈连续梯度" → "未检测到位次与群落指标的显著关联(all p>0.1)"
- Management implication without evidence → hypothesis: "应扩大缓冲带" → "可能有助于……但需大样本验证"

Then draft in IMRAD order (Methods → Results → Discussion → Introduction → Abstract → Title), running Introduction quality gate (Gate 7.5) and Discussion quality gate (Gate 8.2) against the new prose. Keep the earlier quality documents (data contract, statistical gate, claim ledger) as the evidence chain — the prose is the polished surface, not the primary deliverable.

**Phase F: Same as new build.** Reviewer simulation, citation coverage, delivery readiness score. The main difference: the deep literature matrix step is skipped (or done lightly) since the existing draft already has a reference list. Focus on verifying existing citations rather than finding new ones, unless the reviewer simulation reveals a critical gap.

**Pitfall:** Do not treat the existing draft as ground truth. The author-knowledge integration step (Gate 1.7) classifies every claim as adopt/verify/narrow/exclude — do not skip this just because the draft "looks complete." The statistical delivery gate often reveals that the draft's prose claims are stronger than what the analysis actually supports.

**Pitfall — Chinese manuscript length:** The `check_section_lengths.py` script and `section-length-quality-gate.md` reference are calibrated for English manuscripts (6,000-9,000 word budgets). They cannot detect Chinese section headers (引言/讨论/结论) and will report "section not detected." For Chinese ecology research articles, target 8,000-12,000+ Chinese characters (汉字) for the main text, with Introduction ~1,500-2,500 chars, Discussion ~3,000-5,000 chars, Conclusion ~500-800 chars. A 5,000-char Chinese manuscript is too short — it signals shallow literature integration and insufficient discussion depth.

**Pitfall — Automated checker false negatives on Chinese:** The quality gate scripts (`check_acoustic_method_completeness.py`, `check_conclusion_strength.py`, etc.) use English-targeted regex that cannot parse Chinese numbers, phrases, or inline model names. Always manually verify checker-reported gaps against the manuscript text before reporting them as real issues. See `references/rewriting-existing-manuscript.md` for details.

**Pitfall — Reference list must stay synchronized with inline citations during deep research integration:** When you add inline citations to Discussion/Introduction from deep research (Phase C Step 12), you MUST simultaneously add those references to the reference list section. Do NOT add citations to body paragraphs first and plan to "add them to the reference list later." The reference list count should always match the inline citation count. After every round of Discussion paragraph enrichment, re-count the references and verify every cited paper appears in the reference list. The most common failure mode: Crossref/Elicit search → integrate 10 new citations into body text → forget to append them to the reference list → user asks "why are there only 27 references when you said 42?" → embarrassing fix session.

**Pitfall — Elicit API integration:** When `web_search` is unavailable, prefer the Elicit API (`https://elicit.com/api/v1/search` — NOT `api.elicit.com`) over Crossref for ecology deep research because Elicit returns far more targeted results. API key: read from `ELICIT_API_KEY` in the Hermes `.env` file. The API requires a browser-like `User-Agent` header to bypass Cloudflare protection. In Python's `urllib`, you must also remove `http_proxy`/`https_proxy` env vars before making the call (some proxies trigger 403 Cloudflare blocks). Full integration recipe in `references/literature-search-fallback.md`. When `web_search` is unavailable and `browser_navigate` hits CAPTCHAs on Google Scholar, use the Crossref REST API via terminal curl. It has generous rate limits without authentication for most queries:
```
curl -s "https://api.crossref.org/works?query=KEYWORDS&rows=10&filter=type:journal-article" | python -c "import sys,json; ..."
```
Pipe through `python -c` with `json.load(sys.stdin)` to extract title, year, DOI, journal, and authors. Semantic Scholar API works too but hits 429 rate limits faster. Crossref returns up-to-date metadata including DOIs. Also try the Hainan gibbon canopy bridge paper (Chan et al. 2020, DOI:10.1038/s41598-020-72641-z) and Gregory et al. 2017 (DOI:10.1038/s41598-017-04112-x) as canonical references for gibbon canopy connectivity.

For the full rewriting workflow, see `references/rewriting-existing-manuscript.md`.

## Executable Multi-Agent Workflow

WMB now supports an executable workflow via the `wmb` CLI, which integrates with both Codex and Hermes for durable task dispatch.

The canonical project state lives in `.wmb/`. Author confirmation is required for major scientific changes. The default placeholder author is `Dr. Who` and the default target journal is 《生物多样性》.

For the full executable workflow documentation, see `references/multi-agent-workflow.md`. Commands:

```bash
# Initialize a project
wmb init PROJECT

# Check status
wmb status PROJECT

# Create a task
wmb task create PROJECT --capability CAPABILITY --objective OBJECTIVE

# Dispatch (dry-run by default; add --execute to run)
wmb dispatch PROJECT TASK_ID --platform hermes|codex

# Resume after interruption
wmb resume PROJECT

# Verify submission package
wmb verify PROJECT
```

## Pipeline: 31 Steps / 6 Phases

> **Decision loop:** Key gates include PIVOT/REFINE/DOWNGRADE decisions (see `references/decision-loop.md`).
> **Watchdog:** Quality sentinel runs throughout — see `references/sentinel-watchdog.md`.
> **Debate:** Multi-perspective debate available at direction selection and peer review — see `references/multi-perspective-debate.md`.

**Phase A: Discovery & Permission（步骤 1-4）**
*Goal: Confirm what data exists, what's missing, and where the manuscript is headed — before any analysis.*

1. Inspect the user's data package and request any missing essential files only when they cannot be inferred from local context.
2. If a package directory is available, run `scripts/audit_data_package.py <package_dir>` to produce a first-pass readiness report.
3. Build a journal target contract with `references/journal-target-contract.md`. If no target journal is known, create a provisional contract. Manuscript/article DOCX outputs should not include a table of contents unless explicitly requested or required. Use `references/section-length-quality-gate.md` to set a soft Introduction, Discussion, and Conclusion budget for the article type.
4. Build a submission metadata contract with `references/submission-metadata-contract.md`; mark author list, affiliations, funding, permits, ethics, conflicts, data availability, and sensitive-location policy as confirmed or author-confirmation needed.

**Phase B: Data Readiness（步骤 5-9）**
*Goal: Freeze what the data actually contains — no drafting until facts are reconciled.*

5. Freeze a data contract with `references/data-contract.md`: raw facts, derived facts, variable provenance, count reconciliation, and manuscript-safe facts.
6. Build a pre-submission information-gap list with `references/pre-submission-review-gates.md`; keep missing metadata and author tasks out of the formal manuscript body whenever possible.
7. If the user provides an existing manuscript, notes, appendices, protocol, or review comments, run `references/author-knowledge-integration.md` to adopt factual material, verify uncertain items, narrow overclaims, and exclude unsupported content.

> **🔴 CHECKPOINT · 🛑 STOP — Gate 1: Data Contract Freeze** — If counts, variable definitions, or model outputs conflict and cannot be reconciled, BLOCK. Output a data-contract issue list and the smallest defensible deliverable. Do not draft a standard manuscript.

8. Grade manuscript potential with `references/manuscript-potential-rubric.md`; optionally use `scripts/score_manuscript_potential.py`.
9. Choose a deliverable path from `references/deliverable-pathways.md`: low, medium, or high potential.

**Phase C: Direction & Deep Research（步骤 10-14）**
*Goal: Find a specific, answerable question — or downgrade before wasting effort.*

10. Identify the data type and load the relevant section of `references/data-type-routing.md`.
11. Map feasible research questions to methods using `references/question-method-map.md`.
12. Use deep research to evaluate the selected direction with `references/deep-literature-standard.md`: nearest literature, what has already been answered, what remains unanswered, target venues, method boundaries, and whether the dataset can add a defensible contribution. For a standard research article, target at least 30 verified sources before full drafting.
13. Run `references/answerable-unanswered-question.md`.

> **🔴 CHECKPOINT · 🛑 STOP — Gate 2: Answerable Question** — **PROCEED** if a specific, under-answered question is identified and the data can answer it. **REFINE** if the gap exists but the method boundary is fuzzy — narrow the question scope and re-evaluate. **DOWNGRADE** if no answerable question exists — produce a monitoring baseline, data note, local report, or methods note instead.

14. Build an argument and terminology contract with `references/argument-terminology-contract.md`: one-sentence argument, reader promise, paragraph jobs, and canonical terms.

**Phase D: Analysis & Evidence（步骤 15-19）**
*Goal: Run analyses, build result cards, and lock the evidence chain before drafting prose.*

15. Check prohibited or over-strong claims using `references/claim-boundaries.md`.
16. Run `references/statistical-delivery-gate.md` to decide whether central analyses are ready, usable with caveat, need more analysis, or should be removed.
17. For acoustic/automated-recognition manuscripts, run the method-completeness gate in `references/pre-submission-review-gates.md` and optionally `scripts/check_acoustic_method_completeness.py` on the draft.

> **🔴 CHECKPOINT · 🛑 STOP — Gate 3: Statistical Delivery** — **PROCEED** if central results are "ready" or "usable with caveat". **REFINE** if results "need analysis" — run additional analysis before drafting. **BLOCK** if results are "not usable" — output a readiness report, do not draft Results.

18. Build result cards before drafting Results. Use `references/result-card-template.md` or `scripts/build_result_cards.py`.
19. Build a literature matrix and citation plan before drafting Introduction or Discussion; the matrix must assign sources to Introduction, Methods, Discussion, regional context, and software/data functions.

**Phase E: Drafting & Quality（步骤 20-28）**
*Goal: Write the manuscript, then stress-test every claim, section, and figure.*

20. Build an Introduction argument plan with `references/introduction-quality-gate.md`; define core variables, sharpen the specific gap, and map each research question to a method.
21. Build a claim ledger with `references/claim-ledger.md` before drafting Discussion; update it after the draft.
22. Draft in this order: Methods, Results, Discussion, Introduction, Abstract, Title. Avoid putting author-task placeholders into the main scientific narrative.
23. Run `references/discussion-conclusion-quality-gate.md` and re-run `references/section-length-quality-gate.md`.
24. Run conclusion-strength and statistical-enhancement checks with `references/pre-submission-review-gates.md`, `scripts/check_conclusion_strength.py`, and `scripts/check_statistical_enhancements.py`; narrow strong claims that lack direct support.

> **🔴 CHECKPOINT · 🛑 STOP — Gate 4: Conclusion Strength** — **PROCEED** if all strong claims have direct support. **REFINE** if claims need narrowing or caveats. **BLOCK** if strong unsupported claims remain — revise before reviewer simulation.

25. Run `references/figure-table-assembly.md` to ensure central figures/tables, captions, supplements, and sensitive-data handling are ready.
25.5. Run figure-claim trace with `references/figure-claim-trace.md`: for each central figure/table, extract the caption claim and verify it traces back to (a) the corresponding result card, (b) the statistical delivery gate verdict, and (c) the claim ledger. Flag any caption that is stronger than the statistical evidence, contradicts the result card, or is missing from the claim ledger.
26. Run `references/data-availability-source-data.md` to map datasets, figure source data, code, repositories/access routes, FAIR metadata, and sensitive-data restrictions.
27. For DOCX/journal-format outputs, run layout QA with `scripts/check_docx_layout_qa.py`; for sensitive species, run `scripts/check_sensitive_data_security.py`.
28. Run the improvement loop from `references/revision-loop.md`.

**Phase F: Finalization（步骤 29-31）**
*Goal: Simulate reviewers, verify citations, score delivery readiness — ship or loop back.*

29. Run reviewer-objection simulation with `references/reviewer-objection-simulator.md` and revise or disclose the resulting risks.
30. Run citation coverage with `references/citation-coverage-check.md` and optionally `scripts/check_citation_coverage.py --min-references 30`; run `references/reference-verification.md` for DOI/title/year/source checks; run claim-ledger coverage with `scripts/check_claim_ledger.py`; run process-language and overclaim checks with `scripts/check_manuscript_language.py`.
31. Finish with `references/delivery-readiness-score.md`, `references/journal-package-checklist.md`, optionally `scripts/check_delivery_readiness.py <package_dir>`, and an AI-use statement from `assets/ai-use-statement-template.md`.

> **🔴 CHECKPOINT · 🛑 STOP — Gate 5: Delivery Readiness** — Assign Level 1-4. Do not call a manuscript submission-ready unless all Level 4 requirements are confirmed. If serious reviewer objections remain unaddressed, loop back to Phase E.

## Minimum Input Contract

Require or reconstruct these items before writing a manuscript draft:

- Study object: species, taxon group, ecosystem, protected area, or landscape.
- Data files: raw data, cleaned data, model outputs, or summarized results.
- Data dictionary: column meanings, units, coding rules, and missing-value definitions.
- Sampling design: time span, spatial scope, sites/transects/devices, frequency, and survey effort.
- Processing notes: cleaning, exclusions, independent-event rules, taxonomic decisions, classification rules.
- Data contract status: which facts are observed, derived, modeled, assumed, or still unresolved.
- Research question: user-provided question or permission to propose candidate questions.
- One-sentence argument: the bounded claim, evidence, and boundary that the manuscript will serve.
- Manuscript target: research article, short communication, methods article, data paper, or management-facing article.
- Journal target: journal name or provisional venue type, article type, language, abstract style, reference style, figure/table rules, and whether a table of contents is required. Default for manuscript DOCX is no table of contents.
- Submission metadata: authors, affiliations, funding, permits, ethics, data authorization, conflicts, author contributions, data/code availability, and sensitive-location policy, all classified by confirmation status.
- Author materials: existing manuscript, protocol, notes, appendices, or review comments, classified as adopt / verify / narrow / exclude.
- Literature package: core papers, target journal, nearby studies, or permission to generate a literature search plan.
- Terminology ledger: canonical names for species, sites, gradients, metrics, models, and abbreviations.
- Responsibility material: permits, ethics, data authorization, sensitive-location handling, conflicts, and AI-use limits.

If the package lacks data dictionary and sampling design, do not draft Results. Output only a readiness report and revision tasks.

If counts, variable definitions, or model outputs conflict and cannot be reconciled in a data contract, do not draft a standard manuscript. Output a data-contract issue list and the smallest defensible deliverable.

If the user requests a standard research article but deep research yields too few verified relevant sources, too weak a research gap, or no method-boundary support, downgrade the article type or produce a literature-acquisition task list before writing a full draft.

## Data-Type Routing

Classify the package before choosing methods:

- Camera trap: detection/non-detection, activity, community response, disturbance, abundance only under defensible assumptions.
- Acoustic monitoring: call activity, detection probability, automated identification, temporal change.
- Transect or point survey: encounter rate, distance sampling, density, occupancy, trend.
- Occupancy/distribution: detection histories, habitat association, suitability, conservation gaps.
- Remote sensing/habitat: forest cover, fragmentation, connectivity, landscape change.
- Patrol/threat/management: threat hotspots, action prioritization, intervention evaluation.
- Multi-source: integrated observation models, state-space models, hierarchical synthesis.

When uncertain, choose the more conservative route and state what would be needed for stronger inference.

## Stage Gates

### Failure Mode Fallbacks

对于最高频的 3 个失败场景，以下是显式三段式恢复路径：

#### 场景 1：数据合同无法冻结（Gate 1 失败）

| 阶段 | 触发条件 | 动作 |
|------|---------|------|
| 🔍 一线修复 | counts 冲突、变量定义不一致 | 回查原始数据源 → 与用户确认计数规则 → 重建 data contract |
| 🔧 仍失败 | 修复后仍然无法调和 conflicts | 输出 data-contract issue list → 降级 deliverable 为 internal scientific draft 或 data note |
| 🆘 兜底 | 用户无法提供缺失元数据 | 标注 manuscript 为 "method-validation draft"，不提交为 research article |

#### 场景 2：找不到可回答的问题（Gate 2 失败）

| 阶段 | 触发条件 | 动作 |
|------|---------|------|
| 🔍 一线修复 | 研究空白存在但方法边界模糊 | 缩小问题范围 → 用更保守的方法框架 → 重新评估 answerable-unanswered-question |
| 🔧 仍失败 | 窄化后仍无法定义可回答的问题 | DOWNGRADE → 产出 monitoring baseline / data note / local report / methods note |
| 🆘 兜底 | 文献深度不足以支撑任何方向 | 输出 literature-acquisition task list → 暂停 drafting，等待用户补充文献 |

#### 场景 3：统计交付不通过（Gate 3 失败）

| 阶段 | 触发条件 | 动作 |
|------|---------|------|
| 🔍 一线修复 | 结果 "needs analysis"（模型诊断未通过/敏感性未检查） | 运行额外分析：诊断图、敏感性检查、备选模型 → 重新评估 |
| 🔧 仍失败 | 修复后效果仍"not usable" | 移除该结果为 central claim → 窄化 manuscript scope → 标注为 caveat |
| 🆘 兜底 | 所有 central results 均不可用 | BLOCK — 输出 readiness report + revision task list，不 draft Results |

### Gate Definitions

### Gate 0: Permission and Sensitivity

Check for exact coordinates of threatened species, unpublished project information, protected-area internal management data, student or collaborator information, and third-party data restrictions. Mask sensitive locations in public-facing outputs.

### Gate 1: Data Readiness

Check data dictionary, survey effort, temporal and spatial scope, missingness, duplicated records, taxonomy, coordinate reference system, and site independence. Stop if the data cannot support a manuscript draft.

### Gate 1.5: Data Contract Freeze

Before selecting a manuscript direction, freeze a data contract with `references/data-contract.md`.

Required output:

- Raw observed facts.
- Derived analysis facts.
- Variable provenance and units.
- Count reconciliation table.
- Model-output inventory.
- Manuscript-safe facts.
- Unresolved facts that cannot be used as claims.

Any number, variable, spatial gradient, event rule, or model result used in the manuscript must trace to the data contract, a result card, or a verified citation.

### Gate 1.6: Journal Target and Submission Metadata

Before drafting a deliverable manuscript, build:

- `references/journal-target-contract.md`: target venue, article type, language, abstract structure, word count, reference style, figure/table rules, required statements, and output files.
- `references/section-length-quality-gate.md`: soft Introduction, Discussion, and Conclusion length budget matched to article type, main-text target, and journal override.
- `references/submission-metadata-contract.md`: authorship, affiliations, funding, permits, ethics, conflicts, data/code availability, author contributions, and sensitive-location policy.

Default rule: do not add a table of contents to a manuscript/article DOCX unless requested or required by the journal target contract.

### Gate 1.7: Author-Knowledge Integration

If author-provided manuscripts, notes, protocols, appendices, or review comments exist, classify their content with `references/author-knowledge-integration.md`.

Adopt factual and useful local details, verify uncertain items, narrow over-strong claims, and exclude unsupported or confidential content. Data-only testing may ignore author materials, but deliverable manuscripts should reintegrate confirmed author knowledge.

### Gate 1.8: Missing Information Register

Before drafting formal prose, run the missing-information rules in `references/pre-submission-review-gates.md`.

Required output:

- Information gap list, grouped as submission metadata, responsibility metadata, study context, methods-critical, and interpretation-critical.
- Decision for each gap: keep out of main text / mention as transparent caveat / block journal-format status.
- Draft status label: internal draft, method-validation draft, reviewable manuscript, or journal-format manuscript.

Do not fill the manuscript body with "待补充", "TODO", or author-instruction brackets unless the user explicitly asks for a marked review draft. If a methods-critical gap remains, state the limitation in Methods or Limitations and keep the detailed task in the gap list.

### Gate 2: Manuscript Potential Grade

Classify the project as low, medium, or high manuscript potential. Consider sampling design, sample size/effort, data completeness, method fit, novelty, literature gap, management relevance, reproducibility, and ethical/permission completeness.

Low potential can still produce a deliverable article, but the path should be a descriptive note, monitoring baseline, methods note, local conservation report, data paper, or modest short communication. Medium potential can support a standard empirical draft with careful limitations. High potential can support a stronger journal article only if the analysis and contribution hold up after deep research.

### Gate 3: Direction Selection and Deep Research

Generate feasible writing directions from the data potential grade. For each direction, assess novelty, closest studies, required analyses, target venue type, likely reviewer objections, and whether the current data can answer the question. Select the most deliverable direction, not the most ambitious-sounding direction.

Deep research is not only citation gathering. It must decide what the literature has already answered and whether the current dataset can answer a narrower, still-unanswered question. Use `references/answerable-unanswered-question.md`.

For a standard empirical research article, deep research should normally identify at least 30 verified sources and organize them with `references/deep-literature-standard.md`. Fewer sources require an explicit reason and usually a narrower deliverable path.

### Gate 3.5: Answerable Unanswered Question Check

Before selecting a research-article path, identify whether there is a question that is:

1. Not already sufficiently answered by published literature.
2. Specific enough to be more than "few studies exist".
3. Answerable by the current dataset without overclaiming.
4. Able to produce a one-sentence contribution statement.

Required output:

- Already answered by literature.
- Remaining specific gap.
- Candidate unanswered questions.
- Current data can answer.
- Current data cannot answer.
- Best answerable unanswered question.
- One-sentence contribution.
- Downgrade decision if no such question exists.

If this check fails, do not draft a standard research article. Produce a monitoring baseline, data note, local conservation report, method/workflow note, or revision task list.

### Gate 4: Question-Method Fit

Convert the question into object, response variable, predictors, scale, temporal scope, method family, and claim boundary. If the data support only description, do not frame the manuscript as causal or mechanistic.

### Gate 4.5: Argument and Terminology Contract

Run `references/argument-terminology-contract.md` before full prose drafting.

Required output:

- One-sentence argument: system/problem, bounded advance, data/method, evidence, and claim boundary.
- Reader promise check: relevance, contribution, trust, reuse, and boundary.
- Paragraph job map for Introduction, Discussion, and Conclusion when drafting or revising those sections.
- Terminology ledger for species, study areas, gradients, metrics, model terms, units, abbreviations, and management terms.

If the one-sentence argument cannot be written without inventing evidence, do not draft a standard research article. Downgrade, revise the question, or add analysis/literature tasks.

### Gate 5: Analysis Plan

Recommend or audit methods, assumptions, alternative methods, required figures/tables, and claims that must not be made. Ask for human confirmation before treating analyses as final.

### Gate 5.5: Statistical Delivery

Run `references/statistical-delivery-gate.md` before final Results and Discussion.

Required output:

- Analysis inventory.
- Model diagnostics and missing checks.
- Claim strength from statistics.
- Required tables/figures and export status.
- Decision for each result: ready, usable with caveat, needs analysis, or not usable.

Central results that are "needs analysis" or "not usable" must not be used as central claims in a journal-format manuscript.

For classification or automated-recognition validation papers, central performance metrics should include denominators and uncertainty, normally Wilson or exact binomial 95% confidence intervals. If only point estimates are available, add a statistical enhancement task and do not call the paper submission-ready.

### Gate 5.6: Automated-Recognition Method Completeness

For acoustic or image-recognition validation manuscripts, run `references/pre-submission-review-gates.md` and optionally `scripts/check_acoustic_method_completeness.py`.

Required fields include human annotator count, double-review status, disagreement handling, annotation software, event definition, model name/version, model architecture, training data source, threshold, confidence output, post-processing, runtime environment, event matching rule, matching-threshold sensitivity, and 95% confidence intervals.

If model name/version, training data, threshold, or post-processing are missing, frame the draft as a black-box application validation or method-validation draft. Do not claim algorithmic novelty or reproducible model performance until these are supplied.

### Gate 6: Result Cards

Every major result needs a result card with: one-sentence result, figure/table, statistical evidence, sample size or effort, uncertainty, supported claim, unsupported claim, and discussion entry point.

### Gate 6.5: Claim Ledger

Before drafting Discussion, build a claim ledger with `references/claim-ledger.md`.

The ledger must classify each planned manuscript claim as observed fact, derived metric, model-supported result, literature-supported context, interpretation, management implication, or unsupported claim. Unsupported or over-strong claims must be removed, narrowed, or moved to limitations/future work.

### Gate 7: Literature Matrix

Separate papers by function: background anchor, nearest-neighbor problem, method decision, discussion comparison, regional/species context, policy/management source, and software/data citation. Do not include unverified references in the manuscript.

For a standard research article, the matrix should normally contain at least 30 verified sources. It must show what each source already answers, what gap remains, and where it will be used in the manuscript.

### Gate 7.5: Introduction Quality

Before finalizing the Introduction, run `references/introduction-quality-gate.md`.

Required output:

- Four-part introduction argument plan: field context, method/inference boundary, regional foundation/specific gap, definitions/objectives.
- Specific research gap that is not merely "few studies exist".
- Operational definitions for core terms such as protected-area edge spatial gradient, human RAI, site-scale diversity, occurrence/recording tendency, and two-dimensional gradient space.
- Objective-to-method map.
- Soft section-length status for the Introduction, normally 700-1,200 words for a standard 6,000-9,000 word English empirical article unless the journal target contract overrides it.
- List of Introduction citations, normally 10-15 sources for a standard article.

The Introduction must not contain internal workflow language such as "data package", "from scratch reconstruction", "skill", or "evidence-chain reconstruction".

### Gate 8: Manuscript Draft

Write Methods first, then Results, Discussion, Introduction, Abstract, and Title. Results report findings without interpretation. Discussion follows result-comparison-explanation-boundary-meaning.

For observational monitoring data, prefer "describe", "evaluate", "assess", "identify associations", and "record-level pattern". Avoid "test", "prove", "cause", "drive", or "determine" unless the design justifies those verbs.

### Gate 8.2: Discussion and Conclusion Quality

Run `references/discussion-conclusion-quality-gate.md` before reviewer-objection simulation.

Required output:

- Discussion map: each major result -> effect size/uncertainty -> literature comparison -> cautious interpretation -> boundary -> monitoring or conservation implication.
- Human RAI definition and zero-structure caveat.
- HMSC or occupancy language matched to the modeled response, such as recorded occurrence or site-level recording tendency.
- Centroid/ordination language limited to record locations in gradient space.
- Soft section-length status for the Discussion and Conclusion, normally 1,400-2,400 words for Discussion and 150-350 words for Conclusion in a standard 6,000-9,000 word English empirical article unless the journal target contract overrides it.
- Conclusion condensed to dataset, main findings, management relevance, claim boundary, and future data needs.
- Formal-language pass with no process-language traces.

### Gate 8.3: Conclusion-Strength and Sampling-Window Audit

Run `references/pre-submission-review-gates.md` and optionally `scripts/check_conclusion_strength.py`.

Required checks:

- "Replace/substitute/替代" requires direct comparison with the method being replaced. If the dataset only compares machine outputs to human annotations on recorder data, narrow to "reduce reliance on field listening", "support recorder-based screening", or "replace the field-sampling step only".
- "Reliable/可靠" requires scope, denominators, reference standard, and uncertainty.
- "Standard protocol/标准方案" requires repeated validation, management adoption, or wording as "candidate/working protocol".
- Fixed sampling windows support only within-window patterns unless outside-window data or strong independent literature are available.

Strong unsupported wording must be revised before reviewer-objection simulation.

### Gate 8.5: Reviewer-Objection Simulation

Before finalizing the draft, simulate likely reviewer objections with `references/reviewer-objection-simulator.md`. Convert serious objections into revision tasks, added limitations, stronger evidence links, or a downgraded deliverable path.

### Gate 8.7: Figure and Table Assembly

Before calling a manuscript journal-format or submission-ready, run `references/figure-table-assembly.md`.

Main figures/tables must be present, attached, or explicitly marked as blocked. Captions should include sample size, units, uncertainty, and sensitive-location handling where relevant.

For DOCX outputs, also run `scripts/check_docx_layout_qa.py` or manually verify title duplication, table breaks, caption placement, figure readability, Chinese punctuation, unresolved placeholders, image embedding, table of contents absence, and sensitive-map masking.

### Gate 8.72: Figure-Claim Trace

Before calling a manuscript journal-format or submission-ready, run `references/figure-claim-trace.md`.

Required output:

- One row per central figure/table: caption claim, source result card, statistical gate verdict, claim-ledger entry.
- Mismatch flags: caption stronger than statistics, caption contradicts result card, caption missing from claim ledger, figure data not in source-data map.
- Resolution: narrow caption, add caveat, remove figure, or document as accepted risk.

If a caption asserts a causal or management-implication claim that the statistical delivery gate marks as "needs analysis" or "not usable", the figure must not appear as a central claim figure in a journal-format or submission-ready manuscript.

### Gate 8.75: Data Availability and Source Data

Before calling a manuscript journal-format or submission-ready, run `references/data-availability-source-data.md`.

Required output:

- Dataset inventory for raw, cleaned, modeled, figure, table, supplementary, reused, third-party, and code files.
- Access route for each dataset: public repository, controlled access, supplement, reused public source, third-party restricted, justified request, sensitive restricted, or not applicable.
- Source-data mapping for central figures and tables.
- FAIR metadata check for shareable datasets.
- Draft data/code availability statement with sensitive-species restrictions and author-confirmation fields.

For sensitive ecological data (threatened species locations, patrol routes, archaeological sites, private land), public outputs should normally separate summary data and code from exact coordinates, raw media, and patrol-sensitive information.

### Gate 8.8: Sensitive-Species Security

For threatened, traded, poached, patrol-sensitive, or otherwise sensitive species, run the sensitive-species section of `references/pre-submission-review-gates.md` and optionally `scripts/check_sensitive_data_security.py`.

Block journal-format or submission-ready status if the public manuscript exposes exact coordinates, raw point metadata, patrol-sensitive locations, or unapproved data-sharing language. Separate raw media, event tables, point metadata, and analysis code in the data availability statement.

### Gate 9: Integrity Review and Revision Loop

Check figure-text consistency, section-length fit, statistical assumptions, claim boundaries, citation verification, citation coverage, ethics/permits, data/code availability, sensitive-location masking, conflicts, funding, and AI-use disclosure.

Then evaluate whether the draft has further realistic room for improvement. Provide author-decision tasks rather than silently rewriting everything. After the author chooses tasks, revise only within the data's support level.

### Gate 10: Delivery Readiness Score

Assign a final delivery level with `references/delivery-readiness-score.md`:

- Level 1: Internal scientific draft.
- Level 2: Reviewable manuscript.
- Level 3: Journal-format manuscript.
- Level 4: Submission-ready package.

Do not call a manuscript submission-ready unless all Level 4 requirements are confirmed.

## 反例与黑名单 (Anti-Patterns & Blacklist)

以下是本 skill 禁止的行为。按主题分组：

### 数据类（Data）

- Do not draft Results without result cards.
- Do not draft a standard manuscript when key data facts are unresolved in the data contract.
- Do not use a number, variable definition, model estimate, or spatial/detection claim that cannot be traced to the data contract, result cards, or verified citations.
- Do not invent sampling design, survey effort, coordinates, species names, permits, ethics approval, funding, or conflicts.
- Do not ignore author-provided factual material when the goal is a deliverable manuscript; classify it as adopt, verify, narrow, or exclude.
- Do not treat detection rate, photo rate, or encounter rate as density.
- Do not treat habitat suitability as confirmed presence.

### 推断类（Inference）

- Do not draft full prose before the one-sentence argument can state the bounded claim, evidence, and boundary.
- Do not infer causal management effectiveness from before-after data without a defensible design.
- Do not convert co-occurrence into species interaction without scale-aware evidence.
- Do not interpret non-significant human RAI as no ecological effect.
- Do not write HMSC, occupancy, or detection/non-detection results as true distribution, density, habitat preference, avoidance, or causal response unless the model and design support it.
- Do not claim a passive recorder or machine model "replaces" field listening, human monitoring, or traditional methods unless the data directly compare those methods at the same inferential target.
- Do not call a fixed sampling window optimal or complete unless outside-window data or strong independent citations support that claim.
- Do not call centroid or ordination clusters core habitat, refuge, long-term use space, or home range unless independently supported.
- Do not keep major manuscript claims outside the claim ledger.
- Do not continue deep drafting if the best deliverable is a monitoring note, report, or data paper; state that path plainly.
- Do not inflate a low-potential dataset into a high-claim manuscript.
- Do not hide low sample size, weak design, unbalanced effort, or outdated topic positioning behind polished language.
- When evidence is insufficient, output a readiness report and revision tasks instead of a manuscript.

### 写作与术语类（Writing & Terminology）

- Do not let recurring terms drift across sections; use the terminology ledger for species, gradients, metrics, models, units, and abbreviations.
- Do not draft a standard research article from shallow literature coverage; target at least 30 verified relevant sources or downgrade the deliverable.
- Do not write an Introduction without an explicit specific gap, operational definitions for core variables, and objectives that map to methods.
- Do not expand an Introduction or Discussion merely to reach a word count; expand only to add a missing writing function, verified literature comparison, claim boundary, or result-linked interpretation.
- Do not leave an unusually short or long Introduction, Discussion, or Conclusion unexplained when preparing a reviewable, journal-format, or submission-ready draft.
- Do not use internal workflow/process language in formal manuscript sections.
- Do not scatter unresolved placeholders through the main scientific narrative; put them in a pre-submission information gap list unless they are needed as transparent caveats.
- Do not discuss central results without returning to effect direction, effect size or estimate, and uncertainty where available.

### 格式与提交类（Format & Submission）

- Do not format a manuscript as generic IMRAD when a journal target contract exists.
- Do not add a table of contents to a manuscript/article DOCX unless the user explicitly asks or the journal target contract requires it.
- Do not provide a reference list without corresponding in-text citations and a citation coverage check.
- Do not treat citation coverage as reference verification; DOI/title/year/source checks are still required for journal-format or submission-ready packages.
- Do not include AI-generated or unverified citations.
- Do not report classification/recognition metrics as final journal-format results without denominators and uncertainty, or an explicit statistical-enhancement task explaining why uncertainty is not available.
- Do not call a text-only draft "journal-format" if central figures/tables, captions, and supplements are only planned.
- Do not call a draft journal-format if a central figure caption asserts a claim stronger than the statistical delivery gate supports and the mismatch is not disclosed as a caveat.
- Do not call a draft journal-format if central figure/table source data, data/code availability routes, or sensitive-data restrictions are unmapped.
- Do not call a DOCX journal-format until layout QA confirms figures are embedded, captions are attached, tables are readable, no accidental TOC exists, and unresolved placeholders are removed or intentionally retained for review.
- Do not call a journal-format draft "submission-ready" while metadata, permissions, sensitive-location policy, reference verification, or figure/table assembly remain unresolved.
- Do not finalize a draft while serious reviewer objections remain unaddressed and undisclosed.
- Do not proceed with a research-article framing when deep research cannot identify a specific answerable unanswered question.

### 安全与伦理类（Security & Ethics）

- Do not expose sensitive species coordinates or patrol-sensitive locations.
- Do not publish exact coordinates or raw point files for sensitive species without explicit authorization and masking/generalization.
- Do not invent authorship, affiliations, funding, permits, ethics, author contributions, conflicts, or data authorization.
- Do not call an automated-recognition manuscript journal-format if model identity, training data, threshold, post-processing, event definition, and matching rules are missing.

## Bundled Resources

- `references/data-type-routing.md`: data-type-specific routes, common outputs, and boundaries.
- `references/journal-target-contract.md`: target journal, article type, format rules, required statements, outputs, and default no-TOC manuscript rule.
- `references/section-length-quality-gate.md`: soft Introduction, Discussion, and Conclusion budgets by article type.
- `references/submission-metadata-contract.md`: author, affiliation, funding, ethics, permits, conflicts, data/code, and sensitive-location metadata.
- `references/pre-submission-review-gates.md`: missing-information handling, conclusion-strength audit, method-completeness template, statistical enhancement suggestions, DOCX layout QA, and sensitive-data security.
- `references/data-contract.md`: freeze raw facts, derived facts, variable provenance, count reconciliation, and manuscript-safe facts before writing.
- `references/author-knowledge-integration.md`: classify existing manuscripts, notes, protocols, appendices, and review comments into adopt, verify, narrow, or exclude.
- `references/deep-literature-standard.md`: require deep research depth, usually at least 30 verified sources for a standard empirical article.
- `references/manuscript-potential-rubric.md`: low/medium/high potential grading for deliverable manuscript paths.
- `references/deliverable-pathways.md`: choose an output path that matches actual data carrying capacity.
- `references/question-method-map.md`: map ecological research questions to method families and manuscript sections.
- `references/answerable-unanswered-question.md`: use deep research to decide whether a researchable gap exists.
- `references/argument-terminology-contract.md`: lock one-sentence argument, reader promise, paragraph jobs, and canonical terminology before drafting.
- `references/claim-boundaries.md`: common overclaims and safer alternatives.
- `references/statistical-delivery-gate.md`: audit model diagnostics, effort handling, sensitivity checks, result readiness.
- `references/result-card-template.md`: reusable result-card and literature-matrix templates.
- `references/figure-table-assembly.md`: assemble main figures/tables, captions, supplements, and sensitive-data checks for delivery.
- `references/figure-claim-trace.md`: verify every central figure/table caption traces back to result cards, statistical gate verdict, and claim ledger.
- `references/data-availability-source-data.md`: map datasets, source data, code, repository/access routes, FAIR metadata.
- `references/introduction-quality-gate.md`: sharpen research gap, define core concepts, remove process language.
- `references/claim-ledger.md`: map every manuscript claim to data, results, literature, assumptions, caveats.
- `references/citation-coverage-check.md`: ensure deep research sources, in-text citations, and reference list form a complete loop.
- `references/reference-verification.md`: verify title, DOI, year, source, status, URL, and official report/database metadata.
- `references/discussion-conclusion-quality-gate.md`: require effect-size back-references, cautious wording, concise conclusions.
- `references/reviewer-objection-simulator.md`: stress-test novelty, methods, evidence strength, variables, limitations, journal fit.
- `references/revision-loop.md`: evaluate, author-decide, and revise without over-inflating claims.
- `references/rewriting-existing-manuscript.md` *(new)*: full adaptation of the 31-step pipeline for rewriting an existing manuscript rather than building from scratch — fast-pass Phase A-C, anchor on statistical gate audit (Phase D), claim narrowing as the core rewrite activity (Phase E).
- `references/literature-search-fallback.md` *(new)*: when web_search is unavailable and browser hits CAPTCHAs, use Crossref/Semantic Scholar REST APIs via terminal curl for deep research literature discovery.
- `references/domain/method-checks/arrive.md`: ARRIVE 2.0 reporting guidelines for animal research, mapped to ecology skill gates.
- `references/domain/interpretation/evidence-quality.md`: evidence quality assessment framework adapted from GRADE for ecological studies.
- `references/domain/language/ecology.md`: terminology and language guide for ecology and biodiversity writing.
- `references/domain/language/conservation.md`: translate statistical results into conservation language without overclaiming. For other subfields, see `references/domain/language/`.
- `references/delivery-readiness-score.md`: label the output as internal/ reviewable/ journal-format/ submission-ready.
- `references/journal-package-checklist.md`: final package and integrity checklist.
- `references/decision-loop.md` *(new)*: PROCEED/REFINE/DOWNGRADE/BLOCK decisions at 5 key gates.
- `references/sentinel-watchdog.md` *(new)*: 5 continuous quality guards (NaN/Inf, consistency, citation, claim, sensitive data).
- `references/multi-perspective-debate.md` *(new)*: conservative/moderate/ambitious 3-perspective debate protocol.
- `references/run-lessons.md` *(new)*: self-learning — capture lessons from each run, convert to reusable skills.
- `references/knowledge-base-spec.md` *(new)*: structured KB output (decisions/findings/literature/reviews) for RWKM integration.
- `references/branch-exploration.md` *(new)*: experimental parallel direction exploration.
- `scripts/audit_data_package.py`: first-pass file and column audit for a data package.
- `scripts/score_manuscript_potential.py`: questionnaire-based manuscript potential grading.
- `scripts/build_result_cards.py`: create blank or CSV-driven result cards.
- `scripts/check_citation_coverage.py`: first-pass Markdown citation coverage audit, with optional minimum reference threshold for standard articles.
- `scripts/check_claim_ledger.py`: first-pass Markdown claim-ledger completeness and claim-strength audit.
- `scripts/check_section_lengths.py`: first-pass Markdown audit for Introduction, Discussion, and Conclusion word counts, proportions, and soft-threshold revision actions.
- `scripts/check_manuscript_language.py`: first-pass audit for process language, strong causal verbs, camera-trap overclaims, HMSC overclaims, and centroid overclaims.
- `scripts/check_conclusion_strength.py`: first-pass audit for unsupported replacement, proof, reliability, standard-protocol, management-effectiveness, and sampling-window claims.
- `scripts/check_acoustic_method_completeness.py`: first-pass checklist for acoustic automated-recognition method details, including human annotation, model, threshold, post-processing, matching sensitivity, and uncertainty.
- `scripts/check_statistical_enhancements.py`: first-pass recommendations for Wilson/exact confidence intervals, matching-threshold sensitivity, site-level uncertainty, threshold curves, and sampling-window boundaries.
- `scripts/check_sensitive_data_security.py`: first-pass audit for exact-coordinate leakage and missing sensitive-location/data-sharing statements.
- `scripts/check_docx_layout_qa.py`: first-pass DOCX audit for embedded images, content types, captions, placeholders, table width risk, accidental TOC, and coordinate-like text.
- `scripts/check_delivery_readiness.py`: first-pass file-level audit of delivery readiness and accidental table-of-contents outputs.
- `scripts/make_manuscript_skeleton.py`: create a manuscript package skeleton.
- `assets/manuscript-template.md`: IMRAD draft scaffold.
- `assets/ai-use-statement-template.md`: AI-use disclosure scaffold.
