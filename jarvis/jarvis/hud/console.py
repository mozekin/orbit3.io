"""Stark Industries styled console HUD.

Rendered with `rich` when available; :class:`PlainHUD` is a dependency-free
fallback that prints the same information as plain text (also used for
``--no-hud`` and non-interactive output).
"""
from __future__ import annotations

import sys
import time
from datetime import date, datetime
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from ..config import Settings
from ..connectors.weather import glyph_for_code
from ..models import Briefing, Section, SignupReport, TasksDigest, WeatherReport
from ..voice.speaker import SpeechResult

BANNER = r"""
     ██╗     █████╗     ██████╗     ██╗   ██╗    ██╗    ███████╗
     ██║    ██╔══██╗    ██╔══██╗    ██║   ██║    ██║    ██╔════╝
     ██║    ███████║    ██████╔╝    ██║   ██║    ██║    ███████╗
██   ██║    ██╔══██║    ██╔══██╗    ╚██╗ ██╔╝    ██║    ╚════██║
╚█████╔╝ ██ ██║  ██║ ██ ██║  ██║ ██  ╚████╔╝  ██ ██║ ██ ███████║
 ╚════╝  ╚═╝╚═╝  ╚═╝ ╚═╝╚═╝  ╚═╝ ╚═╝  ╚═══╝   ╚═╝╚═╝ ╚═╝╚══════╝
""".strip("\n")

TAGLINE = "STARK INDUSTRIES  //  Just A Rather Very Intelligent System"

BOOT_SEQUENCE = [
    "Initialising arc-reactor telemetry",
    "Calibrating repulsor diagnostics (decorative)",
    "Establishing Gmail uplink",
    "Polling Auravest operations channel",
    "Scanning Orbit3 correspondence",
    "Querying Bureau-grade meteorology for Sydney",
    "Warming the vocal cords",
]

# Palette: Iron Man gold, hot-rod red, arc-reactor cyan.
GOLD = "#F5C242"
RED = "#E23744"
CYAN = "#38E8FF"
DIM = "#7A8699"
GREEN = "#4ADE80"

PRIORITY_STYLE = {"urgent": f"bold {RED}", "high": f"bold {GOLD}", "normal": CYAN}


class HUD(Protocol):
    def boot(self, settings: Settings) -> None: ...
    def status(self, message: str, level: str = "info") -> None: ...
    def render_briefing(self, briefing: Briefing) -> None: ...
    def transcript(self, text: str, typewriter: bool = False) -> None: ...
    def voice_result(self, result: SpeechResult | None, error: str | None = None) -> None: ...


def _local_now(tz_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:  # noqa: BLE001 - unknown tz on host
        return datetime.now()


def _fmt_dt(value: datetime | None, tz_name: str) -> str:
    if value is None:
        return "-"
    try:
        return value.astimezone(ZoneInfo(tz_name)).strftime("%a %d %b %H:%M")
    except Exception:  # noqa: BLE001
        return value.strftime("%a %d %b %H:%M")


def _error_text(section: Section) -> str:
    data_error = getattr(section.data, "error", None)
    return section.error or data_error or "unknown error"


# --------------------------------------------------------------------------- rich HUD
class StarkHUD:
    """The full-colour HUD."""

    def __init__(self, settings: Settings, console: Any | None = None, animate: bool | None = None) -> None:
        from rich.console import Console

        self.settings = settings
        self.console = console or Console(highlight=False)
        self.animate = self.console.is_terminal if animate is None else animate
        self.tz = settings.weather_timezone

    # ---- framing
    def boot(self, settings: Settings) -> None:
        from rich.align import Align
        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text

        now = _local_now(self.tz)
        mode = "MOCK  ·  simulated data" if settings.mock else "LIVE  ·  Gmail + Open-Meteo"
        status = Text.assemble(
            ("PRINCIPAL ", DIM), (settings.principal_name, f"bold {GOLD}"),
            ("   MODE ", DIM), (mode, f"bold {RED}" if settings.mock else f"bold {GREEN}"),
            ("   VOICE ", DIM), (settings.voice_engine.upper(), f"bold {CYAN}"),
            ("\n", ""), (now.strftime("%A %d %B %Y  ·  %H:%M %Z"), GOLD),
            justify="center",
        )
        body = Group(
            Align.center(Text(BANNER, style=f"bold {GOLD}")),
            Align.center(Text(TAGLINE, style=CYAN)),
            Align.center(status),
        )
        self.console.print(Panel(body, border_style=GOLD, padding=(0, 2)))

        if self.animate and settings.animate:
            from rich.progress import Progress, SpinnerColumn, TextColumn

            with Progress(SpinnerColumn(style=CYAN), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                task = progress.add_task("", total=None)
                for step in BOOT_SEQUENCE:
                    progress.update(task, description=f"[{DIM}]{step}…")
                    time.sleep(0.12)
        self.console.print(f"[{GREEN}]◉[/] [{DIM}]All systems nominal.[/]")

    def status(self, message: str, level: str = "info") -> None:
        style = {"info": DIM, "warn": GOLD, "error": RED, "ok": GREEN}.get(level, DIM)
        self.console.print(f"[{style}]▸ {message}[/]")

    # ---- sections
    def render_briefing(self, briefing: Briefing) -> None:
        for section in briefing.sections:
            renderer = getattr(self, f"_render_{section.key}", self._render_generic)
            renderer(section)

    def _panel(self, body: Any, title: str, error: bool = False) -> Any:
        from rich.panel import Panel

        return Panel(body, title=f"[bold {GOLD}]◈ {title}[/]", border_style=RED if error else GOLD, padding=(0, 1))

    def _render_error(self, section: Section) -> None:
        from rich.text import Text

        self.console.print(self._panel(Text(f"✖ {_error_text(section)}", style=RED), section.title, error=True))

    def _render_generic(self, section: Section) -> None:
        from rich.text import Text

        if section.error:
            self._render_error(section)
            return
        self.console.print(self._panel(Text(section.spoken), section.title))

    def _render_signups(self, section: Section) -> None:
        from rich.console import Group
        from rich.table import Table
        from rich.text import Text

        report: SignupReport | None = section.data
        if report is None or section.error or report.error:
            self._render_error(section)
            return
        table = Table(expand=True, header_style=f"bold {CYAN}", border_style=DIM, show_edge=False)
        table.add_column("When", style=DIM, no_wrap=True)
        table.add_column("Name", style=f"bold {GOLD}")
        table.add_column("Email", style=CYAN, overflow="fold")
        table.add_column("Company")
        table.add_column("Plan", style=GREEN)
        for s in report.signups:
            table.add_row(_fmt_dt(s.signed_up_at, self.tz), s.name or "-", s.email or "-", s.company or "-", s.plan or "-")
        if not report.signups:
            table.add_row("-", "No new signups", "", "", "")
        caption = Text(
            f"{report.count} signup(s) · scanned {report.scanned} message(s) · last {report.lookback_days} day(s)",
            style=DIM,
        )
        self.console.print(self._panel(Group(table, caption), section.title))

    def _render_tasks(self, section: Section) -> None:
        from rich.console import Group
        from rich.table import Table
        from rich.text import Text

        digest: TasksDigest | None = section.data
        if digest is None or section.error or digest.error:
            self._render_error(section)
            return
        parts: list[Any] = []
        if digest.urgent:
            urgent = Table(expand=True, header_style=f"bold {RED}", border_style=DIM, show_edge=False,
                           title=f"[bold {RED}]⚠ URGENT COMMUNICATIONS[/]")
            urgent.add_column("Received", style=DIM, no_wrap=True)
            urgent.add_column("From", style=f"bold {GOLD}")
            urgent.add_column("Subject", ratio=2)
            urgent.add_column("Why", style=RED)
            for u in digest.urgent:
                urgent.add_row(_fmt_dt(u.received, self.tz), u.sender, u.subject, u.reason)
            parts.append(urgent)
        tasks = Table(expand=True, header_style=f"bold {CYAN}", border_style=DIM, show_edge=False,
                      title=f"[bold {CYAN}]☑ OUTSTANDING TASKS[/]")
        tasks.add_column("Pri", no_wrap=True)
        tasks.add_column("Task", ratio=3)
        tasks.add_column("Due", style=GOLD, no_wrap=True)
        tasks.add_column("From", style=DIM)
        for t in digest.tasks:
            tasks.add_row(Text(t.priority.upper(), style=PRIORITY_STYLE.get(t.priority, CYAN)), t.title, t.due or "-", t.sender)
        if not digest.tasks:
            tasks.add_row("", "Nothing outstanding", "", "")
        parts.append(tasks)
        parts.append(Text(
            f"{len(digest.tasks)} task(s) · {len(digest.urgent)} urgent · scanned {digest.scanned} message(s) · last {digest.lookback_days} day(s)",
            style=DIM,
        ))
        self.console.print(self._panel(Group(*parts), section.title))

    def _render_weather(self, section: Section) -> None:
        from rich.console import Group
        from rich.table import Table
        from rich.text import Text

        report: WeatherReport | None = section.data
        if report is None or section.error or report.error:
            self._render_error(section)
            return
        c = report.current
        current = Text.assemble(
            (f"{glyph_for_code(c.weather_code)}  ", ""),
            (f"{c.temperature_c:.0f}°C", f"bold {GOLD}"),
            (f"  {c.description}", CYAN),
            (f"   feels {c.apparent_c:.0f}°C · humidity {c.humidity_pct}% · wind {c.wind_kmh:.0f} km/h", DIM),
            (f"   observed {c.observed_at.strftime('%H:%M')} {report.timezone}", DIM),
        )
        table = Table(expand=True, header_style=f"bold {CYAN}", border_style=DIM, show_edge=False)
        table.add_column("Day", style=f"bold {GOLD}", no_wrap=True)
        table.add_column("Conditions", ratio=2)
        table.add_column("High", justify="right")
        table.add_column("Low", justify="right")
        table.add_column("Rain", justify="right")
        table.add_column("Wind", justify="right", style=DIM)
        table.add_column("UV", justify="right", style=DIM)
        for d in report.daily:
            label = "Today" if d.day == date.today() else d.weekday
            rain_style = RED if d.precip_prob_pct >= 50 else (GOLD if d.precip_prob_pct >= 30 else GREEN)
            table.add_row(
                label,
                f"{glyph_for_code(d.weather_code)} {d.description}",
                f"{d.tmax_c:.0f}°C",
                f"{d.tmin_c:.0f}°C",
                Text(f"{d.precip_prob_pct}% · {d.precip_mm:.1f}mm", style=rain_style),
                f"{d.wind_max_kmh:.0f} km/h",
                f"{d.uv_index_max:.0f}" if d.uv_index_max is not None else "-",
            )
        self.console.print(self._panel(Group(current, table), f"{section.title} · {report.location}"))

    # ---- speech
    def transcript(self, text: str, typewriter: bool = False) -> None:
        from rich.panel import Panel
        from rich.rule import Rule
        from rich.text import Text

        if typewriter and self.animate:
            # Character-by-character, capped so a long script never takes more than ~8s.
            delay = min(0.008, 8.0 / max(len(text), 1))
            self.console.print(Rule(f"[bold {GOLD}]◈ TRANSCRIPT[/]", style=CYAN))
            stream = self.console.file
            stream.write("\x1b[3m")  # italic
            for ch in text:
                stream.write(ch)
                stream.flush()
                if ch not in " \n":
                    time.sleep(delay)
            stream.write("\x1b[0m\n\n")
            stream.flush()
            self.console.print(Rule(style=CYAN))
            return
        self.console.print(Panel(Text(text, style="italic"), title=f"[bold {GOLD}]◈ TRANSCRIPT[/]", border_style=CYAN, padding=(0, 1)))

    def voice_result(self, result: SpeechResult | None, error: str | None = None) -> None:
        if error:
            self.console.print(f"[{RED}]✖ voice: {error}[/]")
            return
        if result is None:
            return
        for fb in result.fallbacks:
            self.console.print(f"[{GOLD}]↳ fallback: {fb}[/]")
        self.console.print(f"[{GREEN}]♪ voice: {result.engine} · {result.detail}[/]")


# --------------------------------------------------------------------------- plain HUD
class PlainHUD:
    """Dependency-free text output."""

    def __init__(self, settings: Settings, stream: Any | None = None) -> None:
        self.settings = settings
        self.stream = stream or sys.stdout
        self.tz = settings.weather_timezone

    def _p(self, *lines: str) -> None:
        for line in lines:
            print(line, file=self.stream)

    def boot(self, settings: Settings) -> None:
        self._p("=" * 72, "J.A.R.V.I.S.  //  STARK INDUSTRIES  //  Principal: " + settings.principal_name,
                f"mode={'MOCK' if settings.mock else 'LIVE'}  voice={settings.voice_engine}  "
                f"{_local_now(self.tz).strftime('%A %d %B %Y %H:%M %Z')}", "=" * 72)

    def status(self, message: str, level: str = "info") -> None:
        self._p(f"[{level}] {message}")

    def render_briefing(self, briefing: Briefing) -> None:
        for s in briefing.sections:
            self._p("", f"--- {s.title} ---")
            data = s.data
            if s.error or getattr(data, "error", None):
                self._p(f"ERROR: {_error_text(s)}")
                continue
            if isinstance(data, SignupReport):
                for x in data.signups:
                    self._p(f"  {_fmt_dt(x.signed_up_at, self.tz)}  {x.name:<24} {x.email:<36} {x.company:<22} {x.plan}")
                if not data.signups:
                    self._p("  (no new signups)")
            elif isinstance(data, TasksDigest):
                for u in data.urgent:
                    self._p(f"  URGENT  {u.sender}: {u.subject}  ({u.reason})")
                for t in data.tasks:
                    self._p(f"  [{t.priority:<6}] {t.title}" + (f"  (due {t.due})" if t.due else "") + f"  <{t.sender}>")
                if not data.tasks and not data.urgent:
                    self._p("  (nothing outstanding)")
            elif isinstance(data, WeatherReport):
                c = data.current
                self._p(f"  now: {c.temperature_c:.0f}C {c.description}, feels {c.apparent_c:.0f}C, "
                        f"humidity {c.humidity_pct}%, wind {c.wind_kmh:.0f} km/h")
                for d in data.daily:
                    self._p(f"  {d.weekday:<10} {d.description:<24} {d.tmax_c:>3.0f}/{d.tmin_c:<3.0f}C  rain {d.precip_prob_pct}%")

    def transcript(self, text: str, typewriter: bool = False) -> None:
        self._p("", "--- TRANSCRIPT ---", text, "")

    def voice_result(self, result: SpeechResult | None, error: str | None = None) -> None:
        if error:
            self._p(f"voice error: {error}")
        elif result is not None:
            for fb in result.fallbacks:
                self._p(f"voice fallback: {fb}")
            self._p(f"voice: {result.engine} - {result.detail}")


def make_hud(settings: Settings, plain: bool = False, console: Any | None = None) -> HUD:
    if plain:
        return PlainHUD(settings)
    try:
        import rich  # noqa: F401
    except ImportError:
        return PlainHUD(settings)
    return StarkHUD(settings, console=console)
