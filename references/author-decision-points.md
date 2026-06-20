# Author Decision Points (ADP)

> This reference defines the three points in the pipeline where control is handed to the **author**, not decided silently by the Agent. At every other step the Agent runs its internal quality gates in the background. ADPs are where the Agent must **stop, lay out evidence, and let the author pick the direction** before continuing.

## Why ADPs Exist

The 31-step pipeline contains ~28 internal quality gates the Agent runs on its own. Those stay automatic. But three decisions shape the entire manuscript and belong to the author:

1. **Which question the data should answer** (ADP-1).
2. **Whether the central statistical results are usable** (ADP-2).
3. **How strongly the manuscript is allowed to claim** (ADP-3).

Deciding these silently produces a manuscript the author never agreed to. ADPs make these three decisions visible and author-owned, while keeping the rest of the machinery quiet.

## Soft-Stop with Default (interaction contract)

Every ADP is a **soft stop**, not a hard block:

- The Agent presents the evidence and a **recommended option marked as the default**.
- The Agent states explicitly: *"If you do not respond, I will proceed with [recommended option]."*
- If the author responds, follow the author's choice.
- If the author does not respond (e.g. the run is unattended, a cron job, or a subagent), proceed with the recommended default rather than stalling.

This gives the author a real intervention window without deadlocking an unattended run. The default must always be the **most defensible** option, never the most ambitious.

Do NOT convert an ADP into a hard block. Do NOT skip the author-facing presentation just because a default exists — the evidence must always be laid out so the author *could* have intervened.

---

## ADP-1: Direction Selection

**Position:** After the exploratory analysis step in Phase B, replacing the silent decision at Gate 2 (Answerable Question). This is the most important ADP — it sets the entire manuscript trajectory.

**Prerequisite:** The exploratory analysis has been run (descriptive statistics, visualizations, initial patterns) on the frozen data contract. Direction candidates must be grounded in **what the data actually produced**, not in the variable list alone.

### What the Agent must lay out

1. **Exploratory analysis summary** — the patterns, distributions, and relationships the data actually showed. Plain-language, with the key numbers.
2. **2-4 candidate directions.** For each:
   - **Type:** `application-practice` or `hypothesis` (see twofold classification below).
   - **What the data can answer** — to what depth, with what claim boundary.
   - **Nearest literature gap** — what is already answered, what specific gap remains (run a light `answerable-unanswered-question.md` pass per candidate).
   - **Contribution-language ceiling** — the strongest honest framing this direction supports (see below).
3. **Recommended default** — the most defensible candidate, clearly marked.

### Twofold direction classification

Every candidate direction is tagged as one of:

- **Application-practice (`application-practice`)**: the data inform a practical/management/monitoring question, or surface a descriptive pattern. This is the natural home for data-driven, pattern-finding work. Framing: *describe, evaluate, assess, identify associations, propose for monitoring.*
- **Hypothesis (`hypothesis`)**: the direction is organized around a hypothesis. This is **legitimate whether the hypothesis came before or emerged from the data** — generating hypotheses from data is normal science. The only constraint is the contribution-language ceiling below.

There is **no HARKing penalty and no forced downgrade for data-derived hypotheses.** A hypothesis that emerged from the data is a valid scientific product.

### Contribution-language ceiling (the one real constraint)

The reporting language must match the **evidence strength**, not the origin of the hypothesis:

- A pattern that **emerged from the data** with no independent validation step → frame as *hypothesis-generating / descriptive / observed pattern*. Say plainly: "we observed X and propose the hypothesis that…". Do not report it with confirmatory language ("we tested and confirmed H1", emphatic p-value framing).
- A hypothesis with an **independent validation step** (held-out data, a new sampling round, an external dataset) → confirmatory language is allowed.

This is purely about *whether the wording matches what was actually done* — it has nothing to do with whether the hypothesis preceded the data. Enforced via `claim-boundaries.md` and `answerable-unanswered-question.md`.

### Author picks

- **Select** one candidate direction → proceed to argument & terminology contract.
- **Adjust** → refine scope/framing of a candidate and re-present.
- **Downgrade** → choose a monitoring baseline / data note / local report / methods note path.
- **No response** → proceed with the recommended default direction.

### Output template

```md
# ADP-1: Direction Selection

## Exploratory Analysis Summary
- Key patterns:
- Key numbers:
- Notable distributions / relationships:

## Candidate Directions

### Direction A  [type: application-practice | hypothesis]  ⭐ RECOMMENDED DEFAULT
- What the data can answer:
- Claim boundary:
- Nearest literature gap:
- Contribution-language ceiling:

### Direction B  [type: ...]
- ...

### Direction C  [type: ...]
- ...

## Recommendation
- Default if no response: Direction A
- Reason it is the most defensible:

## Author choice: [ select A/B/C | adjust | downgrade ]
```

---

## ADP-2: Statistical Delivery Confirmation

**Position:** At Gate 3 (Statistical Delivery, step 17), replacing the silent PROCEED/REFINE/BLOCK decision.

**Prerequisite:** `statistical-delivery-gate.md` has been run; every central result has a ready / usable-with-caveat / needs-analysis / not-usable verdict.

### What the Agent must lay out

1. **Central result inventory** — one line per central result.
2. **Per-result verdict** — `ready` / `usable with caveat` / `needs analysis` / `not usable`, with the diagnostic reason (missing residual checks, no uncertainty interval, overdispersion, etc.).
3. **Recommended default** — proceed with `ready`/`caveat` results, flag `needs-analysis` for additional work, drop `not-usable`.

### Author picks

- **Confirm** the verdicts as-is → proceed to result cards.
- **Request more analysis** on a `needs-analysis` result before it can be central.
- **Drop** a result from the central claims.
- **No response** → proceed with the recommended default (use ready/caveat, run the flagged additional analysis if quick, drop not-usable).

### Output template

```md
# ADP-2: Statistical Delivery Confirmation

| Central result | Verdict | Diagnostic reason | Recommended action |
|---|---|---|---|
|  | ready / caveat / needs-analysis / not-usable |  |  |

## Recommendation
- Default if no response:

## Author choice: [ confirm | request analysis on … | drop … ]
```

---

## ADP-3: Claim Boundary Confirmation

**Position:** At Gate 6.5 (Claim Ledger, step 21), before drafting Discussion, replacing the silent claim-narrowing decision.

**Prerequisite:** A draft `claim-ledger.md` exists, with each planned claim classified and traced to data/results/literature.

### What the Agent must lay out

1. **Claim ledger draft** — each planned claim with its current strength classification (observed fact / derived metric / model-supported / literature-supported / interpretation / management implication / unsupported).
2. **Proposed narrowing** — for each claim the statistics don't fully support, the narrowed wording the Agent recommends (causal → associative, qualitative label → descriptive comparison, management directive → hypothesis).
3. **Recommended default** — adopt the proposed narrowing.

### Author picks

- **Lock** the ledger with the proposed narrowing → proceed to draft Discussion.
- **Push back** on a specific narrowing (author may have independent evidence that supports a stronger claim — if so, it must be cited).
- **No response** → proceed with the proposed narrowing (the conservative default).

### Output template

```md
# ADP-3: Claim Boundary Confirmation

| Planned claim | Current strength | Statistics support? | Proposed wording |
|---|---|---|---|

## Removed or Narrowed Claims
| Original | Narrowed to | Why |
|---|---|---|

## Recommendation
- Default if no response: adopt all proposed narrowing

## Author choice: [ lock | push back on … (with citation) ]
```

---

## Relationship to existing gates

ADPs do not replace the internal gates' *logic* — the data contract, statistical delivery gate, and claim ledger still produce their full analysis. ADPs change **who makes the call and whether it is visible**: the Agent surfaces the gate's output to the author at these three points instead of deciding silently. All other gates (figure-claim trace, reviewer simulation, citation coverage, etc.) remain fully automatic in the background.
