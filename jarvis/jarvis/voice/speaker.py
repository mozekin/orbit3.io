"""Speakers.

* :class:`ElevenLabsSpeaker` - streams MP3 chunks from the ElevenLabs
  text-to-speech streaming endpoint straight into a local player (or a file).
* :class:`LocalSpeaker` - offline text-to-speech via whatever the host has:
  macOS ``say`` (Daniel, a British voice), ``espeak-ng``/``espeak`` (en-gb),
  ``pyttsx3``, or Windows SAPI.
* :class:`SilentSpeaker` - prints the transcript only.
* :class:`FallbackSpeaker` - tries speakers in order until one succeeds.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

from ..config import Settings
from ..errors import VoiceError
from .players import Player, find_player, play_file

ELEVENLABS_API = "https://api.elevenlabs.io/v1"


@dataclass
class SpeechResult:
    engine: str
    ok: bool
    detail: str = ""
    audio_path: Path | None = None
    fallbacks: list[str] = field(default_factory=list)


class Speaker(Protocol):
    name: str

    def speak(self, text: str) -> SpeechResult: ...


# --------------------------------------------------------------------------- elevenlabs
class ElevenLabsSpeaker:
    """Stream speech from ElevenLabs.

    ``session`` may be any object with ``post(url, headers=, json=, stream=, timeout=)``
    returning a response with ``status_code``, ``iter_content(chunk_size)`` and
    ``text`` - the real ``requests`` module by default, a fake in tests.
    """

    name = "elevenlabs"

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_turbo_v2_5",
        player: Player | None = None,
        session: Any | None = None,
        save_path: Path | None = None,
        timeout: float = 30.0,
        voice_settings: dict[str, Any] | None = None,
    ) -> None:
        if not api_key:
            raise VoiceError("ElevenLabs API key is not configured.")
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.player = player
        self.session = session
        self.save_path = save_path
        self.timeout = timeout
        # A composed, unhurried delivery: high stability, moderate style.
        self.voice_settings = voice_settings or {
            "stability": 0.65,
            "similarity_boost": 0.8,
            "style": 0.25,
            "use_speaker_boost": True,
        }

    def _http(self) -> Any:
        if self.session is not None:
            return self.session
        try:
            import requests
        except ImportError as exc:  # pragma: no cover
            raise VoiceError("The 'requests' package is required for ElevenLabs.") from exc
        return requests

    def stream(self, text: str, chunk_size: int = 4096) -> Iterable[bytes]:
        url = f"{ELEVENLABS_API}/text-to-speech/{self.voice_id}/stream"
        headers = {"xi-api-key": self.api_key, "accept": "audio/mpeg", "content-type": "application/json"}
        body = {"text": text, "model_id": self.model_id, "voice_settings": self.voice_settings}
        try:
            resp = self._http().post(
                url, headers=headers, json=body, params={"output_format": "mp3_44100_128"},
                stream=True, timeout=self.timeout,
            )
        except Exception as exc:  # noqa: BLE001
            raise VoiceError(f"ElevenLabs request failed: {exc}") from exc
        status = getattr(resp, "status_code", 200)
        if status >= 400:
            detail = getattr(resp, "text", "")[:200]
            raise VoiceError(f"ElevenLabs returned HTTP {status}: {detail}")
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk

    def list_voices(self) -> list[dict[str, Any]]:
        resp = self._http().get(f"{ELEVENLABS_API}/voices", headers={"xi-api-key": self.api_key}, timeout=self.timeout)
        if getattr(resp, "status_code", 200) >= 400:
            raise VoiceError(f"ElevenLabs returned HTTP {resp.status_code}")
        return list(resp.json().get("voices", []))

    def speak(self, text: str) -> SpeechResult:
        player = self.player if self.player is not None else find_player()
        chunks = self.stream(text)
        saved: Path | None = None

        if player is not None and player.streams and self.save_path is None:
            proc = subprocess.Popen(player.stdin_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            assert proc.stdin is not None
            try:
                for chunk in chunks:
                    proc.stdin.write(chunk)
                proc.stdin.close()
                proc.wait()
            except BrokenPipeError as exc:
                raise VoiceError(f"Audio player {player.name} closed the stream.") from exc
            return SpeechResult(self.name, True, f"streamed via {player.name}")

        # Otherwise buffer to a file, then play it (or just keep it).
        target = self.save_path or Path(tempfile.mkstemp(prefix="jarvis-", suffix=".mp3")[1])
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as fh:
            for chunk in chunks:
                fh.write(chunk)
        saved = target
        if player is None:
            if self.save_path:
                return SpeechResult(self.name, True, f"saved to {saved}", audio_path=saved)
            raise VoiceError("No audio player found (install ffplay, mpv or mpg123) and no --save-audio path given.")
        try:
            play_file(player, saved)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise VoiceError(f"Audio playback failed via {player.name}: {exc}") from exc
        return SpeechResult(self.name, True, f"played via {player.name}", audio_path=saved if self.save_path else None)


# --------------------------------------------------------------------------- local
Runner = Callable[[list[str]], None]


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class LocalSpeaker:
    """Offline text-to-speech using whatever the host provides."""

    name = "local"

    def __init__(self, runner: Runner = _run, which: Callable[[str], str | None] = shutil.which, platform: str = sys.platform) -> None:
        self._run = runner
        self._which = which
        self._platform = platform

    def backends(self) -> list[tuple[str, list[str]]]:
        """Ordered list of (name, command) candidates available on this host."""
        out: list[tuple[str, list[str]]] = []
        if self._platform == "darwin" and self._which("say"):
            out.append(("say", ["say", "-v", "Daniel", "-r", "175"]))
        if self._which("espeak-ng"):
            out.append(("espeak-ng", ["espeak-ng", "-v", "en-gb", "-s", "160", "-p", "40"]))
        elif self._which("espeak"):
            out.append(("espeak", ["espeak", "-v", "en-gb", "-s", "160", "-p", "40"]))
        if self._platform == "win32" and self._which("powershell"):
            out.append(("sapi", ["powershell", "-NoProfile", "-Command",
                                 "Add-Type -AssemblyName System.Speech; "
                                 "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                                 "$v = $s.GetInstalledVoices() | ? { $_.VoiceInfo.Culture.Name -eq 'en-GB' } | select -First 1; "
                                 "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }; $s.Speak($args[0])"]))
        return out

    def _pyttsx3(self, text: str) -> bool:
        try:
            import pyttsx3  # type: ignore
        except ImportError:
            return False
        engine = pyttsx3.init()
        for voice in engine.getProperty("voices"):
            blob = f"{voice.id} {getattr(voice, 'name', '')} {getattr(voice, 'languages', '')}".lower()
            if "en-gb" in blob or "en_gb" in blob or "daniel" in blob or "british" in blob:
                engine.setProperty("voice", voice.id)
                break
        engine.setProperty("rate", 165)
        engine.say(text)
        engine.runAndWait()
        return True

    def speak(self, text: str) -> SpeechResult:
        errors: list[str] = []
        for name, cmd in self.backends():
            try:
                self._run([*cmd, text])
                return SpeechResult(self.name, True, f"spoke via {name}")
            except (OSError, subprocess.CalledProcessError) as exc:
                errors.append(f"{name}: {exc}")
        try:
            if self._pyttsx3(text):
                return SpeechResult(self.name, True, "spoke via pyttsx3")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"pyttsx3: {exc}")
        raise VoiceError("No local text-to-speech backend available" + (f" ({'; '.join(errors)})" if errors else "") + ".")


# --------------------------------------------------------------------------- silent / fallback
class SilentSpeaker:
    """Never plays audio; the HUD shows the transcript instead."""

    name = "silent"

    def speak(self, text: str) -> SpeechResult:
        return SpeechResult(self.name, True, "transcript only")


class FallbackSpeaker:
    """Try each speaker in order; the first success wins."""

    name = "fallback"

    def __init__(self, speakers: list[Speaker], on_fallback: Callable[[str, str], None] | None = None) -> None:
        if not speakers:
            raise VoiceError("FallbackSpeaker needs at least one speaker.")
        self.speakers = speakers
        self.on_fallback = on_fallback
        self.name = "+".join(s.name for s in speakers)

    def speak(self, text: str) -> SpeechResult:
        errors: list[str] = []
        for speaker in self.speakers:
            try:
                result = speaker.speak(text)
                result.fallbacks = errors[:]
                return result
            except VoiceError as exc:
                errors.append(f"{speaker.name}: {exc}")
                if self.on_fallback:
                    self.on_fallback(speaker.name, str(exc))
        raise VoiceError("All voice engines failed: " + " | ".join(errors))


def build_speaker(settings: Settings, session: Any | None = None) -> Speaker:
    """Choose the speaker chain from settings.

    * ``none``       -> silent (transcript only)
    * ``local``      -> local TTS, then silent
    * ``elevenlabs`` -> ElevenLabs, then local, then silent
    * ``auto``       -> ElevenLabs if a key is set (and not mock), then local, then silent
    """
    engine = settings.voice_engine
    chain: list[Speaker] = []
    if engine == "none":
        return SilentSpeaker()
    use_eleven = engine == "elevenlabs" or (engine == "auto" and settings.has_elevenlabs and not settings.mock)
    if use_eleven:
        chain.append(
            ElevenLabsSpeaker(
                api_key=settings.elevenlabs_api_key,
                voice_id=settings.elevenlabs_voice_id,
                model_id=settings.elevenlabs_model_id,
                player=find_player(settings.audio_player),
                session=session,
                save_path=settings.save_audio_path,
                timeout=max(settings.request_timeout, 30.0),
            )
        )
    if engine in {"auto", "local", "elevenlabs"}:
        chain.append(LocalSpeaker())
    chain.append(SilentSpeaker())
    return FallbackSpeaker(chain)
