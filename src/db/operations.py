from datetime import datetime, timezone

import pandas as pd

from src.db.connection import get_connection
from src.workflows.state_transitions import derive_next_status


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def update_case_status(case_id: str, new_status: str) -> None:
    """Update persisted case workflow status."""
    updated_at = utc_now_iso()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE cases
            SET status = ?, updated_at = ?
            WHERE case_id = ?
            """,
            (new_status, updated_at, case_id),
        )

        connection.commit()


def create_decision(
    case_id: str,
    selected_action: str,
    approval_required: bool,
    rationale: str,
    policy_version: str,
) -> int:
    """Persist an agent decision, update case status, and record audit events."""
    created_at = utc_now_iso()
    next_status = derive_next_status(selected_action, approval_required)

    with get_connection() as connection:
        current_case = connection.execute(
            """
            SELECT status
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        previous_status = current_case["status"] if current_case else "UNKNOWN"

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
            UPDATE cases
            SET status = ?, updated_at = ?
            WHERE case_id = ?
            """,
            (next_status, created_at, case_id),
        )

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
                "case_status_changed",
                f"Case status changed from '{previous_status}' to '{next_status}'.",
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