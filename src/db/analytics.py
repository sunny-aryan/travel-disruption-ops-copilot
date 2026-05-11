import pandas as pd

from src.db.connection import get_connection


def get_feedback_analytics() -> pd.DataFrame:
    """Return feedback records joined with case context for analytics."""
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                feedback.feedback_id,
                feedback.case_id,
                feedback.recommendation_usefulness,
                feedback.provider_data_quality,
                feedback.override_reason,
                feedback.customer_outcome,
                feedback.internal_note,
                feedback.created_at,
                cases.provider,
                cases.disruption_type,
                cases.disruption_severity,
                cases.customer_tier,
                cases.status
            FROM feedback
            LEFT JOIN cases
                ON feedback.case_id = cases.case_id
            ORDER BY feedback.created_at DESC
            """,
            connection,
        )


def get_case_status_summary() -> pd.DataFrame:
    """Return case count by current workflow status."""
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                status,
                COUNT(*) AS case_count
            FROM cases
            GROUP BY status
            ORDER BY case_count DESC
            """,
            connection,
        )


def get_provider_case_summary() -> pd.DataFrame:
    """Return case count by provider and severity."""
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                provider,
                disruption_severity,
                COUNT(*) AS case_count
            FROM cases
            GROUP BY provider, disruption_severity
            ORDER BY provider, case_count DESC
            """,
            connection,
        )