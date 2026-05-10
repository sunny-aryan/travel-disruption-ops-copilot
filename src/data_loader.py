import json
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/seed_cases.json")


def load_cases() -> pd.DataFrame:
    """Load synthetic disruption cases from local seed data."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Seed data file not found: {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    df = pd.DataFrame(cases)

    df["departure_time"] = pd.to_datetime(df["departure_time"])
    df["sla_deadline"] = pd.to_datetime(df["sla_deadline"])

    return df