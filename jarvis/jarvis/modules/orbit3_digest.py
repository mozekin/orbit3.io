"""Orbit3 task digest: outstanding tasks and urgent communications for
martin@orbit3.io, extracted from recent mail with lightweight heuristics.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from ..config import Settings
from ..connectors.gmail import MailSource
from ..errors import JarvisError
from ..models import EmailMessage, Task, TasksDigest, UrgentMessage, extract_display_name

URGENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\burgent\b", re.I), "it is marked urgent"),
    (re.compile(r"\basap\b|as soon as (you can|possible)", re.I), "it asks for action as soon as possible"),
    (re.compile(r"\bimmediately\b|immediate action", re.I), "it demands immediate action"),
    (re.compile(r"\b(outage|down|unreachable|lost connectivity|halt(ed)?)\b", re.I), "it reports a service outage"),
    (re.compile(r"\b(critical|sev\s?-?1|p1|priority 1)\b", re.I), "it carries a critical severity"),
    (re.compile(r"\boverdue\b", re.I), "something is overdue"),
    (re.compile(r"\b(deadline|due) (today|tomorrow|by (cob|eod|end of day))\b", re.I), "a deadline is imminent"),
    (re.compile(r"\b(security incident|breach|compromised)\b", re.I), "it concerns a security incident"),
]

TASK_LINE_RES: list[re.Pattern[str]] = [
    re.compile(r"^\s*[-*]\s*\[\s?\]\s*(.+)$"),                     # - [ ] checklist
    re.compile(r"^\s*(?:todo|action item|action required|task)\s*[:\-]\s*(.+)$", re.I),
    re.compile(r"^\s*\d+[.)]\s*(.+)$"),                              # 1. numbered items
]
REQUEST_RE = re.compile(
    r"\b(?:could|can|would|will) you(?: please)?\s+([^.?!\n]{6,160})|"
    r"\bplease\s+((?!find|see|note|let me know)[a-z][^.?!\n]{4,160})|"
    r"\bwe need (?:you|someone(?: from \w+)?) to\s+([^.?!\n]{4,160})",
    re.I,
)
DUE_RE = re.compile(
    r"\b(?:by|before|due|until|no later than)\s+"
    r"((?:cob|eod|end of (?:day|week|month))(?:\s+\w+)?|"
    r"(?:mon|tues|wednes|thurs|fri|satur|sun)day|tomorrow|today|"
    r"\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\w*(?:\s+\d{4})?|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\w*\s+\d{1,2}(?:st|nd|rd|th)?)",
    re.I,
)
NEAR_DUE_RE = re.compile(r"^(today|tomorrow|cob|eod)", re.I)
LOW_PRIORITY_RE = re.compile(r"no rush|when you (get|have) a (chance|moment)|at some point|whenever", re.I)

NEWSLETTER_SENDER_RE = re.compile(r"no-?reply|newsletter|digest|marketing|notifications?@|news@", re.I)
ALERT_SENDER_RE = re.compile(r"alert|monitor|pagerduty|opsgenie|datadog|dtdg|statuspage|uptime", re.I)


def _is_bulk_mail(msg: EmailMessage) -> bool:
    headers = {k.lower(): v for k, v in msg.headers.items()}
    if "list-unsubscribe" in headers or headers.get("precedence", "").lower() in {"bulk", "list"}:
        return True
    if any(l.startswith("CATEGORY_") and l != "CATEGORY_PERSONAL" for l in msg.labels):
        return True
    return bool(NEWSLETTER_SENDER_RE.search(msg.sender)) and not ALERT_SENDER_RE.search(msg.sender)


def _is_from_principal(msg: EmailMessage, settings: Settings) -> bool:
    return settings.principal_email.lower() in msg.sender.lower() or "SENT" in msg.labels


def text_urgency(text: str) -> str | None:
    """Return the first urgency reason matching ``text``, or ``None``."""
    for pattern, reason in URGENT_PATTERNS:
        if pattern.search(text):
            return reason
    return None


def urgency_reason(msg: EmailMessage) -> str | None:
    """Return why a message is urgent, or ``None``. Subject is checked before body."""
    headers = {k.lower(): v.lower() for k, v in msg.headers.items()}
    if headers.get("importance") == "high" or headers.get("x-priority", "").startswith("1"):
        return "the sender marked it high importance"
    return text_urgency(msg.subject) or text_urgency((msg.body or msg.snippet)[:600])


_REQUEST_PREFIX_RE = re.compile(r"^(?:(?:could|can|would|will) you(?: please)?|please|kindly)\s+", re.I)


def _clean_task(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" -:;,.?!")
    text = _REQUEST_PREFIX_RE.sub("", text).strip(" -:;,.?!")
    return text[0].upper() + text[1:] if text else text


def extract_due(text: str) -> str | None:
    m = DUE_RE.search(text)
    if not m:
        return None
    due = m.group(1).strip()
    words = due.split()
    if words[0].lower() in {"cob", "eod"}:
        return " ".join([words[0].upper(), *[w.title() for w in words[1:]]])
    return due.title()


def extract_tasks(msg: EmailMessage) -> list[Task]:
    """Pull actionable items out of one message.

    Priority rules: an item is *urgent* when its own text is urgent, or when the
    whole message is urgent and it is the only item; *high* when it is due
    today/tomorrow/COB; otherwise *normal*. Phrases like "no rush" demote.
    """
    if _is_bulk_mail(msg):
        return []
    body = msg.body or msg.snippet
    message_reason = urgency_reason(msg)
    sender = extract_display_name(msg.sender)
    candidates: list[tuple[str, str | None, str]] = []  # (title, due, context)

    # Explicit list items inherit a due date only from the text that introduces the list.
    lines = body.splitlines()
    first_item = next(
        (i for i, line in enumerate(lines) if any(p.match(line) for p in TASK_LINE_RES)), None
    )
    intro = "\n".join(lines[:first_item]) if first_item is not None else ""
    intro_due = extract_due(msg.subject) or extract_due(intro)
    for line in lines:
        for pattern in TASK_LINE_RES:
            m = pattern.match(line)
            if m:
                item = m.group(1)
                candidates.append((item, extract_due(item) or intro_due, item))
                break
    has_list = bool(candidates)

    for m in REQUEST_RE.finditer(body):
        item = next(g for g in m.groups() if g)
        if has_list and re.search(r"\bfollowing\b|\bbelow\b", item, re.I):
            continue  # "upload the following:" is the list's heading, not a task
        context = body[max(0, m.start() - 80) : m.end() + 80]
        candidates.append((item, extract_due(context) or (intro_due if not has_list else None), context))

    # Subject-only reminders (e.g. "TODO: renew domain") when nothing else was found
    if not candidates:
        m = TASK_LINE_RES[1].match(msg.subject)
        if m:
            candidates.append((m.group(1), intro_due, msg.subject))

    tasks: list[Task] = []
    seen: set[str] = set()
    for raw, due, context in candidates:
        title = _clean_task(raw)
        key = re.sub(r"[^a-z0-9 ]", "", title.lower())[:60]
        if not title or key in seen or len(title.split()) < 2:
            continue
        seen.add(key)
        low = bool(LOW_PRIORITY_RE.search(context))
        item_urgent = text_urgency(context) is not None or (message_reason and len(candidates) == 1)
        if item_urgent and not low:
            priority = "urgent"
        elif due and NEAR_DUE_RE.match(due) and not low:
            priority = "high"
        else:
            priority = "normal"
        tasks.append(
            Task(
                title=title,
                source_subject=msg.subject,
                sender=sender,
                message_id=msg.id,
                priority=priority,
                due=due,
                received=msg.date,
            )
        )
    return tasks


_PRIORITY_RANK = {"urgent": 0, "high": 1, "normal": 2}


class TaskDigestService:
    """Build the Orbit3 digest of tasks and urgent communications."""

    def __init__(self, mail: MailSource, settings: Settings) -> None:
        self.mail = mail
        self.settings = settings

    def query(self, lookback_days: int | None = None) -> str:
        days = lookback_days or self.settings.orbit3_lookback_days
        return (
            f"to:{self.settings.principal_email} newer_than:{days}d "
            f"-from:{self.settings.auravest_sender} -label:SENT"
        )

    def fetch(self, lookback_days: int | None = None, max_results: int = 100) -> TasksDigest:
        days = lookback_days or self.settings.orbit3_lookback_days
        now = datetime.now(timezone.utc)
        try:
            messages = self.mail.search(self.query(days), max_results=max_results)
        except JarvisError as exc:
            return TasksDigest(tasks=[], urgent=[], lookback_days=days, scanned=0, generated_at=now, error=str(exc))

        tasks: list[Task] = []
        urgent: list[UrgentMessage] = []
        for msg in messages:
            if _is_from_principal(msg, self.settings):
                continue
            reason = urgency_reason(msg)
            if reason and not _is_bulk_mail(msg):
                urgent.append(
                    UrgentMessage(
                        sender=extract_display_name(msg.sender),
                        subject=msg.subject,
                        reason=reason,
                        message_id=msg.id,
                        received=msg.date,
                        snippet=msg.snippet[:160],
                    )
                )
            tasks.extend(extract_tasks(msg))

        tasks.sort(key=lambda t: (_PRIORITY_RANK.get(t.priority, 9), -(t.received.timestamp() if t.received else 0)))
        urgent.sort(key=lambda u: -(u.received.timestamp() if u.received else 0))
        return TasksDigest(tasks=tasks, urgent=urgent, lookback_days=days, scanned=len(messages), generated_at=now)
