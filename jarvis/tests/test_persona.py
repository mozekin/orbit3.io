from datetime import date, datetime, timezone

import pytest

from jarvis.models import CurrentWeather, DailyForecast, Signup, SignupReport, Task, TasksDigest, UrgentMessage, WeatherReport
from jarvis.persona import Persona

NOW = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)


def _weather(days):
    cur = CurrentWeather(17.4, 15.9, 68, 14.2, 2, "Partly cloudy", True, NOW)
    return WeatherReport("Sydney, NSW", "Australia/Sydney", cur, days, NOW)


def _day(offset, code=2, desc="Partly cloudy", tmax=21.0, tmin=12.0, rain=10):
    return DailyForecast(date(2026, 9, 5 + offset), code, desc, tmax, tmin, rain, 0.0, 20.0, 5.0)


@pytest.fixture
def persona():
    return Persona(seed=42)


def test_greeting_addresses_mr_ozekin_by_time_of_day(persona):
    assert persona.greeting(NOW.replace(hour=7)).startswith("Good morning, Mr. Ozekin.")
    assert persona.greeting(NOW.replace(hour=13)).startswith("Good afternoon, Mr. Ozekin.")
    assert persona.greeting(NOW.replace(hour=21)).startswith("Good evening, Mr. Ozekin.")


def test_greeting_mentions_simulation_in_mock_mode(persona):
    assert "simulated data" in persona.greeting(NOW, mode="mock")
    assert "simulated data" not in persona.greeting(NOW, mode="live")


def test_never_uses_sir(persona):
    texts = [
        persona.greeting(NOW),
        persona.sign_off(),
        persona.error("weather service", "timeout"),
        persona.signups(SignupReport([], 1, 0, NOW)),
        persona.tasks(TasksDigest([], [], 3, 0, NOW)),
        persona.weather(_weather([_day(0)])),
        persona.acknowledge(),
        persona.say("Bring the car round"),
    ]
    for text in texts:
        assert "Mr. Ozekin" in text, text
        assert " sir" not in text.lower(), text


def test_address_appends_salutation_once(persona):
    assert persona.say("The car is ready.") == "The car is ready, Mr. Ozekin."
    assert persona.say("Yes, Mr. Ozekin.") == "Yes, Mr. Ozekin."
    assert persona.say("No punctuation") == "No punctuation, Mr. Ozekin."


def test_custom_salutation():
    p = Persona(salutation="Dr. Ozekin", seed=1)
    assert "Dr. Ozekin" in p.greeting(NOW)


def test_signups_zero_one_many(persona):
    assert "No new Auravest signups" in persona.signups(SignupReport([], 1, 3, NOW)) or "no new signups" in persona.signups(SignupReport([], 1, 3, NOW))
    one = persona.signups(SignupReport([Signup("Priya Raman", "p@x.com", "Professional", "Northwind")], 1, 1, NOW))
    assert "1 new signup in the last 24 hours" in one
    assert "Priya Raman of Northwind on the Professional plan" in one
    many = [Signup(f"User {i}", f"u{i}@x.com", "Starter") for i in range(5)]
    text = persona.signups(SignupReport(many, 2, 5, NOW))
    assert "5 new signups in the last 2 days" in text
    assert "2 others besides" in text


def test_signups_error_is_narrated(persona):
    text = persona.signups(SignupReport([], 1, 0, NOW, error="HTTP 503"))
    assert "Auravest signup feed" in text and "HTTP 503" in text


def test_tasks_quiet_inbox(persona):
    text = persona.tasks(TasksDigest([], [], 3, 12, NOW))
    assert "Orbit3" in text and "Mr. Ozekin" in text


def test_tasks_lists_urgent_and_tasks(persona):
    digest = TasksDigest(
        tasks=[
            Task("Call Rachel", "Outage", "Rachel Nguyen", "m1", priority="urgent"),
            Task("Send the SOW", "Proposal", "Aisha Patel", "m2", priority="high", due="COB Wednesday"),
            Task("Water the plant", "Misc", "Lucy Bennett", "m3"),
        ],
        urgent=[UrgentMessage("Rachel Nguyen", "URGENT: outage", "it is marked urgent", "m1")],
        lookback_days=3, scanned=5, generated_at=NOW,
    )
    text = persona.tasks(digest)
    assert "There is 1 urgent communication" in text
    assert 'Rachel Nguyen writes regarding "URGENT: outage"' in text
    assert "3 outstanding tasks, 1 of which is marked urgent" in text
    assert "Urgent: Call Rachel (from Rachel Nguyen)." in text
    assert "High priority: Send the SOW, due COB Wednesday (from Aisha Patel)." in text


def test_task_due_not_repeated_when_in_title():
    line = Persona._task_phrase(Task("Send SOW by COB Wednesday", "s", "Aisha", "m", due="COB Wednesday"))
    assert line.count("COB Wednesday") == 1


def test_weather_narration_and_umbrella(persona):
    text = persona.weather(_weather([_day(0), _day(1, 61, "Slight rain", 19, 13, 72), _day(2, 3, "Overcast", 20, 12, 35)]))
    assert "In Sydney it is currently 17 degrees and partly cloudy, feeling like 16 degrees" in text
    assert "72 percent chance of rain" in text
    assert "umbrella" in text.lower() or "rain is likely" in text.lower()
    assert "Sunday" in text


def test_weather_hot_and_civilised(persona):
    hot = persona.weather(_weather([_day(1, 0, "Clear sky", 34, 20, 0)]))
    assert "rather warm" in hot
    calm = persona.weather(_weather([_day(1)]))
    assert "Mr. Ozekin" in calm and "umbrella" not in calm


def test_weather_error(persona):
    report = _weather([])
    report.error = "connection refused"
    assert "weather service" in persona.weather(report)


def test_seed_makes_output_deterministic():
    a = Persona(seed=7)
    b = Persona(seed=7)
    assert [a.sign_off() for _ in range(5)] == [b.sign_off() for _ in range(5)]


def test_error_detail_is_truncated_for_speech(persona):
    text = persona.error("weather service", "x" * 500)
    assert "..." in text and len(text) < 300
