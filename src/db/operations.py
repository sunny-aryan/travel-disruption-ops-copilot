from datetime import datetime, timezone
from src.workflows.state_transitions import (
    derive_next_status,
    derive_supervisor_next_status,
)

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

def create_supervisor_decision(
    case_id: str,
    supervisor_decision: str,
    rationale: str,
) -> int:
    """Persist supervisor review decision, update case status, and record audit events."""
    created_at = utc_now_iso()
    next_status = derive_supervisor_next_status(supervisor_decision)

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
            INSERT INTO supervisor_decisions (
                case_id,
                supervisor_decision,
                rationale,
                previous_status,
                new_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                supervisor_decision,
                rationale,
                previous_status,
                next_status,
                created_at,
            ),
        )

        supervisor_decision_id = cursor.lastrowid

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
                "supervisor_decision_submitted",
                (
                    f"Supervisor submitted decision '{supervisor_decision}' "
                    f"with rationale."
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

    return int(supervisor_decision_id)


def get_supervisor_decisions_for_case(case_id: str) -> pd.DataFrame:
    """Return supervisor decision history for a case."""
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                supervisor_decision_id,
                case_id,
                supervisor_decision,
                rationale,
                previous_status,
                new_status,
                created_at
            FROM supervisor_decisions
            WHERE case_id = ?
            ORDER BY created_at DESC
            """,
            connection,
            params=(case_id,),
        )

def create_feedback(
    case_id: str,
    recommendation_usefulness: str,
    provider_data_quality: str,
    override_reason: str,
    customer_outcome: str,
    internal_note: str,
) -> int:
    """Persist workflow feedback for a case and record an audit event."""
    created_at = utc_now_iso()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO feedback (
                case_id,
                recommendation_usefulness,
                provider_data_quality,
                override_reason,
                customer_outcome,
                internal_note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                recommendation_usefulness,
                provider_data_quality,
                override_reason,
                customer_outcome,
                internal_note,
                created_at,
            ),
        )

        feedback_id = cursor.lastrowid

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
                "feedback_submitted",
                (
                    "Workflow feedback submitted: "
                    f"recommendation_usefulness='{recommendation_usefulness}', "
                    f"provider_data_quality='{provider_data_quality}', "
                    f"customer_outcome='{customer_outcome}'."
                ),
                created_at,
            ),
        )

        connection.commit()

    return int(feedback_id)


def get_feedback_for_case(case_id: str) -> pd.DataFrame:
    """Return feedback history for a case."""
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                feedback_id,
                case_id,
                recommendation_usefulness,
                provider_data_quality,
                override_reason,
                customer_outcome,
                internal_note,
                created_at
            FROM feedback
            WHERE case_id = ?
            ORDER BY created_at DESC
            """,
            connection,
            params=(case_id,),
        )