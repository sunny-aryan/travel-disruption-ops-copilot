from datetime import datetime

import streamlit as st

from src.data_loader import get_case_by_id, load_cases


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


def render_case_detail(case: dict) -> None:
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

        st.markdown("### Current Recommended Next Action")

        st.info(case["recommended_next_action"])

    with right_col:
        st.markdown("### Agent Decision Panel")

        st.selectbox(
            "Proposed action",
            options=[
                "Investigate recovery options",
                "Prepare customer message",
                "Escalate to supervisor",
                "Wait for provider update",
                "Mark as resolved",
            ],
            key=f"action_{case['case_id']}",
        )

        st.text_area(
            "Agent rationale",
            placeholder="Explain why this action is appropriate...",
            key=f"rationale_{case['case_id']}",
        )

        st.button(
            "Submit decision",
            disabled=True,
            help="Decision persistence will be added in a later milestone.",
        )

        st.caption(
            "This panel is currently a UX placeholder. Future milestones will validate actions, persist decisions, and update case state."
        )


def main() -> None:
    st.title("Travel Disruption Operations Copilot")

    st.markdown(
        """
        Operations dashboard for prioritizing disrupted travel bookings and guiding agents
        through safe recovery workflows.
        """
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

    st.divider()

    st.info(
        "Next milestone: add mock provider recovery options and external dependency states such as success, timeout, stale data, and provider unavailable."
    )


if __name__ == "__main__":
    main()