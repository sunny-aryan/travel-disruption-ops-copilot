from typing import Any

import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 5


CITY_COORDINATES: dict[str, dict[str, float]] = {
    "Berlin": {"latitude": 52.52, "longitude": 13.405},
    "Munich": {"latitude": 48.137, "longitude": 11.575},
    "Hamburg": {"latitude": 53.551, "longitude": 9.993},
    "Amsterdam": {"latitude": 52.3676, "longitude": 4.9041},
    "Zurich": {"latitude": 47.3769, "longitude": 8.5417},
    "Milan": {"latitude": 45.4642, "longitude": 9.19},
    "Copenhagen": {"latitude": 55.6761, "longitude": 12.5683},
    "Stockholm": {"latitude": 59.3293, "longitude": 18.0686},
    "Paris": {"latitude": 48.8566, "longitude": 2.3522},
    "Brussels": {"latitude": 50.8503, "longitude": 4.3517},
    "Prague": {"latitude": 50.0755, "longitude": 14.4378},
    "Vienna": {"latitude": 48.2082, "longitude": 16.3738},
}


def get_city_coordinates(city: str) -> dict[str, float] | None:
    """Return configured coordinates for a supported city."""
    return CITY_COORDINATES.get(city)


def classify_weather_risk(
    precipitation_mm: float,
    wind_speed_kmh: float,
) -> str:
    """Classify simple operational weather risk."""
    if precipitation_mm >= 10 or wind_speed_kmh >= 50:
        return "high"

    if precipitation_mm >= 3 or wind_speed_kmh >= 30:
        return "medium"

    return "low"


def weather_risk_label(risk: str) -> str:
    labels = {
        "high": "🔴 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low",
        "unknown": "⚪ Unknown",
    }

    return labels.get(risk, "⚪ Unknown")


def build_weather_fallback(city: str, reason: str) -> dict[str, Any]:
    """Return degraded weather response when API data cannot be fetched."""
    return {
        "city": city,
        "api_status": "degraded",
        "source": "Open-Meteo",
        "temperature_c": None,
        "precipitation_mm": None,
        "wind_speed_kmh": None,
        "weather_risk": "unknown",
        "message": reason,
    }


def get_current_weather(city: str) -> dict[str, Any]:
    """
    Fetch current weather from Open-Meteo for a configured city.

    Weather is used as contextual enrichment, not as the sole basis for workflow decisions.
    """
    coordinates = get_city_coordinates(city)

    if coordinates is None:
        return build_weather_fallback(
            city=city,
            reason="City coordinates are not configured for weather enrichment.",
        )

    params = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "current": "temperature_2m,precipitation,wind_speed_10m",
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        current = payload.get("current", {})

        temperature_c = current.get("temperature_2m")
        precipitation_mm = current.get("precipitation")
        wind_speed_kmh = current.get("wind_speed_10m")

        if (
            temperature_c is None
            or precipitation_mm is None
            or wind_speed_kmh is None
        ):
            return build_weather_fallback(
                city=city,
                reason="Weather API response was missing expected current-weather fields.",
            )

        risk = classify_weather_risk(
            precipitation_mm=float(precipitation_mm),
            wind_speed_kmh=float(wind_speed_kmh),
        )

        return {
            "city": city,
            "api_status": "healthy",
            "source": "Open-Meteo",
            "temperature_c": float(temperature_c),
            "precipitation_mm": float(precipitation_mm),
            "wind_speed_kmh": float(wind_speed_kmh),
            "weather_risk": risk,
            "message": "Weather enrichment loaded from Open-Meteo.",
        }

    except requests.Timeout:
        return build_weather_fallback(
            city=city,
            reason="Weather API request timed out.",
        )

    except requests.RequestException as exc:
        return build_weather_fallback(
            city=city,
            reason=f"Weather API request failed: {exc}",
        )

    except ValueError:
        return build_weather_fallback(
            city=city,
            reason="Weather API response could not be parsed.",
        )