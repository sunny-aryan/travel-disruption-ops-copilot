import json
from pathlib import Path

from src.db.connection import get_connection
from src.db.operations import utc_now_iso


SEED_CASES_PATH = Path("data/seed_cases.json")


def cases_table_has_data() -> bool:
    """Return whether the cases table already contains records."""
    with get_connection() as connection:
        result = connection.execute("SELECT COUNT(*) AS count FROM cases").fetchone()
        return result["count"] > 0


def seed_cases_if_empty() -> None:
    """Seed initial cases from JSON if the cases table is empty."""
    if cases_table_has_data():
        return

    if not SEED_CASES_PATH.exists():
        raise FileNotFoundError(f"Seed cases file not found: {SEED_CASES_PATH}")

    with SEED_CASES_PATH.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    now = utc_now_iso()

    with get_connection() as connection:
        for case in cases:
            connection.execute(
                """
                INSERT INTO cases (
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case["case_id"],
                    case["booking_id"],
                    case["passenger_name"],
                    case["provider"],
                    case["origin"],
                    case["destination"],
                    case["departure_time"],
                    case["disruption_type"],
                    case["disruption_severity"],
                    case["passenger_count"],
                    case["customer_tier"],
                    case["ticket_value_eur"],
                    json.dumps(case["special_flags"]),
                    case["sla_deadline"],
                    case["status"],
                    case["recommended_next_action"],
                    now,
                    now,
                ),
            )

        connection.commit()