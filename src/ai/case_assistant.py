from typing import Any

from openai import OpenAI

from src.config import get_openai_api_key, is_openai_configured


AI_MODEL = "gpt-5.5"


def build_fallback_case_summary(
    case: dict[str, Any],
    provider_response: dict[str, Any],
    policy_result: dict[str, Any],
) -> str:
    """Return deterministic fallback summary when AI is unavailable."""
    route = f"{case['origin']} → {case['destination']}"
    disruption = case["disruption_type"].replace("_", " ")
    provider_state = provider_response.get("response_state", "unknown")
    allowed_actions = ", ".join(policy_result.get("allowed_actions", [])) or "none"
    approval_actions = (
        ", ".join(policy_result.get("supervisor_required_actions", [])) or "none"
    )
    blocked_actions = ", ".join(policy_result.get("blocked_actions", [])) or "none"

    return (
        f"{case['case_id']} is a {case['disruption_severity']} {disruption} case "
        f"for passenger {case['passenger_name']} on route {route}. "
        f"The provider response state is {provider_state}. "
        f"Directly allowed actions: {allowed_actions}. "
        f"Actions requiring supervisor approval: {approval_actions}. "
        f"Blocked actions: {blocked_actions}."
    )


def build_fallback_passenger_message(
    case: dict[str, Any],
    provider_response: dict[str, Any],
) -> str:
    """Return deterministic fallback passenger message when AI is unavailable."""
    disruption = case["disruption_type"].replace("_", " ")
    provider_state = provider_response.get("response_state", "unknown")

    if provider_state in ["provider_unavailable", "timeout"]:
        return (
            f"Hello {case['passenger_name']}, we are sorry for the disruption to your "
            f"journey from {case['origin']} to {case['destination']}. We are currently "
            "waiting for updated information from the travel provider and will update "
            "you as soon as reliable options are available."
        )

    return (
        f"Hello {case['passenger_name']}, we are sorry for the {disruption} affecting "
        f"your journey from {case['origin']} to {case['destination']}. Our operations "
        "team is reviewing available recovery options and will follow up with the safest "
        "next step."
    )


def build_case_context(
    case: dict[str, Any],
    provider_response: dict[str, Any],
    policy_result: dict[str, Any],
    weather_context: dict[str, Any] | None = None,
) -> str:
    """Build compact context for the LLM."""
    options = provider_response.get("options", [])

    return f"""
Case:
- Case ID: {case["case_id"]}
- Passenger: {case["passenger_name"]}
- Route: {case["origin"]} to {case["destination"]}
- Disruption type: {case["disruption_type"]}
- Disruption severity: {case["disruption_severity"]}
- Passenger count: {case["passenger_count"]}
- Customer tier: {case["customer_tier"]}
- Ticket value EUR: {case["ticket_value_eur"]}
- Special flags: {case["special_flags"]}
- Current status: {case["status"]}

Provider response:
- Provider status: {provider_response.get("provider_status")}
- Response state: {provider_response.get("response_state")}
- Data freshness minutes: {provider_response.get("data_freshness_minutes")}
- Provider message: {provider_response.get("provider_message")}
- Recovery options: {options}

Policy evaluation:
- Policy version: {policy_result.get("policy_version")}
- Allowed actions: {policy_result.get("allowed_actions")}
- Supervisor-required actions: {policy_result.get("supervisor_required_actions")}
- Blocked actions: {policy_result.get("blocked_actions")}
- Policy reasons: {policy_result.get("reasons")}

Weather context:
{weather_context if weather_context else "Not provided"}
"""


def generate_ai_case_assistance(
    case: dict[str, Any],
    provider_response: dict[str, Any],
    policy_result: dict[str, Any],
    weather_context: dict[str, Any] | None = None,
    force_fallback: bool = False,
) -> dict[str, str]:
    """
    Generate an operational brief and passenger message draft.

    AI output is advisory only. It must not approve actions, override policy,
    execute workflow transitions, or invent unavailable recovery options.
    """
    fallback_summary = build_fallback_case_summary(
        case=case,
        provider_response=provider_response,
        policy_result=policy_result,
    )
    fallback_message = build_fallback_passenger_message(
        case=case,
        provider_response=provider_response,
    )

    if force_fallback:
        return {
            "source": "deterministic_fallback",
            "operational_brief": fallback_summary,
            "passenger_message": fallback_message,
            "status": "AI fallback forced by demo control.",
        }

    if not is_openai_configured():
        return {
            "source": "deterministic_fallback",
            "operational_brief": fallback_summary,
            "passenger_message": fallback_message,
            "status": "OpenAI API key not configured. Fallback output used.",
        }

    client = OpenAI(api_key=get_openai_api_key())

    instructions = """
You are an operations assistant for a travel disruption workflow.

Your role:
- Summarize the case for a human travel operations agent.
- Draft a clear, empathetic passenger-facing message.

Hard boundaries:
- Do not approve refunds.
- Do not approve rebookings.
- Do not override deterministic policy.
- Do not claim that an action has been completed.
- Do not invent recovery options.
- If provider data is stale, missing, partial, unavailable, or timed out, explicitly mention uncertainty.
- Keep the operational brief concise and actionable.
- Keep the passenger message empathetic, factual, and non-committal unless options are clearly available.

Return exactly this format:

OPERATIONAL_BRIEF:
<brief>

PASSENGER_MESSAGE:
<message>
"""

    input_text = build_case_context(
        case=case,
        provider_response=provider_response,
        policy_result=policy_result,
        weather_context=weather_context,
    )

    try:
        response = client.responses.create(
            model=AI_MODEL,
            instructions=instructions,
            input=input_text,
        )

        output_text = response.output_text.strip()

        operational_brief = output_text
        passenger_message = fallback_message

        if "PASSENGER_MESSAGE:" in output_text:
            parts = output_text.split("PASSENGER_MESSAGE:", maxsplit=1)
            operational_brief = parts[0].replace("OPERATIONAL_BRIEF:", "").strip()
            passenger_message = parts[1].strip()

        return {
            "source": "openai",
            "operational_brief": operational_brief,
            "passenger_message": passenger_message,
            "status": "AI assistance generated with OpenAI.",
        }

    except Exception as exc:
        return {
            "source": "deterministic_fallback",
            "operational_brief": fallback_summary,
            "passenger_message": fallback_message,
            "status": f"OpenAI request failed. Fallback output used. Error: {exc}",
        }