import subprocess
from pathlib import Path

import pytest

from jarvis.config import Settings
from jarvis.errors import VoiceError
from jarvis.voice.players import Player, find_player
from jarvis.voice.speaker import ElevenLabsSpeaker, FallbackSpeaker, LocalSpeaker, SilentSpeaker, build_speaker

from conftest import FakeResponse, FakeSession


def test_elevenlabs_stream_request_shape():
    session = FakeSession(FakeResponse(200, chunks=[b"abc", b"", b"def"]))
    speaker = ElevenLabsSpeaker("key", "voice123", model_id="eleven_turbo_v2_5", session=session)
    assert b"".join(speaker.stream("Hello")) == b"abcdef"
    call = session.calls[0]
    assert call["url"].endswith("/text-to-speech/voice123/stream")
    assert call["headers"]["xi-api-key"] == "key"
    assert call["json"]["text"] == "Hello" and call["json"]["model_id"] == "eleven_turbo_v2_5"
    assert call["stream"] is True and call["params"]["output_format"].startswith("mp3")


def test_elevenlabs_http_error_raises_voice_error():
    speaker = ElevenLabsSpeaker("key", "v", session=FakeSession(FakeResponse(401, text="bad key")))
    with pytest.raises(VoiceError, match="HTTP 401"):
        list(speaker.stream("x"))


def test_elevenlabs_requires_key():
    with pytest.raises(VoiceError):
        ElevenLabsSpeaker("", "v")


def test_elevenlabs_saves_to_file_without_player(tmp_path):
    target = tmp_path / "out" / "brief.mp3"
    speaker = ElevenLabsSpeaker("key", "v", session=FakeSession(FakeResponse(200, chunks=[b"ID3", b"data"])),
                                player=None, save_path=target)
    # Force "no player found" regardless of host tools.
    import jarvis.voice.speaker as mod

    original = mod.find_player
    mod.find_player = lambda *_a, **_k: None
    try:
        result = speaker.speak("x")
    finally:
        mod.find_player = original
    assert result.ok and result.audio_path == target and target.read_bytes() == b"ID3data"


def test_elevenlabs_streams_to_player(monkeypatch):
    written = bytearray()

    class FakeStdin:
        def write(self, b):
            written.extend(b)

        def close(self):
            pass

    class FakeProc:
        stdin = FakeStdin()

        def wait(self):
            return 0

    import jarvis.voice.speaker as mod

    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: FakeProc())
    player = Player("fake", ["fake", "-"], ["fake"])
    speaker = ElevenLabsSpeaker("key", "v", session=FakeSession(FakeResponse(200, chunks=[b"a", b"b"])), player=player)
    result = speaker.speak("x")
    assert result.ok and "fake" in result.detail and bytes(written) == b"ab"


def test_local_speaker_uses_first_available_backend():
    calls = []
    speaker = LocalSpeaker(runner=lambda cmd: calls.append(cmd), which=lambda name: name in {"espeak-ng"} or None, platform="linux")
    result = speaker.speak("Good morning")
    assert result.ok and "espeak-ng" in result.detail
    assert calls[0][:3] == ["espeak-ng", "-v", "en-gb"] and calls[0][-1] == "Good morning"


def test_local_speaker_prefers_say_on_macos():
    calls = []
    speaker = LocalSpeaker(runner=lambda cmd: calls.append(cmd), which=lambda name: name in {"say", "espeak"} or None, platform="darwin")
    speaker.speak("hi")
    assert calls[0][:3] == ["say", "-v", "Daniel"]


def test_local_speaker_falls_through_failed_backends():
    def runner(cmd):
        if cmd[0] == "say":
            raise subprocess.CalledProcessError(1, cmd)

    calls = []
    speaker = LocalSpeaker(runner=lambda c: runner(c) or calls.append(c), which=lambda n: n in {"say", "espeak-ng"} or None, platform="darwin")
    result = speaker.speak("hi")
    assert "espeak-ng" in result.detail


def test_local_speaker_without_backends_raises():
    speaker = LocalSpeaker(runner=lambda cmd: None, which=lambda name: None, platform="linux")
    with pytest.raises(VoiceError, match="No local text-to-speech"):
        speaker.speak("hi")


class Boom:
    name = "boom"

    def speak(self, text):
        raise VoiceError("kaput")


def test_fallback_chain_records_failures():
    seen = []
    chain = FallbackSpeaker([Boom(), SilentSpeaker()], on_fallback=lambda n, e: seen.append((n, e)))
    result = chain.speak("x")
    assert result.engine == "silent" and result.fallbacks == ["boom: kaput"]
    assert seen == [("boom", "kaput")]
    assert chain.name == "boom+silent"


def test_fallback_chain_all_fail():
    with pytest.raises(VoiceError, match="All voice engines failed"):
        FallbackSpeaker([Boom(), Boom()]).speak("x")


def test_build_speaker_selection():
    assert isinstance(build_speaker(Settings(voice_engine="none")), SilentSpeaker)
    local = build_speaker(Settings(voice_engine="local"))
    assert [s.name for s in local.speakers] == ["local", "silent"]
    auto_no_key = build_speaker(Settings(voice_engine="auto"))
    assert [s.name for s in auto_no_key.speakers] == ["local", "silent"]
    auto_key = build_speaker(Settings(voice_engine="auto", elevenlabs_api_key="k"))
    assert [s.name for s in auto_key.speakers] == ["elevenlabs", "local", "silent"]
    mock_key = build_speaker(Settings(voice_engine="auto", elevenlabs_api_key="k", mock=True))
    assert [s.name for s in mock_key.speakers] == ["local", "silent"]
    forced = build_speaker(Settings(voice_engine="elevenlabs", elevenlabs_api_key="k", mock=True))
    assert forced.speakers[0].name == "elevenlabs"


def test_find_player_override_detects_streaming():
    p = find_player("mpv --no-video -")
    assert p is not None and p.streams and p.name == "mpv" and p.file_cmd == ["mpv", "--no-video"]
    q = find_player("afplay")
    assert q is not None and not q.streams
