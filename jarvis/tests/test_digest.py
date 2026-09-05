from datetime import timedelta

from jarvis.config import Settings
from jarvis.connectors.gmail import FailingMailSource
from jarvis.modules.orbit3_digest import TaskDigestService, extract_due, extract_tasks, urgency_reason

from conftest import NOW, make_email


def test_urgency_from_header_subject_and_body():
    assert urgency_reason(make_email(headers={"importance": "high"})) == "the sender marked it high importance"
    assert urgency_reason(make_email(subject="URGENT: help")) == "it is marked urgent"
    assert urgency_reason(make_email(subject="[P1] Critical disk", body="Immediate action required")) == "it carries a critical severity"
    assert urgency_reason(make_email(body="The invoice is overdue")) == "something is overdue"
    assert urgency_reason(make_email(subject="Lunch?", body="Fancy a sandwich?")) is None


def test_extract_due_variants():
    assert extract_due("please send it by COB Wednesday") == "COB Wednesday"
    assert extract_due("due Friday") == "Friday"
    assert extract_due("before 12 Sept 2026") == "12 Sept 2026"
    assert extract_due("by tomorrow morning") == "Tomorrow"
    assert extract_due("no date here") is None


def test_checklist_items_inherit_due_from_intro():
    msg = make_email(
        sender="James Okafor <james@vanta.com>",
        subject="SOC 2 evidence request - due Friday",
        body="Hi Martin,\n\nCould you upload the following evidence by Friday:\n\n- [ ] Access review sign-off\n- [ ] Vendor risk register\n\nThanks",
    )
    tasks = extract_tasks(msg)
    assert [t.title for t in tasks] == ["Access review sign-off", "Vendor risk register"]
    assert all(t.due == "Friday" and t.priority == "normal" for t in tasks)
    assert tasks[0].sender == "James Okafor"


def test_request_prefixes_are_stripped_and_deduped():
    msg = make_email(body="Could you review the draft before Thursday?\n\n1. Could you review the draft before Thursday?\n2. Reminder: the invoice is overdue - please chase")
    titles = [t.title for t in extract_tasks(msg)]
    assert titles == ["Review the draft before Thursday", "Reminder: the invoice is overdue - please chase"]


def test_item_level_priority():
    msg = make_email(body="1. Fix the outage immediately\n2. No rush, but water the plant at some point\n3. Send the report by COB today")
    by_title = {t.title: t for t in extract_tasks(msg)}
    assert by_title["Fix the outage immediately"].priority == "urgent"
    assert by_title["No rush, but water the plant at some point"].priority == "normal"
    assert by_title["Send the report by COB today"].priority == "high"


def test_single_task_inherits_message_urgency():
    msg = make_email(subject="URGENT", body="Please call me on 0412 555 019.")
    tasks = extract_tasks(msg)
    assert len(tasks) == 1 and tasks[0].priority == "urgent" and tasks[0].title.startswith("Call me")


def test_bulk_mail_is_skipped():
    newsletter = make_email(sender="Cloudflare <noreply@notify.cloudflare.com>", body="Please review your dashboard.",
                            headers={"list-unsubscribe": "<x>"})
    assert extract_tasks(newsletter) == []
    category = make_email(body="Please renew now", labels=["INBOX", "CATEGORY_PROMOTIONS"])
    assert extract_tasks(category) == []


def test_subject_todo_fallback():
    tasks = extract_tasks(make_email(subject="TODO: renew domain", body="It lapses soon."))
    assert [t.title for t in tasks] == ["Renew domain"]


def test_service_query_and_digest(mail):
    settings = Settings(mock=True, orbit3_lookback_days=3)
    svc = TaskDigestService(mail, settings)
    assert svc.query() == "to:martin@orbit3.io newer_than:3d -from:support@auravest.ai -label:SENT"
    digest = svc.fetch()
    assert digest.error is None and digest.scanned == 7
    assert [u.sender for u in digest.urgent] == ["Rachel Nguyen", "Datadog Monitoring", "Lucy Bennett"]
    assert [t.priority for t in digest.tasks] == sorted([t.priority for t in digest.tasks], key={"urgent": 0, "high": 1, "normal": 2}.get)
    titles = [t.title for t in digest.tasks]
    assert "Call me on 0412 555 019 as soon as you see this" in titles
    assert "Access review sign-off for Q3" in titles
    assert not any("Cloudflare" in t.sender for t in digest.tasks)
    assert not any(t.message_id == "o3-108" for t in digest.tasks)  # sent mail excluded
    assert not any(t.message_id == "o3-109" for t in digest.tasks)  # outside look-back


def test_service_excludes_principal_sender(now):
    from jarvis.connectors.gmail import MockMailSource

    own = make_email(id="own", sender="Martin Ozekin <martin@orbit3.io>", to="martin@orbit3.io", subject="URGENT note to self",
                     body="Please remember the keys", date=now - timedelta(hours=1))
    digest = TaskDigestService(MockMailSource([own], now=now), Settings(mock=True)).fetch()
    assert digest.tasks == [] and digest.urgent == []


def test_service_reports_connector_error():
    digest = TaskDigestService(FailingMailSource("token expired"), Settings(mock=True)).fetch()
    assert digest.error == "token expired" and digest.tasks == [] and digest.urgent == []
