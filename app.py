import streamlit as st

from src.data_loader import load_cases


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

    display_df = filtered_df[
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

    display_df = display_df[
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

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "Next milestone: add a case detail view where agents can inspect one disrupted booking, "
        "see passenger impact, and evaluate recovery options."
    )


if __name__ == "__main__":
    main()