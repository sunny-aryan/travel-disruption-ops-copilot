import json
from pathlib import Path
from typing import Any


PROVIDER_RESPONSES_PATH = Path("data/provider_responses.json")


def load_provider_responses() -> dict[str, Any]:
    """Load mocked provider responses from local JSON."""
    if not PROVIDER_RESPONSES_PATH.exists():
        raise FileNotFoundError(
            f"Provider response file not found: {PROVIDER_RESPONSES_PATH}"
        )

    with PROVIDER_RESPONSES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_recovery_options(case_id: str) -> dict[str, Any]:
    """
    Simulate fetching recovery options from an external travel provider.

    In the MVP, this reads from local JSON, but it intentionally models the shape
    of an unreliable external dependency.
    """
    responses = load_provider_responses()

    if case_id not in responses:
        return {
            "provider_status": "unknown",
            "response_state": "missing_response",
            "data_freshness_minutes": None,
            "provider_message": "No provider response configured for this case.",
            "options": [],
        }

    return responses[case_id]


def is_provider_data_fresh(provider_response: dict[str, Any]) -> bool:
    """Return whether provider data is fresh enough for normal agent action."""
    freshness = provider_response.get("data_freshness_minutes")

    if freshness is None:
        return False

    return freshness <= 15


def provider_status_label(provider_status: str) -> str:
    labels = {
        "healthy": "🟢 Healthy",
        "degraded": "🟡 Degraded",
        "unavailable": "🔴 Unavailable",
        "timeout": "🔴 Timeout",
        "unknown": "⚪ Unknown",
    }

    return labels.get(provider_status, "⚪ Unknown")


def response_state_label(response_state: str) -> str:
    labels = {
        "success": "🟢 Success",
        "partial_response": "🟡 Partial response",
        "stale_data": "🟠 Stale data",
        "provider_unavailable": "🔴 Provider unavailable",
        "timeout": "🔴 Timeout",
        "missing_response": "⚪ Missing response",
    }

    return labels.get(response_state, "⚪ Unknown")