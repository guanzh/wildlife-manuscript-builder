# Author Decision Points (ADP)

> This reference defines the three points in the pipeline where control is handed to the **author**, not decided silently by the Agent. At every other step the Agent runs its internal quality gates in the background. ADPs are where the Agent must **stop, lay out evidence, and let the author pick the direction** before continuing.

## Why ADPs Exist

The 31-step pipeline contains ~28 internal quality gates the Agent runs on its own. Those stay automatic. But three decisions shape the entire manuscript and belong to the author:

1. **Which question the data should answer** (ADP-1).
2. **Whether the central statistical results are usable** (ADP-2).
3. **How strongly the manuscript is allowed to claim** (ADP-3).

Deciding these silently produces a manuscript the author never agreed to. ADPs make these three decisions visible and author-owned, while keeping the rest of the machinery quiet.

## Interaction Modes and Stop Levels

Default mode is **interactive**. In this mode, ADP-1 is a **hard stop** because choosing the manuscript direction is the highest-value author judgment in a data-first workflow.

Use these stop levels:

- **Hard stop by default:** ADP-1 Direction Selection. The Agent presents evidence and candidate directions, then waits for the author to select, adjust, or downgrade. Do not proceed silently in interactive work.
- **Soft stop with conservative default:** ADP-2 Statistical Delivery and ADP-3 Claim Boundary. The Agent presents evidence, marks the most defensible default, and may proceed if the author does not respond.
- **Unattended exception:** If the user or run configuration explicitly asks for an unattended/automatic run, ADP-1 may proceed with the most defensible default after the evidence is displayed. This exception prevents cron jobs, subagents, and batch runs from stalling.

The default must always be the **most defensible** option, never the most ambitious. Never skip the author-facing presentation just because a default exists.

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
3. **Recommended default** — the most defensible candidate, clearly marked for reference or for explicitly unattended runs.

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
- **No response in interactive mode** → stop with the ADP-1 package and wait for author choice.
- **No response in explicitly unattended mode** → proceed with the recommended default direction.

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
- Recommended default for unattended mode: Direction A
- Reason it is the most defensible:

## Interaction status
- Interactive mode: do not proceed until the author selects, adjusts, or downgrades.
- Unattended mode: proceed with the recommended default if no response is possible.

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

ADPs do not replace the internal gates' *logic* — the data contract, statistical delivery gate, and claim ledger still produce their full analysis. ADPs change **who makes the call and whether it is visible**: the Agent surfaces the gate's output to the author at these three points instead of deciding silently. ADP-1 is author-owned by default; ADP-2 and ADP-3 may use conservative defaults after presenting evidence. All other gates (figure-claim trace, reviewer simulation, citation coverage, etc.) remain fully automatic in the background.
