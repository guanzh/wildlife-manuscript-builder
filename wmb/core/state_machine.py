"""Legal workflow transitions for canonical WMB run state."""

from __future__ import annotations

from collections.abc import Mapping

RUN_STATUSES = frozenset(
    {
        "intake",
        "awaiting_research_direction",
        "evidence_and_analysis",
        "result_and_claim_build",
        "manuscript_drafting",
        "independent_review",
        "package_verification",
        "awaiting_final_confirmation",
        "candidate_level_4",
        "downgraded",
        "blocked",
    }
)

DECISIONS = frozenset({"PROCEED", "REFINE", "DOWNGRADE", "BLOCK"})

_ACTIVE_STATUSES = frozenset(
    {
        "intake",
        "awaiting_research_direction",
        "evidence_and_analysis",
        "result_and_claim_build",
        "manuscript_drafting",
        "independent_review",
        "package_verification",
        "awaiting_final_confirmation",
    }
)

DECISION_TRANSITIONS: Mapping[str, Mapping[str, frozenset[str]]] = {
    "PROCEED": {
        "intake": frozenset({"awaiting_research_direction"}),
        "awaiting_research_direction": frozenset({"evidence_and_analysis"}),
        "evidence_and_analysis": frozenset({"result_and_claim_build"}),
        "result_and_claim_build": frozenset({"manuscript_drafting"}),
        "manuscript_drafting": frozenset({"independent_review"}),
        "independent_review": frozenset({"package_verification"}),
        "package_verification": frozenset({"awaiting_final_confirmation"}),
        "awaiting_final_confirmation": frozenset({"candidate_level_4"}),
    },
    "REFINE": {
        "intake": frozenset({"intake"}),
        "awaiting_research_direction": frozenset({"awaiting_research_direction"}),
        "evidence_and_analysis": frozenset({"evidence_and_analysis"}),
        "result_and_claim_build": frozenset(
            {"evidence_and_analysis", "result_and_claim_build"}
        ),
        "manuscript_drafting": frozenset(
            {"result_and_claim_build", "manuscript_drafting"}
        ),
        "independent_review": frozenset(
            {"manuscript_drafting", "independent_review"}
        ),
        "package_verification": frozenset(
            {"manuscript_drafting", "package_verification"}
        ),
        "awaiting_final_confirmation": frozenset(
            {"manuscript_drafting", "awaiting_final_confirmation"}
        ),
    },
    "DOWNGRADE": {
        status: frozenset({"downgraded"}) for status in _ACTIVE_STATUSES
    },
    "BLOCK": {status: frozenset({"blocked"}) for status in _ACTIVE_STATUSES},
}

LEGAL_TRANSITIONS: Mapping[str, frozenset[str]] = {
    status: frozenset(
        target
        for transitions in DECISION_TRANSITIONS.values()
        for target in transitions.get(status, ())
    )
    for status in RUN_STATUSES
}


class IllegalTransition(ValueError):
    """Raised when a requested canonical workflow transition is not legal."""


def validate_transition(from_status: object, to_status: object, decision: object) -> None:
    """Raise ``IllegalTransition`` unless the decision permits the state change."""

    if not isinstance(decision, str) or decision not in DECISIONS:
        raise IllegalTransition(
            f"decision must be one of {', '.join(sorted(DECISIONS))}"
        )
    if not isinstance(from_status, str) or from_status not in RUN_STATUSES:
        raise IllegalTransition(f"unknown current status: {from_status!r}")
    if not isinstance(to_status, str) or to_status not in RUN_STATUSES:
        raise IllegalTransition(f"unknown target status: {to_status!r}")

    legal_targets = DECISION_TRANSITIONS[decision].get(from_status, frozenset())
    if to_status not in legal_targets:
        raise IllegalTransition(
            f"{decision} transition from {from_status!r} to {to_status!r} "
            "is not legal"
        )
