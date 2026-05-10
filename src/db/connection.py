import sqlite3
from pathlib import Path


DB_PATH = Path("data/disruption_ops.db")


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection for the local workflow database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection