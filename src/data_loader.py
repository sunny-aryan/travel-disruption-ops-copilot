import json

import pandas as pd

from src.db.connection import get_connection


def load_cases() -> pd.DataFrame:
    """Load disruption cases from local SQLite database."""
    with get_connection() as connection:
        df = pd.read_sql_query(
            """
            SELECT
                case_id,
                booking_id,
                passenger_name,
                provider,
                origin,
                destination,
                departure_time,
                disruption_type,
                disruption_severity,
                passenger_count,
                customer_tier,
                ticket_value_eur,
                special_flags,
                sla_deadline,
                status,
                recommended_next_action,
                created_at,
                updated_at
            FROM cases
            ORDER BY updated_at DESC
            """,
            connection,
        )

    if df.empty:
        return df

    df["departure_time"] = pd.to_datetime(df["departure_time"])
    df["sla_deadline"] = pd.to_datetime(df["sla_deadline"])

    df["special_flags"] = df["special_flags"].apply(
        lambda value: json.loads(value) if isinstance(value, str) else value
    )

    return df


def get_case_by_id(case_id: str) -> dict:
    """Return a single case as a dictionary."""
    cases_df = load_cases()
    matching_cases = cases_df[cases_df["case_id"] == case_id]

    if matching_cases.empty:
        raise ValueError(f"No case found for case_id: {case_id}")

    return matching_cases.iloc[0].to_dict()