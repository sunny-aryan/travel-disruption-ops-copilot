from typing import Any


POLICY_VERSION = "travel-disruption-policy-v1"


def evaluate_policy(case: dict[str, Any], provider_response: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate deterministic workflow policy for a disrupted travel case.

    The policy engine does not decide what the agent should do.
    It decides which actions are allowed, blocked, or require supervisor approval.
    """
    allowed_actions = []
    blocked_actions = []
    supervisor_required_actions = []
    reasons = []

    response_state = provider_response.get("response_state")
    provider_status = provider_response.get("provider_status")
    options = provider_response.get("options", [])
    freshness = provider_response.get("data_freshness_minutes")

    disruption_severity = case.get("disruption_severity")
    ticket_value = case.get("ticket_value_eur", 0)
    special_flags = case.get("special_flags", [])

    provider_data_fresh = freshness is not None and freshness <= 15
    provider_failed = response_state in ["provider_unavailable", "timeout"]
    provider_partial = response_state == "partial_response"
    provider_stale = response_state == "stale_data" or not provider_data_fresh

    has_rebook_option = any(option.get("option_type") == "rebook" for option in options)
    has_refund_option = any(option.get("option_type") == "refund" for option in options)
    has_wait_option = any(option.get("option_type") == "wait" for option in options)

    max_cost_delta = max(
        [
            option.get("cost_delta_eur", 0) or 0
            for option in options
            if option.get("option_type") == "rebook"
        ],
        default=0,
    )

    # Escalation is always available as a safety valve.
    allowed_actions.append("escalate_to_supervisor")
    reasons.append("Escalation is always available for ambiguous or high-risk disruption cases.")

    # Provider failure handling.
    if provider_failed:
        allowed_actions.append("wait_for_provider_update")
        blocked_actions.extend(["rebook_passenger", "issue_refund", "mark_resolved"])
        reasons.append(
            "Provider dependency failed, so rebooking/refund decisions cannot rely on fresh provider data."
        )

    # Stale data handling.
    elif provider_stale:
        allowed_actions.append("wait_for_provider_update")
        blocked_actions.extend(["rebook_passenger", "mark_resolved"])
        reasons.append(
            "Provider data is stale or missing, so rebooking and resolution are blocked until refreshed or reviewed."
        )

        if has_refund_option:
            supervisor_required_actions.append("issue_refund")
            reasons.append(
                "Refund option exists, but stale provider data requires supervisor approval."
            )
        else:
            blocked_actions.append("issue_refund")

    # Partial provider response.
    elif provider_partial:
        allowed_actions.append("wait_for_provider_update")
        reasons.append(
            "Provider returned partial data. Agent may continue investigation, but risky actions require review."
        )

        if has_wait_option:
            allowed_actions.append("prepare_customer_update")

        if has_rebook_option:
            supervisor_required_actions.append("rebook_passenger")

        if has_refund_option:
            supervisor_required_actions.append("issue_refund")
        else:
            blocked_actions.append("issue_refund")

    # Fresh successful provider response.
    else:
        if has_rebook_option:
            allowed_actions.append("rebook_passenger")
            reasons.append("Fresh provider data includes at least one rebooking option.")

        if has_refund_option:
            allowed_actions.append("issue_refund")
            reasons.append("Fresh provider data includes a refund option.")

        if has_wait_option:
            allowed_actions.append("wait_for_provider_update")

        if has_rebook_option or has_refund_option or has_wait_option:
            allowed_actions.append("prepare_customer_update")

        if not options:
            blocked_actions.extend(["rebook_passenger", "issue_refund", "mark_resolved"])
            reasons.append("No provider recovery options are available.")

    # Ticket value threshold.
    if ticket_value >= 200:
        if "issue_refund" in allowed_actions:
            allowed_actions.remove("issue_refund")
        if "issue_refund" not in supervisor_required_actions:
            supervisor_required_actions.append("issue_refund")
        reasons.append("Ticket value is above €200, so refund requires supervisor approval.")

    # High-cost rebooking threshold.
    if max_cost_delta > 50:
        if "rebook_passenger" in allowed_actions:
            allowed_actions.remove("rebook_passenger")
        if "rebook_passenger" not in supervisor_required_actions:
            supervisor_required_actions.append("rebook_passenger")
        reasons.append("Rebooking cost delta is above €50, so rebooking requires supervisor approval.")

    # Special handling flags.
    if any(flag in special_flags for flag in ["accessibility_support", "same_day_medical_visit", "overnight_risk"]):
        if "escalate_to_supervisor" not in allowed_actions:
            allowed_actions.append("escalate_to_supervisor")
        reasons.append(
            "Passenger has sensitive impact flags, so supervisor escalation should remain available."
        )

    # Critical cases should not be allowed to sit silently.
    if disruption_severity == "critical":
        if "wait_for_provider_update" in allowed_actions:
            supervisor_required_actions.append("wait_for_provider_update")
            allowed_actions.remove("wait_for_provider_update")
        reasons.append("Critical disruption cases require active review rather than passive waiting.")

    # Remove duplicates while preserving order.
    allowed_actions = list(dict.fromkeys(allowed_actions))
    blocked_actions = list(dict.fromkeys(blocked_actions))
    supervisor_required_actions = list(dict.fromkeys(supervisor_required_actions))
    reasons = list(dict.fromkeys(reasons))

    # If an action is supervisor-required, it should not also appear as simply allowed.
    allowed_actions = [
        action for action in allowed_actions if action not in supervisor_required_actions
    ]

    return {
        "policy_version": POLICY_VERSION,
        "provider_status": provider_status,
        "allowed_actions": allowed_actions,
        "blocked_actions": blocked_actions,
        "supervisor_required_actions": supervisor_required_actions,
        "reasons": reasons,
    }