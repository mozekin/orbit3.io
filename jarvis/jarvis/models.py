"""Plain data models shared across connectors, modules and the HUD."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


class _Serialisable:
    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))  # type: ignore[call-overload]


# --------------------------------------------------------------------------- mail
@dataclass
class EmailMessage(_Serialisable):
    id: str
    thread_id: str
    sender: str
    to: str
    subject: str
    date: datetime
    snippet: str = ""
    body: str = ""
    labels: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def sender_email(self) -> str:
        return extract_email(self.sender)

    @property
    def sender_name(self) -> str:
        return extract_display_name(self.sender)

    @property
    def text(self) -> str:
        """Subject + body, for keyword scanning."""
        return f"{self.subject}\n{self.body or self.snippet}"


def extract_email(header_value: str) -> str:
    """'Jane Doe <jane@x.com>' -> 'jane@x.com'."""
    value = (header_value or "").strip()
    if "<" in value and ">" in value:
        return value[value.rfind("<") + 1 : value.rfind(">")].strip().lower()
    return value.strip("\"' ").lower()


def extract_display_name(header_value: str) -> str:
    value = (header_value or "").strip()
    if "<" in value:
        name = value[: value.rfind("<")].strip().strip('"').strip()
        if name:
            return name
    email = extract_email(value)
    return email.split("@")[0].replace(".", " ").title() if email else value


# --------------------------------------------------------------------------- auravest
@dataclass
class Signup(_Serialisable):
    name: str
    email: str
    plan: str = ""
    company: str = ""
    signed_up_at: datetime | None = None
    source_message_id: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def display(self) -> str:
        who = self.name or self.email or "an unnamed user"
        if self.company:
            who += f" of {self.company}"
        return who


@dataclass
class SignupReport(_Serialisable):
    signups: list[Signup]
    lookback_days: int
    scanned: int
    generated_at: datetime
    error: str | None = None

    @property
    def count(self) -> int:
        return len(self.signups)


# --------------------------------------------------------------------------- orbit3
@dataclass
class Task(_Serialisable):
    title: str
    source_subject: str
    sender: str
    message_id: str
    priority: str = "normal"  # urgent | high | normal
    due: str | None = None
    received: datetime | None = None


@dataclass
class UrgentMessage(_Serialisable):
    sender: str
    subject: str
    reason: str
    message_id: str
    received: datetime | None = None
    snippet: str = ""


@dataclass
class TasksDigest(_Serialisable):
    tasks: list[Task]
    urgent: list[UrgentMessage]
    lookback_days: int
    scanned: int
    generated_at: datetime
    error: str | None = None

    @property
    def urgent_task_count(self) -> int:
        return sum(1 for t in self.tasks if t.priority == "urgent")


# --------------------------------------------------------------------------- weather
@dataclass
class CurrentWeather(_Serialisable):
    temperature_c: float
    apparent_c: float
    humidity_pct: int
    wind_kmh: float
    weather_code: int
    description: str
    is_day: bool
    observed_at: datetime


@dataclass
class DailyForecast(_Serialisable):
    day: date
    weather_code: int
    description: str
    tmax_c: float
    tmin_c: float
    precip_prob_pct: int
    precip_mm: float
    wind_max_kmh: float
    uv_index_max: float | None = None

    @property
    def weekday(self) -> str:
        return self.day.strftime("%A")


@dataclass
class WeatherReport(_Serialisable):
    location: str
    timezone: str
    current: CurrentWeather
    daily: list[DailyForecast]
    fetched_at: datetime
    source: str = "open-meteo"
    error: str | None = None


# --------------------------------------------------------------------------- briefing
@dataclass
class Section(_Serialisable):
    key: str
    title: str
    spoken: str
    data: Any = None
    error: str | None = None


@dataclass
class Briefing(_Serialisable):
    greeting: str
    sections: list[Section]
    sign_off: str
    generated_at: datetime
    mode: str = "live"

    @property
    def script(self) -> str:
        parts = [self.greeting, *[s.spoken for s in self.sections], self.sign_off]
        return "\n\n".join(p.strip() for p in parts if p and p.strip())
