from src.db.connection import get_connection


def initialize_database() -> None:
    """Create local SQLite tables if they do not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                selected_action TEXT NOT NULL,
                approval_required INTEGER NOT NULL,
                rationale TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()