"""Assemble the briefing from the feature modules.

Every section is isolated: a failing connector produces an error section that
J.A.R.V.I.S. narrates politely instead of aborting the whole run.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Sequence

from .config import Settings
from .connectors.gmail import MailSource, mail_source_from_settings
from .connectors.weather import WeatherClient, weather_client_from_settings
from .errors import JarvisError
from .models import Briefing, Section
from .modules.auravest import AuravestSignupService
from .modules.orbit3_digest import TaskDigestService
from .modules.weather_report import WeatherService
from .persona import Persona

ALL_SECTIONS: tuple[str, ...] = ("signups", "tasks", "weather")
SECTION_TITLES = {
    "signups": "AURAVEST SIGNUPS",
    "tasks": "ORBIT3 TASK DIGEST",
    "weather": "SYDNEY WEATHER",
}


class BriefingAssembler:
    def __init__(
        self,
        settings: Settings,
        persona: Persona | None = None,
        mail_factory: Callable[[], MailSource] | None = None,
        weather_factory: Callable[[], WeatherClient] | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        self.settings = settings
        self.persona = persona or Persona(settings.principal_name)
        self._mail_factory = mail_factory or (lambda: mail_source_from_settings(settings))
        self._weather_factory = weather_factory or (lambda: weather_client_from_settings(settings))
        self._mail: MailSource | None = None
        self._progress = on_progress or (lambda _msg: None)

    def _mail_source(self) -> MailSource:
        if self._mail is None:
            self._mail = self._mail_factory()
        return self._mail

    # ---- sections
    def signups_section(self) -> Section:
        title = SECTION_TITLES["signups"]
        try:
            report = AuravestSignupService(self._mail_source(), self.settings).fetch()
        except JarvisError as exc:
            return Section("signups", title, self.persona.error("Auravest signup feed", str(exc)), None, str(exc))
        return Section("signups", title, self.persona.signups(report), report, report.error)

    def tasks_section(self) -> Section:
        title = SECTION_TITLES["tasks"]
        try:
            digest = TaskDigestService(self._mail_source(), self.settings).fetch()
        except JarvisError as exc:
            return Section("tasks", title, self.persona.error("Orbit3 mailbox", str(exc)), None, str(exc))
        return Section("tasks", title, self.persona.tasks(digest), digest, digest.error)

    def weather_section(self) -> Section:
        title = SECTION_TITLES["weather"]
        try:
            report = WeatherService(self._weather_factory(), self.settings).fetch()
        except JarvisError as exc:
            return Section("weather", title, self.persona.error("weather service", str(exc)), None, str(exc))
        return Section("weather", title, self.persona.weather(report), report, report.error)

    def build(self, sections: Sequence[str] = ALL_SECTIONS, now: datetime | None = None) -> Briefing:
        now = now or datetime.now(timezone.utc)
        builders = {
            "signups": self.signups_section,
            "tasks": self.tasks_section,
            "weather": self.weather_section,
        }
        out: list[Section] = []
        for key in sections:
            if key not in builders:
                raise JarvisError(f"Unknown section '{key}'. Choose from: {', '.join(ALL_SECTIONS)}")
            self._progress(SECTION_TITLES[key])
            out.append(builders[key]())
        mode = "mock" if self.settings.mock else "live"
        local_now = now
        try:
            from zoneinfo import ZoneInfo

            local_now = now.astimezone(ZoneInfo(self.settings.weather_timezone))
        except Exception:  # noqa: BLE001
            pass
        return Briefing(
            greeting=self.persona.greeting(local_now, mode=mode),
            sections=out,
            sign_off=self.persona.sign_off(),
            generated_at=now,
            mode=mode,
        )
