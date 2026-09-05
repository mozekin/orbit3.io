"""Mail sources: the live Gmail API connector and an offline mock.

Both expose the same tiny interface::

    source.search(query, max_results) -> list[EmailMessage]

The mock understands enough Gmail search syntax (``from:``, ``to:``,
``subject:``, ``newer_than:Nd``, ``is:unread``, ``label:``, negation with ``-``
and quoted free text) to exercise the real queries the modules build.
"""
from __future__ import annotations

import base64
import html
import json
import re
import shlex
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable, Protocol

from ..config import MOCK_DATA_DIR, Settings
from ..errors import ConnectorError
from ..models import EmailMessage, extract_email


class MailSource(Protocol):
    name: str

    def search(self, query: str, max_results: int = 50) -> list[EmailMessage]: ...


# --------------------------------------------------------------------------- helpers
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")


def html_to_text(markup: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", markup)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</tr>|</h[1-6]>", "\n", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text).replace("\xa0", " ")
    lines = [_WS_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _b64url_decode(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def extract_body(payload: dict[str, Any]) -> str:
    """Pick the best text body from a Gmail message payload (prefers text/plain)."""
    plain: list[str] = []
    rich: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime = part.get("mimeType", "")
        body = part.get("body", {}) or {}
        data = body.get("data")
        if data and mime == "text/plain":
            plain.append(_b64url_decode(data))
        elif data and mime == "text/html":
            rich.append(html_to_text(_b64url_decode(data)))
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    if plain:
        return "\n".join(plain).strip()
    if rich:
        return "\n".join(rich).strip()
    return ""


def parse_date(value: str | None, fallback_ms: str | None = None) -> datetime:
    if value:
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (TypeError, ValueError):
            pass
    if fallback_ms:
        return datetime.fromtimestamp(int(fallback_ms) / 1000, tz=timezone.utc)
    return datetime.now(timezone.utc)


def message_from_gmail(raw: dict[str, Any]) -> EmailMessage:
    payload = raw.get("payload", {}) or {}
    headers = {h["name"].lower(): h.get("value", "") for h in payload.get("headers", []) or []}
    return EmailMessage(
        id=raw.get("id", ""),
        thread_id=raw.get("threadId", ""),
        sender=headers.get("from", ""),
        to=headers.get("to", ""),
        subject=headers.get("subject", "(no subject)"),
        date=parse_date(headers.get("date"), raw.get("internalDate")),
        snippet=html.unescape(raw.get("snippet", "") or ""),
        body=extract_body(payload),
        labels=list(raw.get("labelIds", []) or []),
        headers=headers,
    )


# --------------------------------------------------------------------------- live
class GmailConnector:
    """Read-only Gmail connector backed by the official API client."""

    name = "gmail"

    def __init__(self, credentials: Any, user_id: str = "me") -> None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:  # pragma: no cover
            raise ConnectorError("google-api-python-client is not installed.") from exc
        self._service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        self._user = user_id

    @classmethod
    def from_settings(cls, settings: Settings, interactive: bool = True) -> "GmailConnector":
        from .google_auth import credentials_from_settings

        return cls(credentials_from_settings(settings, interactive=interactive))

    def search(self, query: str, max_results: int = 50) -> list[EmailMessage]:
        try:
            listing = (
                self._service.users()
                .messages()
                .list(userId=self._user, q=query, maxResults=max_results)
                .execute()
            )
            out: list[EmailMessage] = []
            for ref in listing.get("messages", []) or []:
                raw = (
                    self._service.users()
                    .messages()
                    .get(userId=self._user, id=ref["id"], format="full")
                    .execute()
                )
                out.append(message_from_gmail(raw))
            out.sort(key=lambda m: m.date, reverse=True)
            return out
        except ConnectorError:
            raise
        except Exception as exc:  # noqa: BLE001 - googleapiclient raises many types
            raise ConnectorError(f"Gmail query failed: {exc}") from exc


# --------------------------------------------------------------------------- mock
class GmailQuery:
    """A tiny interpreter for the subset of Gmail search syntax the app uses."""

    _NEWER = re.compile(r"^(\d+)([dhm])$")

    def __init__(self, query: str, now: datetime | None = None) -> None:
        self.now = now or datetime.now(timezone.utc)
        self.terms: list[tuple[bool, str, str]] = []  # (negated, field, value)
        for token in shlex.split(query or ""):
            negated = token.startswith("-")
            token = token[1:] if negated else token
            if ":" in token:
                field, _, value = token.partition(":")
                self.terms.append((negated, field.lower(), value))
            else:
                self.terms.append((negated, "text", token))

    def _newer_than(self, spec: str) -> datetime:
        m = self._NEWER.match(spec)
        if not m:
            raise ValueError(f"Unsupported newer_than spec: {spec}")
        n, unit = int(m.group(1)), m.group(2)
        delta = {"d": timedelta(days=n), "h": timedelta(hours=n), "m": timedelta(days=30 * n)}[unit]
        return self.now - delta

    def _match_term(self, field: str, value: str, msg: EmailMessage) -> bool:
        v = value.lower()
        if field == "from":
            return v in msg.sender.lower()
        if field == "to":
            return v in msg.to.lower()
        if field == "subject":
            return v in msg.subject.lower()
        if field == "newer_than":
            return msg.date >= self._newer_than(v)
        if field == "older_than":
            return msg.date < self._newer_than(v)
        if field == "is":
            if v == "unread":
                return "UNREAD" in msg.labels
            if v == "read":
                return "UNREAD" not in msg.labels
            return v.upper() in msg.labels
        if field == "label":
            return v.upper().replace("-", "_") in {l.upper() for l in msg.labels}
        if field == "text":
            return v in msg.text.lower() or v in msg.sender.lower()
        raise ValueError(f"Unsupported query field: {field}")

    def matches(self, msg: EmailMessage) -> bool:
        for negated, field, value in self.terms:
            hit = self._match_term(field, value, msg)
            if hit == negated:
                return False
        return True


class MockMailSource:
    """Serves fixture emails from JSON and filters them with :class:`GmailQuery`."""

    name = "mock-gmail"

    def __init__(self, messages: Iterable[EmailMessage], now: datetime | None = None) -> None:
        self.messages = sorted(messages, key=lambda m: m.date, reverse=True)
        self.now = now or datetime.now(timezone.utc)
        self.queries: list[str] = []

    @classmethod
    def from_json(cls, path: Path | None = None, now: datetime | None = None) -> "MockMailSource":
        path = path or MOCK_DATA_DIR / "emails.json"
        now = now or datetime.now(timezone.utc)
        try:
            records = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConnectorError(f"Cannot load mock emails from {path}: {exc}") from exc
        return cls([cls._record_to_message(r, now) for r in records], now=now)

    @staticmethod
    def _record_to_message(rec: dict[str, Any], now: datetime) -> EmailMessage:
        if "age_hours" in rec:
            when = now - timedelta(hours=float(rec["age_hours"]))
        else:
            when = datetime.fromisoformat(rec["date"])
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        body = rec.get("body", "")
        if rec.get("html"):
            body = html_to_text(rec["html"])
        return EmailMessage(
            id=rec.get("id", f"mock-{abs(hash(rec.get('subject', '')))}"),
            thread_id=rec.get("thread_id", rec.get("id", "")),
            sender=rec.get("from", ""),
            to=rec.get("to", ""),
            subject=rec.get("subject", "(no subject)"),
            date=when,
            snippet=rec.get("snippet") or body[:160],
            body=body,
            labels=list(rec.get("labels", ["INBOX"])),
            headers={k.lower(): v for k, v in (rec.get("headers") or {}).items()},
        )

    def search(self, query: str, max_results: int = 50) -> list[EmailMessage]:
        self.queries.append(query)
        q = GmailQuery(query, now=self.now)
        return [m for m in self.messages if q.matches(m)][:max_results]


class FailingMailSource:
    """A mail source that always raises - used to exercise error narration."""

    name = "failing-gmail"

    def __init__(self, message: str = "simulated outage") -> None:
        self.message = message

    def search(self, query: str, max_results: int = 50) -> list[EmailMessage]:
        raise ConnectorError(self.message)


def mail_source_from_settings(settings: Settings, interactive: bool = True) -> MailSource:
    if settings.mock:
        return MockMailSource.from_json()
    return GmailConnector.from_settings(settings, interactive=interactive)


__all__ = [
    "MailSource",
    "GmailConnector",
    "MockMailSource",
    "FailingMailSource",
    "GmailQuery",
    "message_from_gmail",
    "extract_body",
    "html_to_text",
    "mail_source_from_settings",
    "extract_email",
]
