"""Sydney weather via Open-Meteo (no API key required).

``OpenMeteoClient`` fetches live data; ``MockWeatherClient`` serves a fixture.
Both return a :class:`WeatherReport`. ``parse_open_meteo`` is a pure function so
the mapping from the API payload can be unit-tested without a network.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from ..config import MOCK_DATA_DIR, Settings
from ..errors import ConnectorError
from ..models import CurrentWeather, DailyForecast, WeatherReport

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

CURRENT_FIELDS = (
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "weather_code",
    "wind_speed_10m",
    "is_day",
)
DAILY_FIELDS = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "precipitation_sum",
    "wind_speed_10m_max",
    "uv_index_max",
)

# WMO weather interpretation codes -> (description, glyph)
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "☀"),
    1: ("Mainly clear", "🌤"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁"),
    45: ("Fog", "🌫"),
    48: ("Depositing rime fog", "🌫"),
    51: ("Light drizzle", "🌦"),
    53: ("Moderate drizzle", "🌦"),
    55: ("Dense drizzle", "🌧"),
    56: ("Light freezing drizzle", "🌧"),
    57: ("Dense freezing drizzle", "🌧"),
    61: ("Slight rain", "🌧"),
    63: ("Moderate rain", "🌧"),
    65: ("Heavy rain", "🌧"),
    66: ("Light freezing rain", "🌧"),
    67: ("Heavy freezing rain", "🌧"),
    71: ("Slight snow", "🌨"),
    73: ("Moderate snow", "🌨"),
    75: ("Heavy snow", "❄"),
    77: ("Snow grains", "🌨"),
    80: ("Slight rain showers", "🌦"),
    81: ("Moderate rain showers", "🌧"),
    82: ("Violent rain showers", "⛈"),
    85: ("Slight snow showers", "🌨"),
    86: ("Heavy snow showers", "❄"),
    95: ("Thunderstorm", "⛈"),
    96: ("Thunderstorm with slight hail", "⛈"),
    99: ("Thunderstorm with heavy hail", "⛈"),
}


def describe_code(code: int) -> str:
    return WMO_CODES.get(int(code), ("Unknown conditions", "?"))[0]


def glyph_for_code(code: int) -> str:
    return WMO_CODES.get(int(code), ("Unknown conditions", "?"))[1]


class WeatherClient(Protocol):
    name: str

    def fetch(self) -> WeatherReport: ...


def parse_open_meteo(payload: dict[str, Any], location: str, timezone_name: str, fetched_at: datetime | None = None) -> WeatherReport:
    """Map an Open-Meteo ``/v1/forecast`` payload to a :class:`WeatherReport`."""
    try:
        cur = payload["current"]
        daily = payload["daily"]
        current = CurrentWeather(
            temperature_c=float(cur["temperature_2m"]),
            apparent_c=float(cur.get("apparent_temperature", cur["temperature_2m"])),
            humidity_pct=int(round(float(cur.get("relative_humidity_2m", 0)))),
            wind_kmh=float(cur.get("wind_speed_10m", 0.0)),
            weather_code=int(cur.get("weather_code", 0)),
            description=describe_code(cur.get("weather_code", 0)),
            is_day=bool(int(cur.get("is_day", 1))),
            observed_at=datetime.fromisoformat(cur["time"]),
        )
        days: list[DailyForecast] = []
        for i, day_str in enumerate(daily["time"]):
            uv = (daily.get("uv_index_max") or [None] * len(daily["time"]))[i]
            days.append(
                DailyForecast(
                    day=date.fromisoformat(day_str),
                    weather_code=int(daily["weather_code"][i]),
                    description=describe_code(daily["weather_code"][i]),
                    tmax_c=float(daily["temperature_2m_max"][i]),
                    tmin_c=float(daily["temperature_2m_min"][i]),
                    precip_prob_pct=int((daily.get("precipitation_probability_max") or [0] * 99)[i] or 0),
                    precip_mm=float((daily.get("precipitation_sum") or [0.0] * 99)[i] or 0.0),
                    wind_max_kmh=float((daily.get("wind_speed_10m_max") or [0.0] * 99)[i] or 0.0),
                    uv_index_max=float(uv) if uv is not None else None,
                )
            )
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ConnectorError(f"Unexpected Open-Meteo payload: {exc!r}") from exc
    return WeatherReport(
        location=location,
        timezone=payload.get("timezone", timezone_name),
        current=current,
        daily=days,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )


class OpenMeteoClient:
    """Live Open-Meteo forecast client."""

    name = "open-meteo"

    def __init__(self, settings: Settings, session: Any | None = None) -> None:
        self.settings = settings
        self._session = session

    def params(self) -> dict[str, Any]:
        s = self.settings
        return {
            "latitude": s.weather_latitude,
            "longitude": s.weather_longitude,
            "current": ",".join(CURRENT_FIELDS),
            "daily": ",".join(DAILY_FIELDS),
            "timezone": s.weather_timezone,
            "forecast_days": s.weather_forecast_days,
            "wind_speed_unit": "kmh",
            "temperature_unit": "celsius",
        }

    def fetch(self) -> WeatherReport:
        session = self._session
        if session is None:
            try:
                import requests
            except ImportError as exc:  # pragma: no cover
                raise ConnectorError("The 'requests' package is required for live weather.") from exc
            session = requests
        try:
            resp = session.get(OPEN_METEO_URL, params=self.params(), timeout=self.settings.request_timeout)
            if getattr(resp, "status_code", 200) >= 400:
                raise ConnectorError(f"Open-Meteo returned HTTP {resp.status_code}: {getattr(resp, 'text', '')[:200]}")
            payload = resp.json()
        except ConnectorError:
            raise
        except Exception as exc:  # noqa: BLE001 - network errors are varied
            raise ConnectorError(f"Open-Meteo request failed: {exc}") from exc
        return parse_open_meteo(payload, self.settings.weather_location_name, self.settings.weather_timezone)


class MockWeatherClient:
    """Serves the bundled Open-Meteo fixture, re-dated to today."""

    name = "mock-weather"

    def __init__(self, settings: Settings, path: Path | None = None, today: date | None = None) -> None:
        self.settings = settings
        self.path = path or MOCK_DATA_DIR / "weather.json"
        self.today = today or date.today()

    def fetch(self) -> WeatherReport:
        try:
            payload = json.loads(Path(self.path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConnectorError(f"Cannot load mock weather from {self.path}: {exc}") from exc
        # Re-date the fixture so "today" in the HUD is always today.
        from datetime import timedelta

        payload["daily"]["time"] = [
            (self.today + timedelta(days=i)).isoformat() for i in range(len(payload["daily"]["time"]))
        ]
        try:
            from zoneinfo import ZoneInfo

            local_now = datetime.now(ZoneInfo(self.settings.weather_timezone))
        except Exception:  # noqa: BLE001
            local_now = datetime.now()
        payload["current"]["time"] = local_now.replace(tzinfo=None, microsecond=0).isoformat(timespec="minutes")
        return parse_open_meteo(payload, self.settings.weather_location_name, self.settings.weather_timezone)


class FailingWeatherClient:
    name = "failing-weather"

    def __init__(self, message: str = "simulated outage") -> None:
        self.message = message

    def fetch(self) -> WeatherReport:
        raise ConnectorError(self.message)


def weather_client_from_settings(settings: Settings) -> WeatherClient:
    return MockWeatherClient(settings) if settings.mock else OpenMeteoClient(settings)
