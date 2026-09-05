"""Runtime settings.

Everything is read from environment variables (optionally loaded from a ``.env``
file). ``--mock`` mode needs none of them; sensible defaults cover Mr. Ozekin's
profile, Sydney's coordinates and a British ElevenLabs voice.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOCK_DATA_DIR = PROJECT_ROOT / "mock_data"

GMAIL_SCOPES = ("https://www.googleapis.com/auth/gmail.readonly",)


def _load_dotenv(path: Path | None) -> None:
    """Load a .env file if python-dotenv is installed and the file exists."""
    if path is None or not path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - optional dependency
        return
    load_dotenv(path, override=False)


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


def _env_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


@dataclass
class Settings:
    """All tunables for a J.A.R.V.I.S. run."""

    # Mode
    mock: bool = False

    # Principal
    principal_name: str = "Mr. Ozekin"
    principal_email: str = "martin@orbit3.io"

    # Google OAuth2
    google_credentials_path: Path = Path("credentials.json")
    google_token_path: Path = Path("token.json")

    # Auravest
    auravest_sender: str = "support@auravest.ai"
    auravest_lookback_days: int = 1

    # Orbit3 digest
    orbit3_lookback_days: int = 3

    # Weather
    weather_latitude: float = -33.8688
    weather_longitude: float = 151.2093
    weather_timezone: str = "Australia/Sydney"
    weather_location_name: str = "Sydney, NSW"
    weather_forecast_days: int = 3

    # Voice
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "onwK4e9ZLuTAKqWW03F9"  # "Daniel" - British, measured
    elevenlabs_model_id: str = "eleven_turbo_v2_5"
    audio_player: str = ""
    voice_engine: str = "auto"  # auto | elevenlabs | local | none
    save_audio_path: Path | None = None

    # Presentation
    hud: bool = True
    animate: bool = True
    request_timeout: float = 20.0

    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None, dotenv_path: Path | None = None) -> "Settings":
        """Build settings from ``env`` (defaults to ``os.environ``)."""
        if env is None:
            _load_dotenv(dotenv_path if dotenv_path is not None else Path(".env"))
            env = os.environ
        g = env.get
        return cls(
            mock=_env_bool(g("JARVIS_MOCK"), False),
            principal_name=g("JARVIS_PRINCIPAL_NAME") or "Mr. Ozekin",
            principal_email=g("JARVIS_PRINCIPAL_EMAIL") or "martin@orbit3.io",
            google_credentials_path=Path(g("GOOGLE_CREDENTIALS_PATH") or "credentials.json"),
            google_token_path=Path(g("GOOGLE_TOKEN_PATH") or "token.json"),
            auravest_sender=g("AURAVEST_SENDER") or "support@auravest.ai",
            auravest_lookback_days=_env_int(g("AURAVEST_LOOKBACK_DAYS"), 1),
            orbit3_lookback_days=_env_int(g("ORBIT3_LOOKBACK_DAYS"), 3),
            weather_latitude=_env_float(g("WEATHER_LATITUDE"), -33.8688),
            weather_longitude=_env_float(g("WEATHER_LONGITUDE"), 151.2093),
            weather_timezone=g("WEATHER_TIMEZONE") or "Australia/Sydney",
            weather_location_name=g("WEATHER_LOCATION_NAME") or "Sydney, NSW",
            weather_forecast_days=_env_int(g("WEATHER_FORECAST_DAYS"), 3),
            elevenlabs_api_key=g("ELEVENLABS_API_KEY") or "",
            elevenlabs_voice_id=g("ELEVENLABS_VOICE_ID") or "onwK4e9ZLuTAKqWW03F9",
            elevenlabs_model_id=g("ELEVENLABS_MODEL_ID") or "eleven_turbo_v2_5",
            audio_player=g("JARVIS_AUDIO_PLAYER") or "",
            voice_engine=(g("JARVIS_VOICE_ENGINE") or "auto").lower(),
            request_timeout=_env_float(g("JARVIS_REQUEST_TIMEOUT"), 20.0),
        )

    @property
    def has_elevenlabs(self) -> bool:
        return bool(self.elevenlabs_api_key.strip())

    def describe(self) -> dict[str, Any]:
        """Safe-to-print summary (secrets redacted)."""
        out: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name == "elevenlabs_api_key":
                value = "set" if value else "not set"
            elif isinstance(value, Path):
                value = str(value)
            out[f.name] = value
        return out
