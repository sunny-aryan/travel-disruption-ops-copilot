from src.db.seed import seed_cases_if_empty
from src.db.operations import (
    create_decision,
    create_supervisor_decision,
    get_audit_events_for_case,
    get_decisions_for_case,
    get_supervisor_decisions_for_case,
)
from src.db.schema import initialize_database
from datetime import datetime
from src.policy.policy_engine import evaluate_policy

import streamlit as st
import pandas as pd

from src.data_loader import get_case_by_id, load_cases
from src.services.provider_client import (
    get_recovery_options,
    is_provider_data_fresh,
    provider_status_label,
    response_state_label,
)


st.set_page_config(
    page_title="Travel Disruption Ops Copilot",
    page_icon="🚆",
    layout="wide",
)


def priority_rank(severity: str) -> int:
    rank = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }
    return rank.get(severity, 5)


def priority_label(severity: str) -> str:
    labels = {
        "critical": "🔴 Critical",
        "high": "🟠 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low",
    }
    return labels.get(severity, "⚪ Unknown")


def format_flags(flags: list[str]) -> str:
    if not flags:
        return "None"

    return ", ".join(flag.replace("_", " ") for flag in flags)


def format_datetime(value) -> str:
    if value is None:
        return "Unknown"

    return value.strftime("%d %b %Y, %H:%M")


def calculate_sla_status(sla_deadline) -> str:
    now = datetime.now()

    if sla_deadline.to_pydatetime() < now:
        return "🔴 Breached"

    hours_remaining = (sla_deadline.to_pydatetime() - now).total_seconds() / 3600

    if hours_remaining <= 2:
        return "🟠 At risk"

    if hours_remaining <= 6:
        return "🟡 Watch"

    return "🟢 Healthy"


def build_display_queue(cases_df):
    display_df = cases_df[
        [
            "case_id",
            "priority",
            "sla_deadline",
            "provider",
            "origin",
            "destination",
            "disruption_type",
            "passenger_count",
            "customer_tier",
            "special_flags",
            "status",
            "recommended_next_action",
        ]
    ].copy()

    display_df["route"] = display_df["origin"] + " → " + display_df["destination"]
    display_df["special_flags"] = display_df["special_flags"].apply(format_flags)
    display_df["sla_deadline"] = display_df["sla_deadline"].dt.strftime(
        "%d %b %Y, %H:%M"
    )

    return display_df[
        [
            "case_id",
            "priority",
            "sla_deadline",
            "provider",
            "route",
            "disruption_type",
            "passenger_count",
            "customer_tier",
            "special_flags",
            "status",
            "recommended_next_action",
        ]
    ]

def format_option_datetime(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return pd.to_datetime(value).strftime("%d %b %Y, %H:%M")


def format_cost_delta(value) -> str:
    if value is None:
        return "N/A"

    if value == 0:
        return "€0.00"

    return f"€{value:.2f}"


def render_provider_status(provider_response: dict) -> None:
    st.markdown("### Provider Dependency Status")

    provider_status = provider_response["provider_status"]
    response_state = provider_response["response_state"]
    freshness = provider_response["data_freshness_minutes"]

    freshness_label = "Unknown" if freshness is None else f"{freshness} min old"

    st.markdown(
        f"""
        **Provider status:** {provider_status_label(provider_status)}  
        **Response state:** {response_state_label(response_state)}  
        **Data freshness:** {freshness_label}
        """
    )

    st.caption(provider_response["provider_message"])

    if not is_provider_data_fresh(provider_response):
        st.warning(
            "Provider data is not fresh enough for normal automated recommendation. "
            "Agent should wait, refresh, or escalate depending on case urgency."
        )

    if response_state in ["provider_unavailable", "timeout"]:
        st.error(
            "Recovery options are unavailable because the provider dependency failed. "
            "Do not rebook from stale or missing data."
        )


def render_recovery_options(provider_response: dict) -> None:
    st.markdown("### Recovery Options")

    options = provider_response.get("options", [])

    if not options:
        st.warning("No recovery options available from provider response.")
        return

    options_df = pd.DataFrame(options)

    options_df["departure_time"] = options_df["departure_time"].apply(
        format_option_datetime
    )
    options_df["arrival_time"] = options_df["arrival_time"].apply(format_option_datetime)
    options_df["cost_delta_eur"] = options_df["cost_delta_eur"].apply(format_cost_delta)

    options_df = options_df[
        [
            "option_id",
            "option_type",
            "departure_time",
            "arrival_time",
            "arrival_delay_minutes",
            "cost_delta_eur",
            "confidence",
        ]
    ]

    st.dataframe(
        options_df,
        use_container_width=True,
        hide_index=True,
    )


def provider_guidance(provider_response: dict) -> str:
    response_state = provider_response["response_state"]

    if response_state == "success":
        return "Fresh provider options are available. Agent can evaluate rebooking or refund actions."

    if response_state == "partial_response":
        return "Provider returned partial data. Agent can continue investigation, but high-risk actions should be reviewed carefully."

    if response_state == "stale_data":
        return "Provider data is stale. Agent should not rely on these options without refresh or supervisor review."

    if response_state in ["provider_unavailable", "timeout"]:
        return "Provider dependency failed. Agent should wait for recovery or escalate urgent cases."

    return "Provider response is unclear. Agent should investigate before taking action."

def humanize_action(action: str) -> str:
    return action.replace("_", " ").title()


def render_policy_evaluation(policy_result: dict) -> None:
    st.markdown("### Policy Evaluation")

    st.caption(f"Policy version: `{policy_result['policy_version']}`")

    allowed = policy_result["allowed_actions"]
    blocked = policy_result["blocked_actions"]
    supervisor_required = policy_result["supervisor_required_actions"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Allowed**")
        if allowed:
            for action in allowed:
                st.success(humanize_action(action))
        else:
            st.caption("No directly allowed actions.")

    with col2:
        st.markdown("**Needs Approval**")
        if supervisor_required:
            for action in supervisor_required:
                st.warning(humanize_action(action))
        else:
            st.caption("No supervisor approval required.")

    with col3:
        st.markdown("**Blocked**")
        if blocked:
            for action in blocked:
                st.error(humanize_action(action))
        else:
            st.caption("No blocked actions.")

    with st.expander("Policy reasons"):
        for reason in policy_result["reasons"]:
            st.markdown(f"- {reason}")

def build_action_options(policy_result: dict) -> list[dict]:
    """Build selectable agent actions from deterministic policy output."""
    action_options = []

    for action in policy_result["allowed_actions"]:
        action_options.append(
            {
                "action": action,
                "label": f"✅ {humanize_action(action)}",
                "approval_required": False,
            }
        )

    for action in policy_result["supervisor_required_actions"]:
        action_options.append(
            {
                "action": action,
                "label": f"⚠️ {humanize_action(action)}",
                "approval_required": True,
            }
        )

    return action_options


def get_action_guidance(action: str, approval_required: bool) -> str:
    """Return UX guidance for a selected action."""
    guidance = {
        "rebook_passenger": "Use this only when provider data is fresh and the selected rebooking option is reliable.",
        "issue_refund": "Use this when refund is policy-eligible. High-value or uncertain refunds may require approval.",
        "wait_for_provider_update": "Use this when provider data is unavailable, stale, partial, or still changing.",
        "escalate_to_supervisor": "Use this when the case is high-risk, ambiguous, urgent, or blocked by policy.",
        "prepare_customer_update": "Use this to draft or send a customer-facing update before final resolution.",
        "mark_resolved": "Use this only after a valid rebooking, refund, or no-action resolution path exists.",
    }

    base_guidance = guidance.get(
        action,
        "Review the policy evaluation and provider status before taking this action.",
    )

    if approval_required:
        return f"{base_guidance} This action requires supervisor approval before completion."

    return base_guidance

def render_agent_decision_panel(case: dict, policy_result: dict) -> None:
    st.markdown("### Agent Decision Panel")

    action_options = build_action_options(policy_result)

    if not action_options:
        st.error("No selectable actions are currently available for this case.")
        return

    action_labels = [option["label"] for option in action_options]

    selected_label = st.selectbox(
        "Proposed action",
        options=action_labels,
        key=f"action_{case['case_id']}",
    )

    selected_option = next(
        option for option in action_options if option["label"] == selected_label
    )

    selected_action = selected_option["action"]
    approval_required = selected_option["approval_required"]

    if approval_required:
        st.warning("This action requires supervisor approval.")
    else:
        st.success("This action is directly allowed by policy.")

    st.info(get_action_guidance(selected_action, approval_required))

    rationale = st.text_area(
        "Agent rationale",
        placeholder="Explain why this action is appropriate for this disrupted booking...",
        key=f"rationale_{case['case_id']}",
    )

    submitted = st.button(
        "Submit decision",
        key=f"submit_{case['case_id']}",
        help="Submit this decision and record an audit event.",
    )

    if submitted:
        if len(rationale.strip()) < 10:
            st.error("Please enter a rationale of at least 10 characters before submitting.")
        else:
            decision_id = create_decision(
                case_id=case["case_id"],
                selected_action=selected_action,
                approval_required=approval_required,
                rationale=rationale.strip(),
                policy_version=policy_result["policy_version"],
            )

            st.success(f"Decision submitted and recorded. Decision ID: {decision_id}")
            st.rerun()

    st.caption("A rationale of at least 10 characters is required for auditability.")

def format_boolean_label(value) -> str:
    return "Yes" if bool(value) else "No"


def render_decision_history(case_id: str) -> None:
    st.markdown("### Decision History")

    decisions_df = get_decisions_for_case(case_id)

    if decisions_df.empty:
        st.caption("No decisions recorded for this case yet.")
        return

    display_df = decisions_df.copy()
    display_df["selected_action"] = display_df["selected_action"].apply(humanize_action)
    display_df["approval_required"] = display_df["approval_required"].apply(
        format_boolean_label
    )

    st.dataframe(
        display_df[
            [
                "decision_id",
                "selected_action",
                "approval_required",
                "rationale",
                "policy_version",
                "created_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_audit_trail(case_id: str) -> None:
    st.markdown("### Audit Trail")

    audit_df = get_audit_events_for_case(case_id)

    if audit_df.empty:
        st.caption("No audit events recorded for this case yet.")
        return

    st.dataframe(
        audit_df[
            [
                "event_id",
                "event_type",
                "event_description",
                "created_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

def render_supervisor_decision_panel(case: dict) -> None:
    st.markdown("### Supervisor Decision")

    supervisor_options = {
        "Approve": "approve",
        "Reject": "reject",
        "Request more information": "request_more_information",
    }

    selected_label = st.selectbox(
        "Supervisor action",
        options=list(supervisor_options.keys()),
        key=f"supervisor_action_{case['case_id']}",
    )

    selected_decision = supervisor_options[selected_label]

    guidance = {
        "approve": "Approve when the proposed action is reasonable and the operational risk is acceptable.",
        "reject": "Reject when the proposed action is unsafe, unsupported by evidence, or violates policy.",
        "request_more_information": "Use this when the case needs more provider data, agent context, or customer information.",
    }

    st.info(guidance[selected_decision])

    rationale = st.text_area(
        "Supervisor rationale",
        placeholder="Explain the reason for this supervisor decision...",
        key=f"supervisor_rationale_{case['case_id']}",
    )

    submitted = st.button(
        "Submit supervisor decision",
        key=f"submit_supervisor_{case['case_id']}",
    )

    if submitted:
        if len(rationale.strip()) < 10:
            st.error("Please enter a supervisor rationale of at least 10 characters.")
        else:
            supervisor_decision_id = create_supervisor_decision(
                case_id=case["case_id"],
                supervisor_decision=selected_decision,
                rationale=rationale.strip(),
            )

            st.success(
                f"Supervisor decision recorded. Decision ID: {supervisor_decision_id}"
            )
            st.rerun()

    st.caption("Supervisor decisions update case state and are recorded in the audit trail.")

def render_supervisor_decision_history(case_id: str) -> None:
    st.markdown("### Supervisor Decision History")

    supervisor_df = get_supervisor_decisions_for_case(case_id)

    if supervisor_df.empty:
        st.caption("No supervisor decisions recorded for this case yet.")
        return

    display_df = supervisor_df.copy()
    display_df["supervisor_decision"] = display_df["supervisor_decision"].apply(
        humanize_action
    )

    st.dataframe(
        display_df[
            [
                "supervisor_decision_id",
                "supervisor_decision",
                "rationale",
                "previous_status",
                "new_status",
                "created_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

def render_supervisor_case_review(case: dict) -> None:
    provider_response = get_recovery_options(case["case_id"])
    policy_result = evaluate_policy(case, provider_response)

    st.divider()
    st.subheader(f"Supervisor Review: {case['case_id']}")

    top_col1, top_col2, top_col3, top_col4 = st.columns(4)

    with top_col1:
        st.metric("Priority", priority_label(case["disruption_severity"]))

    with top_col2:
        st.metric("SLA status", calculate_sla_status(case["sla_deadline"]))

    with top_col3:
        st.metric("Current status", case["status"])

    with top_col4:
        st.metric("Ticket value", f"€{case['ticket_value_eur']:.2f}")

    left_col, right_col = st.columns([1.4, 1])

    with left_col:
        st.markdown("### Case Context")

        st.markdown(
            f"""
            **Passenger:** {case["passenger_name"]}  
            **Route:** {case["origin"]} → {case["destination"]}  
            **Provider:** {case["provider"]}  
            **Disruption:** {case["disruption_type"].replace("_", " ").title()}  
            **Special flags:** {format_flags(case["special_flags"])}
            """
        )

        render_provider_status(provider_response)

    with right_col:
        render_supervisor_decision_panel(case)

    st.divider()

    render_policy_evaluation(policy_result)

    st.divider()

    render_decision_history(case["case_id"])

    st.divider()

    render_supervisor_decision_history(case["case_id"])

    st.divider()

    render_audit_trail(case["case_id"])

def render_supervisor_queue(cases_df) -> None:
    st.subheader("Supervisor Review Queue")

    supervisor_df = cases_df[
        cases_df["status"] == "PENDING_SUPERVISOR_APPROVAL"
    ].copy()

    if supervisor_df.empty:
        st.success("No cases currently require supervisor review.")
        return

    supervisor_df["priority_rank"] = supervisor_df["disruption_severity"].apply(
        priority_rank
    )
    supervisor_df["priority"] = supervisor_df["disruption_severity"].apply(
        priority_label
    )
    supervisor_df = supervisor_df.sort_values(
        by=["priority_rank", "sla_deadline", "updated_at"]
    )

    display_df = build_display_queue(supervisor_df)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    selected_case_id = st.selectbox(
        "Select a supervisor case to review",
        options=supervisor_df["case_id"].tolist(),
        key="supervisor_case_selector",
    )

    selected_case = get_case_by_id(selected_case_id)
    render_supervisor_case_review(selected_case)

def render_case_detail(case: dict) -> None:
    provider_response = get_recovery_options(case["case_id"])
    policy_result = evaluate_policy(case, provider_response)
    st.subheader(f"Case Detail: {case['case_id']}")

    top_col1, top_col2, top_col3, top_col4 = st.columns(4)

    with top_col1:
        st.metric("Priority", priority_label(case["disruption_severity"]))

    with top_col2:
        st.metric("SLA status", calculate_sla_status(case["sla_deadline"]))

    with top_col3:
        st.metric("Ticket value", f"€{case['ticket_value_eur']:.2f}")

    with top_col4:
        st.metric("Passengers", case["passenger_count"])

    st.divider()

    left_col, middle_col, right_col = st.columns([1.1, 1.2, 1])

    with left_col:
        st.markdown("### Booking & Passenger Context")

        st.markdown(
            f"""
            **Passenger:** {case["passenger_name"]}  
            **Booking ID:** {case["booking_id"]}  
            **Customer tier:** {case["customer_tier"].title()}  
            **Special flags:** {format_flags(case["special_flags"])}
            """
        )

        st.markdown("### Route")

        st.markdown(
            f"""
            **Origin:** {case["origin"]}  
            **Destination:** {case["destination"]}  
            **Departure:** {format_datetime(case["departure_time"])}
            """
        )

    with middle_col:
        st.markdown("### Disruption Context")

        st.markdown(
            f"""
            **Provider:** {case["provider"]}  
            **Disruption type:** {case["disruption_type"].replace("_", " ").title()}  
            **Severity:** {case["disruption_severity"].title()}  
            **Current status:** {case["status"]}
            """
        )


        render_provider_status(provider_response)

        st.markdown("### Current Recommended Next Action")

        st.info(case["recommended_next_action"])

        st.markdown("### Provider-Aware Guidance")

        st.info(provider_guidance(provider_response))

    with right_col:
        render_agent_decision_panel(case, policy_result)

    st.divider()

    render_policy_evaluation(policy_result)

    st.divider()

    render_recovery_options(provider_response)  

    st.divider()

    render_decision_history(case["case_id"])

    st.divider()

    render_audit_trail(case["case_id"])      


def main() -> None:
    initialize_database()
    seed_cases_if_empty()
    st.title("Travel Disruption Operations Copilot")

    st.markdown(
        """
        Operations dashboard for prioritizing disrupted travel bookings and guiding agents
        through safe recovery workflows.
        """
    )

    role = st.radio(
        "Workflow view",
        options=["Agent View", "Supervisor View"],
        horizontal=True,
    )    

    cases_df = load_cases()
    cases_df["priority_rank"] = cases_df["disruption_severity"].apply(priority_rank)
    cases_df["priority"] = cases_df["disruption_severity"].apply(priority_label)

    cases_df = cases_df.sort_values(
        by=["priority_rank", "sla_deadline", "departure_time"]
    )

    open_cases = len(cases_df[cases_df["status"] != "RESOLVED"])
    critical_cases = len(cases_df[cases_df["disruption_severity"] == "critical"])
    supervisor_review_cases = len(
        cases_df[
            cases_df["recommended_next_action"]
            .str.lower()
            .str.contains("supervisor|escalate", regex=True)
        ]
    )

    st.divider()

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.metric("Open disruption cases", open_cases)

    with kpi_col2:
        st.metric("Critical cases", critical_cases)

    with kpi_col3:
        st.metric("Needs escalation", supervisor_review_cases)

    with kpi_col4:
        st.metric("Providers affected", cases_df["provider"].nunique())

    st.divider()

    if role == "Agent View":
        st.subheader("Disruption Queue")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            selected_provider = st.selectbox(
                "Provider",
                options=["All"] + sorted(cases_df["provider"].unique().tolist()),
            )

        with filter_col2:
            selected_severity = st.selectbox(
                "Severity",
                options=["All", "critical", "high", "medium", "low"],
            )

        with filter_col3:
            selected_disruption = st.selectbox(
                "Disruption type",
                options=["All"] + sorted(cases_df["disruption_type"].unique().tolist()),
            )

        filtered_df = cases_df.copy()

        if selected_provider != "All":
            filtered_df = filtered_df[filtered_df["provider"] == selected_provider]

        if selected_severity != "All":
            filtered_df = filtered_df[
                filtered_df["disruption_severity"] == selected_severity
            ]

        if selected_disruption != "All":
            filtered_df = filtered_df[
                filtered_df["disruption_type"] == selected_disruption
            ]

        display_df = build_display_queue(filtered_df)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.subheader("Open a Case")

        selected_case_id = st.selectbox(
            "Select a case to inspect",
            options=filtered_df["case_id"].tolist(),
        )

        selected_case = get_case_by_id(selected_case_id)
        render_case_detail(selected_case)

    else:
        render_supervisor_queue(cases_df)
    
    st.divider()

    st.caption(
        "Prototype status: provider dependency responses are mocked to simulate success, timeout, stale data, partial responses, and provider unavailability."
    )


if __name__ == "__main__":
    main()