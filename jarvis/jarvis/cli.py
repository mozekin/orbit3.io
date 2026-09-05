"""Command-line entry point for J.A.R.V.I.S.

Examples::

    jarvis --mock                     # full briefing on simulated data, no keys needed
    jarvis                            # live: Gmail (OAuth2) + Open-Meteo + ElevenLabs
    jarvis --auth                     # run the Google consent flow and store token.json
    jarvis --sections weather,tasks   # only some sections
    jarvis --voice local              # skip ElevenLabs, use the host's TTS
    jarvis --say "Bring the car round."
    jarvis --mock --json              # machine-readable briefing
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path
from typing import Sequence

from . import __version__
from .briefing import ALL_SECTIONS, BriefingAssembler
from .config import Settings
from .errors import JarvisError, VoiceError
from .hud import make_hud
from .persona import Persona
from .voice import ElevenLabsSpeaker, build_speaker


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jarvis",
        description="Project J.A.R.V.I.S. - a personal voice assistant for Mr. Ozekin.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples::", 1)[-1],
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--mock", action="store_true", help="run on bundled fixtures; no API keys or network needed")
    mode.add_argument("--live", action="store_true", help="force live connectors even if JARVIS_MOCK is set")
    p.add_argument("--sections", default=",".join(ALL_SECTIONS),
                   help=f"comma-separated sections to brief (default: {','.join(ALL_SECTIONS)})")
    p.add_argument("--days", type=int, default=None, help="override look-back window in days for both mail sections")
    p.add_argument("--voice", choices=["auto", "elevenlabs", "local", "none"], default=None,
                   help="voice engine (default: auto = ElevenLabs if key set, else local, else transcript)")
    p.add_argument("--no-voice", action="store_true", help="alias for --voice none")
    p.add_argument("--save-audio", type=Path, default=None, metavar="FILE", help="write the ElevenLabs MP3 here instead of playing")
    p.add_argument("--no-hud", action="store_true", help="plain text output instead of the Stark HUD")
    p.add_argument("--no-anim", action="store_true", help="disable boot animation and typewriter effect")
    p.add_argument("--json", action="store_true", help="print the briefing as JSON and exit (implies --no-voice)")
    p.add_argument("--say", metavar="TEXT", help="have J.A.R.V.I.S. say TEXT and exit")
    p.add_argument("--auth", action="store_true", help="run the Google OAuth2 consent flow, store the token and exit")
    p.add_argument("--list-voices", action="store_true", help="list ElevenLabs voices (British/butler ones first) and exit")
    p.add_argument("--check", action="store_true", help="print effective configuration and auth status, then exit")
    p.add_argument("--env-file", type=Path, default=Path(".env"), help="path to a .env file (default: ./.env)")
    p.add_argument("--version", action="version", version=f"J.A.R.V.I.S. {__version__}")
    return p


def settings_from_args(args: argparse.Namespace) -> Settings:
    settings = Settings.from_env(dotenv_path=args.env_file)
    if args.mock:
        settings.mock = True
    if args.live:
        settings.mock = False
    if args.days:
        settings.auravest_lookback_days = args.days
        settings.orbit3_lookback_days = args.days
    if args.no_voice or args.json:
        settings.voice_engine = "none"
    elif args.voice:
        settings.voice_engine = args.voice
    if args.save_audio:
        settings.save_audio_path = args.save_audio
        if settings.voice_engine == "auto":
            settings.voice_engine = "elevenlabs"
    settings.hud = not args.no_hud
    settings.animate = not args.no_anim
    return settings


# --------------------------------------------------------------------------- sub-commands
def cmd_check(settings: Settings) -> int:
    from .connectors.google_auth import token_status

    info = settings.describe()
    info["google_auth"] = token_status(settings)
    print(json.dumps(info, indent=2, default=str))
    return 0


def cmd_auth(settings: Settings) -> int:
    from .connectors.google_auth import credentials_from_settings

    try:
        creds = credentials_from_settings(settings, interactive=True)
    except JarvisError as exc:
        print(f"Authentication failed: {exc}", file=sys.stderr)
        return 1
    print(f"Google token stored at {settings.google_token_path} (scopes: {', '.join(creds.scopes or [])}).")
    return 0


def cmd_list_voices(settings: Settings) -> int:
    if not settings.has_elevenlabs:
        print("ELEVENLABS_API_KEY is not set.", file=sys.stderr)
        return 1
    try:
        voices = ElevenLabsSpeaker(settings.elevenlabs_api_key, settings.elevenlabs_voice_id).list_voices()
    except JarvisError as exc:
        print(f"Could not list voices: {exc}", file=sys.stderr)
        return 1

    def rank(v: dict) -> tuple[int, str]:
        blob = json.dumps(v).lower()
        score = 0
        if "butler" in blob:
            score -= 3
        if "british" in blob:
            score -= 2
        if "male" in blob:
            score -= 1
        return (score, v.get("name", ""))

    for v in sorted(voices, key=rank):
        labels = ", ".join(f"{k}={val}" for k, val in (v.get("labels") or {}).items())
        marker = " ◀ current" if v.get("voice_id") == settings.elevenlabs_voice_id else ""
        print(f"{v.get('voice_id')}  {v.get('name', ''):<24} {labels}{marker}")
    return 0


def cmd_say(settings: Settings, text: str, hud) -> int:
    persona = Persona(settings.principal_name)
    line = persona.say(text)
    hud.transcript(line)
    return _speak(settings, line, hud)


def _speak(settings: Settings, script: str, hud, while_speaking=None) -> int:
    """Speak ``script``; if ``while_speaking`` is given, run it concurrently (e.g. the typewriter)."""
    if settings.voice_engine == "none":
        if while_speaking:
            while_speaking()
        return 0
    outcome: dict[str, object] = {}

    def worker() -> None:
        try:
            outcome["result"] = build_speaker(settings).speak(script)
        except VoiceError as exc:
            outcome["error"] = str(exc)

    if while_speaking:
        thread = threading.Thread(target=worker, name="jarvis-voice", daemon=True)
        thread.start()
        while_speaking()
        thread.join()
    else:
        worker()
    if "error" in outcome:
        hud.voice_result(None, error=str(outcome["error"]))
        return 1
    hud.voice_result(outcome.get("result"))  # type: ignore[arg-type]
    return 0


# --------------------------------------------------------------------------- main
def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = settings_from_args(args)
    hud = make_hud(settings, plain=(not settings.hud) or args.json)

    if args.check:
        return cmd_check(settings)
    if args.auth:
        return cmd_auth(settings)
    if args.list_voices:
        return cmd_list_voices(settings)
    if args.say:
        return cmd_say(settings, args.say, hud)

    sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    unknown = [s for s in sections if s not in ALL_SECTIONS]
    if unknown:
        print(f"Unknown section(s): {', '.join(unknown)}. Choose from: {', '.join(ALL_SECTIONS)}", file=sys.stderr)
        return 2

    if not args.json:
        hud.boot(settings)

    assembler = BriefingAssembler(settings, on_progress=lambda name: None if args.json else hud.status(f"Compiling {name}"))
    try:
        briefing = assembler.build(sections)
    except JarvisError as exc:
        print(f"J.A.R.V.I.S. could not assemble the briefing: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({**briefing.to_dict(), "script": briefing.script}, indent=2, default=str))
        return 0

    hud.render_briefing(briefing)
    rc = _speak(settings, briefing.script, hud,
                while_speaking=lambda: hud.transcript(briefing.script, typewriter=settings.animate))
    if any(s.error for s in briefing.sections):
        hud.status("One or more sections reported errors; see above.", level="warn")
    return rc


def main() -> int:
    try:
        return run()
    except KeyboardInterrupt:
        print("\nAs you wish, Mr. Ozekin. Standing down.", file=sys.stderr)
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
