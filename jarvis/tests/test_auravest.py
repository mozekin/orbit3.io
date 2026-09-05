from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from jarvis.config import Settings
from jarvis.connectors.gmail import FailingMailSource, MockMailSource
from jarvis.modules.auravest import AuravestSignupService, _parse_timestamp, is_signup_notification, parse_signup

from conftest import NOW, make_email

SYD = ZoneInfo("Australia/Sydney")


def test_parse_key_value_notification():
    msg = make_email(
        sender="support@auravest.ai",
        subject="[Auravest] New signup: Priya Raman (priya@northwindcapital.com.au)",
        body="Name: Priya Raman\nEmail: priya@northwindcapital.com.au\nCompany: Northwind Capital\nPlan: Professional\nSigned up: 2026-09-05 06:41 AEST\nSource: Organic search",
    )
    s = parse_signup(msg, SYD)
    assert s is not None
    assert (s.name, s.email, s.company, s.plan) == ("Priya Raman", "priya@northwindcapital.com.au", "Northwind Capital", "Professional")
    assert s.signed_up_at == datetime(2026, 9, 5, 6, 41, tzinfo=timezone(timedelta(hours=10)))
    assert s.extra["source"] == "Organic search"
    assert s.source_message_id == "m1"


def test_parse_json_notification():
    msg = make_email(
        sender="support@auravest.ai",
        subject="Auravest signup notification",
        body='Operational notification.\n{"event": "user.signup", "user": {"full_name": "Tom Halloran", "email": "tom@gmail.com"}, "plan": "Starter", "company": "", "created_at": "2026-09-05T01:12:09+10:00"}\nThanks',
    )
    s = parse_signup(msg)
    assert s is not None
    assert (s.name, s.email, s.plan, s.company) == ("Tom Halloran", "tom@gmail.com", "Starter", "")
    assert s.signed_up_at.isoformat() == "2026-09-05T01:12:09+10:00"


def test_parse_html_table_notification(mail):
    msg = next(m for m in mail.messages if m.id == "av-003")
    s = parse_signup(msg)
    assert s is not None
    assert s.name == "Dr. Elena Vasquez"
    assert s.email == "e.vasquez@sydneyhealthgroup.org"
    assert s.company == "Sydney Health Group"
    assert s.plan == "Enterprise Trial"


def test_parse_subject_only_notification():
    msg = make_email(sender="support@auravest.ai", subject="New signup: Sam Whitcombe (sam@whitcombe.dev)", body="")
    s = parse_signup(msg)
    assert s is not None and s.name == "Sam Whitcombe" and s.email == "sam@whitcombe.dev"
    assert s.signed_up_at == NOW  # falls back to the message date


def test_non_signup_mail_is_ignored():
    msg = make_email(sender="support@auravest.ai", subject="Auravest weekly usage report", body="Active users: 412")
    assert not is_signup_notification(msg)
    assert parse_signup(msg) is None


def test_signup_without_identity_is_ignored():
    msg = make_email(sender="support@auravest.ai", subject="New signup", body="Something went wrong rendering this notification.")
    assert parse_signup(msg) is None


def test_timestamp_parsing_variants():
    assert _parse_timestamp("2026-09-05 06:41 AEST").utcoffset() == timedelta(hours=10)
    assert _parse_timestamp("2026-09-05T01:12:09+10:00").hour == 1
    assert _parse_timestamp("2026-09-05", SYD).tzinfo == SYD
    assert _parse_timestamp("05/09/2026 14:30").day == 5
    assert _parse_timestamp("not a date") is None
    assert _parse_timestamp("") is None


def test_service_builds_query_and_dedupes(now):
    settings = Settings(mock=True, auravest_lookback_days=1)
    dup = make_email(id="dup", sender="support@auravest.ai", subject="New signup: Priya Raman (priya@northwindcapital.com.au)",
                     body="Name: Priya Raman\nEmail: priya@northwindcapital.com.au", date=now - timedelta(hours=1))
    base = MockMailSource.from_json(now=now)
    mail = MockMailSource([*base.messages, dup], now=now)
    svc = AuravestSignupService(mail, settings)
    assert svc.query() == "from:support@auravest.ai newer_than:1d"
    report = svc.fetch()
    assert report.count == 3
    assert [s.name for s in report.signups] == ["Priya Raman", "Tom Halloran", "Dr. Elena Vasquez"]
    assert report.scanned == 5 and report.error is None


def test_service_lookback_override(mail):
    report = AuravestSignupService(mail, Settings(mock=True)).fetch(lookback_days=7)
    assert report.lookback_days == 7
    assert "Sam Whitcombe" in [s.name for s in report.signups]


def test_service_reports_connector_error():
    report = AuravestSignupService(FailingMailSource("gmail down"), Settings(mock=True)).fetch()
    assert report.count == 0 and report.error == "gmail down"
