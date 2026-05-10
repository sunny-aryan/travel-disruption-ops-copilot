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


def get_case_by_id(case_id: str) -> dict:
    """Return a single case as a dictionary."""
    cases_df = load_cases()
    matching_cases = cases_df[cases_df["case_id"] == case_id]

    if matching_cases.empty:
        raise ValueError(f"No case found for case_id: {case_id}")

    return matching_cases.iloc[0].to_dict()