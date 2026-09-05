"""Google OAuth2 (installed-app flow) for Gmail read-only access.

First run opens a browser for consent and stores ``token.json``; later runs
refresh silently. All Google imports are lazy so ``--mock`` mode never needs
the Google client libraries installed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from ..config import GMAIL_SCOPES, Settings
from ..errors import AuthError

SETUP_HINT = (
    "Create an OAuth 2.0 'Desktop app' client in Google Cloud Console "
    "(APIs & Services > Credentials), enable the Gmail API, download the JSON "
    "and save it as credentials.json (or set GOOGLE_CREDENTIALS_PATH)."
)


def _import_google() -> tuple[Any, Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise AuthError(
            "Google client libraries are not installed. Run: pip install -r requirements.txt "
            "(or use --mock)."
        ) from exc
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover
        raise
    except BaseException as exc:  # pragma: no cover - e.g. a broken native 'cryptography' build
        raise AuthError(
            f"Google client libraries failed to import ({type(exc).__name__}: {exc}). "
            "Try: pip install --upgrade cryptography cffi google-auth (or use --mock)."
        ) from exc
    return Request, Credentials, InstalledAppFlow


def load_credentials(
    credentials_path: Path,
    token_path: Path,
    scopes: Sequence[str] = GMAIL_SCOPES,
    interactive: bool = True,
) -> Any:
    """Return valid ``google.oauth2.credentials.Credentials``.

    Order: cached token -> silent refresh -> interactive consent (if allowed).
    """
    Request, Credentials, InstalledAppFlow = _import_google()
    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), list(scopes))
        except (ValueError, KeyError) as exc:
            raise AuthError(f"Stored token at {token_path} is unreadable: {exc}") from exc

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            return creds
        except Exception as exc:  # noqa: BLE001 - refresh errors are varied
            if not interactive:
                raise AuthError(f"Token refresh failed: {exc}") from exc
            creds = None

    if not interactive:
        raise AuthError(f"No valid Google token at {token_path}; run `jarvis --auth` first.")
    if not credentials_path.exists():
        raise AuthError(f"Google OAuth client file not found at {credentials_path}. {SETUP_HINT}")

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), list(scopes))
    creds = flow.run_local_server(port=0, prompt="consent")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    return creds


def credentials_from_settings(settings: Settings, interactive: bool = True) -> Any:
    return load_credentials(
        settings.google_credentials_path, settings.google_token_path, GMAIL_SCOPES, interactive
    )


def token_status(settings: Settings) -> dict[str, Any]:
    """Describe the auth state without triggering a browser flow."""
    return {
        "credentials_file": str(settings.google_credentials_path),
        "credentials_present": settings.google_credentials_path.exists(),
        "token_file": str(settings.google_token_path),
        "token_present": settings.google_token_path.exists(),
    }
