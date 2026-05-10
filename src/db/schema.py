from src.db.connection import get_connection


def initialize_database() -> None:
    """Create local SQLite tables if they do not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                booking_id TEXT NOT NULL,
                passenger_name TEXT NOT NULL,
                provider TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                disruption_type TEXT NOT NULL,
                disruption_severity TEXT NOT NULL,
                passenger_count INTEGER NOT NULL,
                customer_tier TEXT NOT NULL,
                ticket_value_eur REAL NOT NULL,
                special_flags TEXT NOT NULL,
                sla_deadline TEXT NOT NULL,
                status TEXT NOT NULL,
                recommended_next_action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

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