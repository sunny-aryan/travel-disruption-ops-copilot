from typing import Final


ACTION_TO_STATUS: Final[dict[str, str]] = {
    "rebook_passenger": "RESOLVED_REBOOKED",
    "issue_refund": "RESOLVED_REFUNDED",
    "wait_for_provider_update": "WAITING_PROVIDER",
    "escalate_to_supervisor": "PENDING_SUPERVISOR_APPROVAL",
    "prepare_customer_update": "CUSTOMER_CONTACT_PENDING",
    "mark_resolved": "RESOLVED",
}


def derive_next_status(selected_action: str, approval_required: bool) -> str:
    """
    Derive the next case lifecycle state from selected action.

    Supervisor-required actions move to approval state rather than final resolution.
    """
    if approval_required:
        return "PENDING_SUPERVISOR_APPROVAL"

    return ACTION_TO_STATUS.get(selected_action, "INVESTIGATING")