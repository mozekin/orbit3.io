import json

import pytest

from jarvis.briefing import ALL_SECTIONS, BriefingAssembler
from jarvis.cli import build_parser, run, settings_from_args
from jarvis.config import Settings
from jarvis.connectors.gmail import FailingMailSource
from jarvis.connectors.weather import FailingWeatherClient, MockWeatherClient
from jarvis.errors import JarvisError
from jarvis.persona import Persona


def test_assembler_builds_all_sections(settings, mail, now):
    progress = []
    assembler = BriefingAssembler(settings, persona=Persona(seed=1), mail_factory=lambda: mail,
                                  weather_factory=lambda: MockWeatherClient(settings), on_progress=progress.append)
    briefing = assembler.build(now=now)
    assert [s.key for s in briefing.sections] == list(ALL_SECTIONS)
    assert briefing.mode == "mock" and briefing.greeting.startswith("Good afternoon, Mr. Ozekin.")
    assert "Mr. Ozekin" in briefing.sign_off
    assert progress == ["AURAVEST SIGNUPS", "ORBIT3 TASK DIGEST", "SYDNEY WEATHER"]
    assert all(s.error is None for s in briefing.sections)
    script = briefing.script
    assert script.startswith(briefing.greeting) and script.endswith(briefing.sign_off)
    assert "Priya Raman" in script and "Rachel Nguyen" in script and "In Sydney" in script


def test_assembler_isolates_failures(settings):
    assembler = BriefingAssembler(settings, persona=Persona(seed=1), mail_factory=lambda: FailingMailSource("gmail 503"),
                                  weather_factory=lambda: FailingWeatherClient("meteo down"))
    briefing = assembler.build()
    assert [s.error for s in briefing.sections] == ["gmail 503", "gmail 503", "meteo down"]
    assert "Auravest signup feed" in briefing.sections[0].spoken
    assert "Orbit3 mailbox" in briefing.sections[1].spoken
    assert "weather service" in briefing.sections[2].spoken and "meteo down" in briefing.sections[2].spoken
    assert "Mr. Ozekin" in briefing.greeting


def test_assembler_mail_factory_failure_is_a_section_error(settings):
    def broken():
        raise JarvisError("no credentials.json")

    briefing = BriefingAssembler(settings, mail_factory=broken, weather_factory=lambda: MockWeatherClient(settings)).build(["signups", "weather"])
    assert briefing.sections[0].error == "no credentials.json" and briefing.sections[1].error is None


def test_assembler_rejects_unknown_section(settings):
    with pytest.raises(JarvisError):
        BriefingAssembler(settings).build(["nonsense"])


def test_settings_from_args_overrides():
    args = build_parser().parse_args(["--mock", "--days", "5", "--voice", "local", "--no-hud", "--no-anim"])
    s = settings_from_args(args)
    assert s.mock and s.auravest_lookback_days == 5 and s.orbit3_lookback_days == 5
    assert s.voice_engine == "local" and not s.hud and not s.animate
    s2 = settings_from_args(build_parser().parse_args(["--json"]))
    assert s2.voice_engine == "none"
    s3 = settings_from_args(build_parser().parse_args(["--save-audio", "x.mp3"]))
    assert s3.voice_engine == "elevenlabs" and str(s3.save_audio_path) == "x.mp3"


def test_settings_from_env():
    s = Settings.from_env({"JARVIS_MOCK": "true", "AURAVEST_LOOKBACK_DAYS": "2", "WEATHER_LATITUDE": "-33.9", "ELEVENLABS_API_KEY": "k"})
    assert s.mock and s.auravest_lookback_days == 2 and s.weather_latitude == -33.9 and s.has_elevenlabs
    assert s.describe()["elevenlabs_api_key"] == "set"
    bad = Settings.from_env({"AURAVEST_LOOKBACK_DAYS": "many"})
    assert bad.auravest_lookback_days == 1


def test_cli_mock_json(capsys):
    assert run(["--mock", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "mock" and [s["key"] for s in out["sections"]] == list(ALL_SECTIONS)
    assert out["sections"][0]["data"]["signups"][0]["name"] == "Priya Raman"
    assert "Mr. Ozekin" in out["script"]


def test_cli_mock_plain(capsys):
    assert run(["--mock", "--no-hud", "--no-voice", "--sections", "weather,signups"]) == 0
    out = capsys.readouterr().out
    assert "--- SYDNEY WEATHER ---" in out and "--- AURAVEST SIGNUPS ---" in out and "ORBIT3" not in out
    assert "--- TRANSCRIPT ---" in out


def test_cli_mock_rich_hud_no_anim(capsys):
    assert run(["--mock", "--no-anim", "--no-voice"]) == 0
    out = capsys.readouterr().out
    assert "STARK INDUSTRIES" in out and "AURAVEST SIGNUPS" in out and "TRANSCRIPT" in out


def test_cli_unknown_section(capsys):
    assert run(["--mock", "--sections", "gossip"]) == 2
    assert "Unknown section" in capsys.readouterr().err


def test_cli_say(capsys):
    assert run(["--mock", "--no-hud", "--no-voice", "--say", "Bring the car round."]) == 0
    assert "Bring the car round, Mr. Ozekin." in capsys.readouterr().out


def test_cli_check(capsys):
    assert run(["--mock", "--check"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["mock"] is True and "google_auth" in info


def test_cli_list_voices_without_key(capsys):
    assert run(["--list-voices", "--env-file", "/nonexistent/.env"]) == 1
