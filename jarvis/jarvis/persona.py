"""The J.A.R.V.I.S. persona.

Cultured, unfailingly polite, quietly amused. Everything spoken to the principal
passes through here so the tone stays consistent: measured British phrasing,
dry understatement, and the salutation "Mr. Ozekin" - never "sir".
"""
from __future__ import annotations

import random
from datetime import date, datetime
from typing import Iterable, Sequence

from .models import DailyForecast, Signup, SignupReport, Task, TasksDigest, UrgentMessage, WeatherReport

SALUTATION = "Mr. Ozekin"


def _join(items: Sequence[str]) -> str:
    """Oxford-comma-free, butler-approved list joining."""
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _plural(n: int, singular: str, plural: str | None = None) -> str:
    return singular if n == 1 else (plural or singular + "s")


def _describe_temp(value: float) -> str:
    return f"{round(value)} degrees"


class Persona:
    """Composes everything J.A.R.V.I.S. says.

    ``seed`` makes the choice between alternative phrasings deterministic, which
    keeps tests stable; by default it varies by calendar day so the briefing
    doesn't sound identical every morning.
    """

    def __init__(self, salutation: str = SALUTATION, seed: int | None = None) -> None:
        self.salutation = salutation
        self._rng = random.Random(seed if seed is not None else date.today().toordinal())

    # ------------------------------------------------------------------ helpers
    def _pick(self, options: Sequence[str]) -> str:
        return self._rng.choice(list(options))

    def address(self, text: str) -> str:
        """Append the salutation to a sentence if it isn't already present."""
        text = text.strip()
        if self.salutation in text:
            return text
        if text.endswith((".", "!", "?")):
            return f"{text[:-1]}, {self.salutation}{text[-1]}"
        return f"{text}, {self.salutation}."

    # ------------------------------------------------------------------ framing
    def time_of_day(self, now: datetime) -> str:
        hour = now.hour
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 18:
            return "afternoon"
        return "evening"

    def greeting(self, now: datetime, mode: str = "live") -> str:
        opener = f"Good {self.time_of_day(now)}, {self.salutation}."
        follow = self._pick(
            [
                "All systems are online and your briefing is prepared.",
                "Systems are nominal. I have taken the liberty of assembling your briefing.",
                "The house is in order and I have your briefing ready, as promised.",
                "Everything is running within acceptable parameters. Shall we begin?",
            ]
        )
        if mode == "mock":
            follow += " Do note that I am operating on simulated data this session, so any resemblance to reality is purely coincidental."
        return f"{opener} {follow}"

    def sign_off(self) -> str:
        return self._pick(
            [
                f"That concludes the briefing, {self.salutation}. I shall be here, as ever.",
                f"That is everything for now, {self.salutation}. Do try to enjoy the day; I am told it is customary.",
                f"Briefing complete, {self.salutation}. I will alert you the moment anything requires your attention.",
                f"That is all for the present, {self.salutation}. I remain, as always, at your service.",
            ]
        )

    def error(self, service: str, detail: str = "") -> str:
        line = self._pick(
            [
                f"I regret to report that the {service} is not responding at present, {self.salutation}.",
                f"The {service} appears to be sulking, {self.salutation}. I am unable to retrieve it just now.",
                f"Unfortunately the {service} declined to cooperate, {self.salutation}.",
            ]
        )
        if detail:
            detail = detail.strip().rstrip(".")
            if len(detail) > 140:  # keep the spoken version civilised; the HUD shows it in full
                detail = detail[:137].rstrip() + "..."
            line += f" The fault reads: {detail}. I have logged it."
        return line

    # ------------------------------------------------------------------ auravest
    def signups(self, report: SignupReport) -> str:
        window = "24 hours" if report.lookback_days == 1 else f"{report.lookback_days} days"
        if report.error:
            return self.error("Auravest signup feed", report.error)
        n = report.count
        if n == 0:
            return self._pick(
                [
                    f"No new Auravest signups in the last {window}, {self.salutation}. I shall endeavour not to take it personally.",
                    f"Auravest reports no new signups over the past {window}, {self.salutation}. The servers, at least, are enjoying the rest.",
                ]
            )
        lead = f"Auravest has {n} new {_plural(n, 'signup')} in the last {window}, {self.salutation}."
        details = [self._signup_phrase(s) for s in report.signups[:3]]
        body = " " + "; ".join(details) + "." if details else ""
        if n > 3:
            body += f" And {n - 3} {_plural(n - 3, 'other', 'others')} besides, which I have listed on the display."
        tail = self._pick(
            [
                " A most encouraging trend, though I would caution against redecorating just yet.",
                " Growth, it seems, is afoot.",
                " I have filed the details for your review.",
            ]
        ) if n >= 3 else ""
        return lead + body + tail

    @staticmethod
    def _signup_phrase(s: Signup) -> str:
        phrase = s.display
        if s.plan:
            phrase += f" on the {s.plan} plan"
        return phrase

    # ------------------------------------------------------------------ orbit3
    def tasks(self, digest: TasksDigest) -> str:
        if digest.error:
            return self.error("Orbit3 mailbox", digest.error)
        n_tasks = len(digest.tasks)
        n_urgent = len(digest.urgent)
        if n_tasks == 0 and n_urgent == 0:
            return self._pick(
                [
                    f"Turning to Orbit3: your inbox is, remarkably, quiet, {self.salutation}. I checked twice.",
                    f"On the Orbit3 front there is nothing outstanding, {self.salutation}. I would savour the moment.",
                ]
            )
        parts: list[str] = [f"Turning to Orbit3, {self.salutation}."]
        if n_urgent:
            parts.append(
                f"There {'is' if n_urgent == 1 else 'are'} {n_urgent} urgent {_plural(n_urgent, 'communication')} requiring your attention."
            )
            for u in digest.urgent[:3]:
                parts.append(self._urgent_phrase(u))
        if n_tasks:
            urgent_tasks = digest.urgent_task_count
            summary = f"You have {n_tasks} outstanding {_plural(n_tasks, 'task')}"
            if urgent_tasks:
                summary += f", {urgent_tasks} of {'which is' if urgent_tasks == 1 else 'which are'} marked urgent"
            parts.append(summary + ".")
            for t in digest.tasks[:4]:
                parts.append(self._task_phrase(t))
            if n_tasks > 4:
                parts.append(f"The remaining {n_tasks - 4} are on the display.")
        closing = self._pick(
            [
                "I would suggest the urgent items first, though naturally the order is yours.",
                "Nothing there that a strong coffee will not see off.",
                "I have taken the liberty of ordering them by priority.",
            ]
        ) if n_urgent or digest.urgent_task_count else ""
        return " ".join(p for p in parts + [closing] if p)

    @staticmethod
    def _urgent_phrase(u: UrgentMessage) -> str:
        return f"{u.sender} writes regarding \"{u.subject.strip()}\"; flagged because {u.reason}."

    @staticmethod
    def _task_phrase(t: Task) -> str:
        line = t.title.strip().rstrip(".")
        if t.due and t.due.lower() not in line.lower():
            line += f", due {t.due}"
        if t.priority == "urgent":
            line = "Urgent: " + line
        elif t.priority == "high":
            line = "High priority: " + line
        return line + f" (from {t.sender})."

    # ------------------------------------------------------------------ weather
    def weather(self, report: WeatherReport) -> str:
        if report.error:
            return self.error("weather service", report.error)
        c = report.current
        city = report.location.split(",")[0].strip()
        now_line = (
            f"In {city} it is currently {_describe_temp(c.temperature_c)} and {c.description.lower()}, "
            f"feeling like {_describe_temp(c.apparent_c)}, with humidity at {c.humidity_pct} percent "
            f"and a wind of {round(c.wind_kmh)} kilometres per hour."
        )
        outlook = self._outlook(report.daily)
        advice = self._weather_advice(report.daily)
        return " ".join(p for p in [now_line, outlook, advice] if p)

    def _outlook(self, daily: Sequence[DailyForecast]) -> str:
        if not daily:
            return ""
        phrases = []
        today = date.today()
        for d in daily:
            label = "Today" if d.day == today else d.weekday
            phrases.append(
                f"{label}, {d.description.lower()} with a high of {_describe_temp(d.tmax_c)} and a low of {_describe_temp(d.tmin_c)}"
                + (f", {d.precip_prob_pct} percent chance of rain" if d.precip_prob_pct >= 30 else "")
            )
        return "The outlook: " + "; ".join(phrases) + "."

    def _weather_advice(self, daily: Iterable[DailyForecast]) -> str:
        wet = [d for d in daily if d.precip_prob_pct >= 50]
        hot = [d for d in daily if d.tmax_c >= 30]
        if wet:
            names = _join([("today" if d.day == date.today() else d.weekday) for d in wet])
            return self._pick(
                [
                    f"I would suggest an umbrella {names}, {self.salutation}, unless you intend to make a point.",
                    f"Rain is likely {names}, {self.salutation}. I have taken the liberty of noting where you left your coat.",
                ]
            )
        if hot:
            return f"It will be rather warm {_join([d.weekday for d in hot])}, {self.salutation}. Hydration is advised, and I do not mean the whisky."
        return self._pick(
            [
                f"Nothing in the forecast that should trouble you, {self.salutation}.",
                f"A perfectly civilised outlook, {self.salutation}. I would make the most of it.",
            ]
        )

    # ------------------------------------------------------------------ misc
    def acknowledge(self) -> str:
        return self._pick(
            [
                f"Of course, {self.salutation}.",
                f"Right away, {self.salutation}.",
                f"As you wish, {self.salutation}.",
            ]
        )

    def say(self, text: str) -> str:
        """Speak arbitrary text, ensuring the salutation is present."""
        return self.address(text)
