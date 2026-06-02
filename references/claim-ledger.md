# Claim Ledger

Use this gate after result cards and the literature matrix, before drafting Discussion. Update it again after the full draft.

The claim ledger turns the manuscript from prose into an auditable argument. Every important claim should have an evidence source, claim strength, boundary, and status.

## Claim Strength Categories

Use the weakest category that honestly fits:

- observed fact: direct survey, metadata, or raw-data fact.
- derived metric: cleaned, filtered, aggregated, standardized, or classified value.
- model-supported association: statistical result with estimate, uncertainty, and model context.
- literature context: background, comparison, or method expectation from verified sources.
- interpretation: explanation that combines result plus literature but is not directly tested.
- management implication: cautious application to monitoring or conservation decisions.
- causal claim: requires experimental, counterfactual, BACI, controlled, or otherwise defensible causal design. Usually remove or narrow.
- unsupported: remove, rewrite, or convert to future work.

For central Discussion claims, the evidence source should include the effect estimate or uncertainty location, not only a general result label.

Causal claims cannot be kept only because the caveat mentions "no counterfactual design" or "no experiment". That caveat is a reason to narrow or remove the claim, not a reason to retain causal wording.

## Required Ledger Table

Use these exact column names when possible so `scripts/check_claim_ledger.py` can audit the file.

```md
| Claim ID | Manuscript Location | Claim | Evidence Source | Evidence ID | Claim Strength | Boundary / Caveat | Status |
|---|---|---|---|---|---|---|---|
| C001 | Results |  | data-contract / result-card / literature / method / author-confirmed / assumption | F001 / D001 / R001 / citation key | observed fact / derived metric / model-supported association / literature context / interpretation / management implication / causal claim / unsupported |  | keep / narrow / remove / needs verification |
```

## Evidence Source Rules

- Data-contract claims must cite a fact ID from the data contract.
- Result claims must cite a result-card ID, figure, table, estimate, or model-output row.
- Literature claims must cite verified sources that also appear in the literature matrix and final reference list.
- Method claims must cite accepted method papers, software, or a clearly described reproducible workflow.
- Author-confirmed claims must be marked as such and should not become statistical or legal claims without documentation.
- Assumptions must stay in Methods, limitations, or future-work language.

## Section Rules

Introduction:

- Use literature context and gap claims.
- Do not introduce dataset results before Methods/Results unless the journal style requires it.

Methods:

- Use observed facts, derived facts, and method claims.
- Do not imply analyses were done if only figures or summaries exist.

Results:

- Use derived metrics and model-supported associations.
- Do not explain causes, mechanisms, or management meaning.

Discussion:

- Move from result to comparison to explanation to boundary to implication.
- Every interpretation must be linked to a result card plus literature context.

Abstract and title:

- Must be no stronger than the strongest supported claim in the ledger.
- Avoid causal or management-effectiveness wording unless the ledger supports it.

Introduction:

- Gap claims must cite the literature matrix and state what closest studies already answered.
- Definitions of core variables should trace to the data contract or Methods.

## Required Output

```md
# Claim Ledger

## Ledger

| Claim ID | Manuscript Location | Claim | Evidence Source | Evidence ID | Claim Strength | Boundary / Caveat | Status |
|---|---|---|---|---|---|---|---|

## Removed Or Narrowed Claims

| Original claim | Problem | Safer replacement |
|---|---|---|

## Strongest Permitted Abstract Claim

## Claims That Require Author Verification

## Claims That Require New Analysis Or Data
```

## Common Wildlife Overclaims

Narrow these unless the design truly supports them:

- Detection rate or RAI equals abundance or density.
- Camera records prove absence.
- Correlation with disturbance proves avoidance, sensitivity, or causation.
- Protected-area edge patterns prove management effectiveness.
- Co-occurrence proves species interaction.
- A local species inventory proves regional conservation status.
- A proxy variable is treated as the exact ecological process it only approximates.

## Final Rule

If a major title, abstract, result, discussion, or management claim is missing from the ledger, add it, narrow it, or remove it before finalizing the manuscript.
