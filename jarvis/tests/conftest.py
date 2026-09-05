"""Shared fixtures."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jarvis.config import MOCK_DATA_DIR, Settings  # noqa: E402
from jarvis.connectors.gmail import MockMailSource  # noqa: E402
from jarvis.models import EmailMessage  # noqa: E402

NOW = datetime(2026, 9, 5, 4, 0, tzinfo=timezone.utc)  # 14:00 AEST on a Saturday


@pytest.fixture
def now() -> datetime:
    return NOW


@pytest.fixture
def settings() -> Settings:
    return Settings(mock=True, voice_engine="none", animate=False, hud=False)


@pytest.fixture
def mail(now: datetime) -> MockMailSource:
    return MockMailSource.from_json(MOCK_DATA_DIR / "emails.json", now=now)


def make_email(**overrides) -> EmailMessage:
    base = dict(
        id="m1",
        thread_id="t1",
        sender="Someone <someone@example.com>",
        to="martin@orbit3.io",
        subject="Hello",
        date=NOW,
        snippet="",
        body="",
        labels=["INBOX"],
        headers={},
    )
    base.update(overrides)
    return EmailMessage(**base)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, chunks=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self._chunks = chunks or []
        self.text = text

    def json(self):
        return self._payload

    def iter_content(self, chunk_size=4096):
        yield from self._chunks


class FakeSession:
    """Records calls and returns canned responses."""

    def __init__(self, response: FakeResponse, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def _record(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        if self.error:
            raise self.error
        return self.response

    def get(self, url, **kwargs):
        return self._record("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._record("POST", url, **kwargs)
