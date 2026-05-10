from datetime import datetime, timezone

import pandas as pd

from src.db.connection import get_connection


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def create_decision(
    case_id: str,
    selected_action: str,
    approval_required: bool,
    rationale: str,
    policy_version: str,
) -> int:
    """Persist an agent decision and corresponding audit event."""
    created_at = utc_now_iso()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO decisions (
                case_id,
                selected_action,
                approval_required,
                rationale,
                policy_version,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                selected_action,
                int(approval_required),
                rationale,
                policy_version,
                created_at,
            ),
        )

        decision_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO audit_events (
                case_id,
                event_type,
                event_description,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                case_id,
                "decision_submitted",
                (
                    f"Agent submitted action '{selected_action}' "
                    f"with approval_required={approval_required}."
                ),
                created_at,
            ),
        )

        connection.commit()

    return int(decision_id)


def get_decisions_for_case(case_id: str) -> pd.DataFrame:
    """Return decision history for a case."""
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                decision_id,
                case_id,
                selected_action,
                approval_required,
                rationale,
                policy_version,
                created_at
            FROM decisions
            WHERE case_id = ?
            ORDER BY created_at DESC
            """,
            connection,
            params=(case_id,),
        )


def get_audit_events_for_case(case_id: str) -> pd.DataFrame:
    """Return audit events for a case."""
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                event_id,
                case_id,
                event_type,
                event_description,
                created_at
            FROM audit_events
            WHERE case_id = ?
            ORDER BY created_at DESC
            """,
            connection,
            params=(case_id,),
        )