"""Weather module: wraps a weather client and never raises - errors are carried
in the report so the persona can narrate them."""
from __future__ import annotations

from datetime import datetime, timezone

from ..config import Settings
from ..connectors.weather import WeatherClient
from ..errors import JarvisError
from ..models import CurrentWeather, WeatherReport


class WeatherService:
    def __init__(self, client: WeatherClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    def fetch(self) -> WeatherReport:
        try:
            report = self.client.fetch()
        except JarvisError as exc:
            now = datetime.now(timezone.utc)
            placeholder = CurrentWeather(0.0, 0.0, 0, 0.0, 0, "Unavailable", True, now)
            return WeatherReport(
                location=self.settings.weather_location_name,
                timezone=self.settings.weather_timezone,
                current=placeholder,
                daily=[],
                fetched_at=now,
                source=getattr(self.client, "name", "weather"),
                error=str(exc),
            )
        report.daily = report.daily[: self.settings.weather_forecast_days]
        return report
