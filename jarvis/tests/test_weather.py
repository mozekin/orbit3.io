import json
from datetime import date

import pytest

from jarvis.config import MOCK_DATA_DIR, Settings
from jarvis.connectors.weather import (
    OPEN_METEO_URL,
    FailingWeatherClient,
    MockWeatherClient,
    OpenMeteoClient,
    describe_code,
    glyph_for_code,
    parse_open_meteo,
)
from jarvis.errors import ConnectorError
from jarvis.modules.weather_report import WeatherService

from conftest import FakeResponse, FakeSession

PAYLOAD = json.loads((MOCK_DATA_DIR / "weather.json").read_text())


def test_wmo_code_mapping():
    assert describe_code(0) == "Clear sky"
    assert describe_code(61) == "Slight rain"
    assert describe_code(999) == "Unknown conditions"
    assert glyph_for_code(95) == "⛈"


def test_parse_open_meteo_payload():
    report = parse_open_meteo(PAYLOAD, "Sydney, NSW", "Australia/Sydney")
    assert report.location == "Sydney, NSW" and report.timezone == "Australia/Sydney"
    assert report.current.temperature_c == 17.4 and report.current.description == "Partly cloudy"
    assert report.current.humidity_pct == 68 and report.current.is_day
    assert [d.day for d in report.daily] == [date(2026, 9, 5), date(2026, 9, 6), date(2026, 9, 7)]
    assert report.daily[1].description == "Slight rain" and report.daily[1].precip_prob_pct == 72
    assert report.daily[0].weekday == "Saturday"
    assert report.daily[2].uv_index_max == 4.8


def test_parse_open_meteo_rejects_bad_payload():
    with pytest.raises(ConnectorError):
        parse_open_meteo({"current": {}}, "x", "y")


def test_open_meteo_client_builds_request():
    settings = Settings(weather_forecast_days=3)
    session = FakeSession(FakeResponse(200, PAYLOAD))
    report = OpenMeteoClient(settings, session=session).fetch()
    call = session.calls[0]
    assert call["url"] == OPEN_METEO_URL
    assert call["params"]["latitude"] == -33.8688 and call["params"]["longitude"] == 151.2093
    assert call["params"]["timezone"] == "Australia/Sydney" and call["params"]["forecast_days"] == 3
    assert "weather_code" in call["params"]["current"] and "precipitation_probability_max" in call["params"]["daily"]
    assert report.current.temperature_c == 17.4


def test_open_meteo_client_http_error():
    session = FakeSession(FakeResponse(429, text="rate limited"))
    with pytest.raises(ConnectorError, match="HTTP 429"):
        OpenMeteoClient(Settings(), session=session).fetch()


def test_open_meteo_client_network_error():
    session = FakeSession(FakeResponse(200, PAYLOAD), error=OSError("no route"))
    with pytest.raises(ConnectorError, match="no route"):
        OpenMeteoClient(Settings(), session=session).fetch()


def test_mock_client_redates_to_today():
    today = date(2030, 1, 1)
    report = MockWeatherClient(Settings(mock=True), today=today).fetch()
    assert [d.day for d in report.daily] == [date(2030, 1, 1), date(2030, 1, 2), date(2030, 1, 3)]


def test_weather_service_wraps_errors():
    report = WeatherService(FailingWeatherClient("dns failure"), Settings()).fetch()
    assert report.error == "dns failure" and report.daily == [] and report.location == "Sydney, NSW"


def test_weather_service_trims_days():
    report = WeatherService(MockWeatherClient(Settings(mock=True)), Settings(weather_forecast_days=2)).fetch()
    assert len(report.daily) == 2
