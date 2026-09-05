import base64
from datetime import timedelta

import pytest

from jarvis.connectors.gmail import (
    FailingMailSource,
    GmailQuery,
    MockMailSource,
    extract_body,
    html_to_text,
    message_from_gmail,
)
from jarvis.errors import ConnectorError
from jarvis.models import extract_display_name, extract_email

from conftest import NOW, make_email


def test_extract_email_and_name():
    assert extract_email("Jane Doe <Jane@X.com>") == "jane@x.com"
    assert extract_email("jane@x.com") == "jane@x.com"
    assert extract_display_name("Jane Doe <jane@x.com>") == "Jane Doe"
    assert extract_display_name("jane.doe@x.com") == "Jane Doe"


def test_html_to_text_strips_markup_and_scripts():
    text = html_to_text("<html><style>p{}</style><body><p>Hello&nbsp;<b>world</b></p><script>x()</script><div>Bye</div></body></html>")
    assert text.splitlines() == ["Hello world", "Bye"]


def _b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def test_extract_body_prefers_plain_over_html():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/html", "body": {"data": _b64("<p>rich</p>")}},
            {"mimeType": "text/plain", "body": {"data": _b64("plain")}},
        ],
    }
    assert extract_body(payload) == "plain"
    assert extract_body({"mimeType": "text/html", "body": {"data": _b64("<p>only html</p>")}}) == "only html"
    assert extract_body({"mimeType": "text/plain", "body": {}}) == ""


def test_message_from_gmail_parses_headers_and_date():
    raw = {
        "id": "abc",
        "threadId": "t",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Hi &amp; bye",
        "internalDate": "1757044800000",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "A <a@x.com>"},
                {"name": "To", "value": "martin@orbit3.io"},
                {"name": "Subject", "value": "Test"},
                {"name": "Date", "value": "Sat, 05 Sep 2026 14:00:00 +1000"},
            ],
            "body": {"data": _b64("body text")},
        },
    }
    msg = message_from_gmail(raw)
    assert msg.id == "abc" and msg.sender_email == "a@x.com" and msg.subject == "Test"
    assert msg.body == "body text" and msg.snippet == "Hi & bye"
    assert msg.date.utcoffset() == timedelta(hours=10)
    assert "UNREAD" in msg.labels


def test_message_date_falls_back_to_internal_date():
    raw = {"id": "x", "internalDate": "1757044800000", "payload": {"headers": [], "body": {}}}
    assert message_from_gmail(raw).date.isoformat() == "2025-09-05T04:00:00+00:00"


@pytest.mark.parametrize(
    "query,expected",
    [
        ("from:auravest", True),
        ("from:nobody", False),
        ("-from:auravest", False),
        ("to:martin@orbit3.io", True),
        ("subject:signup", True),
        ("newer_than:1d", True),
        ("newer_than:1h", False),
        ("is:unread", True),
        ("label:inbox", True),
        ("-label:SENT", True),
        ('"new signup"', True),
        ("from:auravest newer_than:2d -label:SENT", True),
    ],
)
def test_gmail_query_matching(query, expected):
    msg = make_email(sender="Auravest <support@auravest.ai>", subject="New signup: X", labels=["INBOX", "UNREAD"],
                     date=NOW - timedelta(hours=5))
    assert GmailQuery(query, now=NOW).matches(msg) is expected


def test_gmail_query_rejects_unknown_field():
    with pytest.raises(ValueError):
        GmailQuery("has:attachment", now=NOW).matches(make_email())


def test_mock_source_loads_fixture_sorted_and_filters(mail):
    assert mail.messages == sorted(mail.messages, key=lambda m: m.date, reverse=True)
    hits = mail.search("from:support@auravest.ai newer_than:1d")
    assert [m.id for m in hits] == ["av-001", "av-002", "av-003", "av-004"]
    assert mail.queries == ["from:support@auravest.ai newer_than:1d"]
    assert len(mail.search("from:support@auravest.ai", max_results=2)) == 2


def test_mock_source_html_records_are_converted(mail):
    msg = next(m for m in mail.messages if m.id == "av-003")
    assert "<table>" not in msg.body and "Dr. Elena Vasquez" in msg.body


def test_mock_source_missing_file(tmp_path):
    with pytest.raises(ConnectorError):
        MockMailSource.from_json(tmp_path / "nope.json")


def test_failing_source_raises():
    with pytest.raises(ConnectorError, match="boom"):
        FailingMailSource("boom").search("anything")
