"""Parse Auravest operational signup notifications from support@auravest.ai.

The notification format has varied over time (key/value text, an embedded JSON
event, an HTML table, or just the subject line), so the parser tries each in
turn and merges whatever it finds.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

from ..config import Settings
from ..connectors.gmail import MailSource
from ..errors import JarvisError
from ..models import EmailMessage, Signup, SignupReport

SIGNUP_SUBJECT_RE = re.compile(r"sign[\s-]?up|signed up|new (user|account|customer|registration)|registered", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SUBJECT_NAME_RE = re.compile(r"(?:sign[\s-]?up|new (?:user|account|customer))\s*[:\-]\s*([^(<\n]+?)\s*(?:\(|<|$)", re.I)

_FIELD_ALIASES = {
    "name": ("name", "full name", "full_name", "user", "customer", "contact"),
    "email": ("email", "e-mail", "email address", "user email"),
    "company": ("company", "organisation", "organization", "org", "business", "account name"),
    "plan": ("plan", "tier", "subscription", "package"),
    "signed_up_at": ("signed up", "signed_up", "created", "created_at", "date", "registered", "timestamp"),
    "source": ("source", "referrer", "channel", "utm_source"),
}

_KV_RE = re.compile(r"^\s*([A-Za-z][A-Za-z _-]{1,30}?)\s*[:=]\s*(.+?)\s*$")


def _canonical(key: str) -> str | None:
    k = key.strip().lower().replace("-", " ").replace("_", " ")
    for canon, aliases in _FIELD_ALIASES.items():
        if k in {a.replace("_", " ") for a in aliases}:
            return canon
    return None


def _parse_kv_lines(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        m = _KV_RE.match(line)
        if not m:
            continue
        canon = _canonical(m.group(1))
        if canon and canon not in found:
            found[canon] = m.group(2).strip()
    return found


def _parse_html_table_text(text: str) -> dict[str, str]:
    """html_to_text renders <td>Name</td><td>Value</td> as 'Name Value' on one line."""
    found: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        canon = _canonical(parts[0])
        if canon and canon not in found:
            found[canon] = parts[1].strip()
        elif line.lower().startswith("organisation ") or line.lower().startswith("organization "):
            found.setdefault("company", line.split(None, 1)[1].strip())
    return found


def _flatten_json(obj: object, prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            flat.update(_flatten_json(v, f"{prefix}{k}."))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flat.update(_flatten_json(v, f"{prefix}{i}."))
    else:
        flat[prefix.rstrip(".")] = "" if obj is None else str(obj)
    return flat


def _parse_json_block(text: str) -> dict[str, str]:
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
                    found: dict[str, str] = {}
                    for key, value in _flatten_json(data).items():
                        canon = _canonical(key.split(".")[-1])
                        if canon and value and canon not in found:
                            found[canon] = value
                    return found
        start = text.find("{", start + 1)
    return {}


_TZ_ABBREVIATIONS = {
    "AEST": 10, "AEDT": 11, "ACST": 9.5, "ACDT": 10.5, "AWST": 8,
    "NZST": 12, "NZDT": 13, "UTC": 0, "GMT": 0, "BST": 1,
    "EST": -5, "EDT": -4, "PST": -8, "PDT": -7,
}


def _parse_timestamp(value: str | None, default_tz: tzinfo = timezone.utc) -> datetime | None:
    """Parse the many timestamp shapes seen in notifications.

    Naive timestamps are assumed to be in ``default_tz``; a trailing zone
    abbreviation such as ``AEST`` is honoured when known.
    """
    if not value:
        return None
    value = value.strip()
    tz: tzinfo = default_tz
    m = re.match(r"^(.*?)\s+([A-Z]{3,4})$", value)
    if m and m.group(2) in _TZ_ABBREVIATIONS:
        value = m.group(1)
        tz = timezone(timedelta(hours=_TZ_ABBREVIATIONS[m.group(2)]))
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d %b %Y %H:%M", "%d %b %Y"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=tz)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=tz)
    except ValueError:
        return None


def is_signup_notification(msg: EmailMessage) -> bool:
    return bool(SIGNUP_SUBJECT_RE.search(msg.subject)) or bool(
        re.search(r"(new user has signed up|user\.signup|new account created)", msg.text, re.I)
    )


def parse_signup(msg: EmailMessage, default_tz: tzinfo = timezone.utc) -> Signup | None:
    """Extract a :class:`Signup` from one notification, or ``None`` if it isn't one."""
    if not is_signup_notification(msg):
        return None

    fields: dict[str, str] = {}
    for parser in (_parse_json_block, _parse_kv_lines, _parse_html_table_text):
        for k, v in parser(msg.body or msg.snippet).items():
            fields.setdefault(k, v)

    # Subject fallbacks: "New signup: Priya Raman (priya@...)"
    if "name" not in fields:
        m = SUBJECT_NAME_RE.search(msg.subject)
        if m and not EMAIL_RE.fullmatch(m.group(1).strip()):
            fields["name"] = m.group(1).strip()
    if "email" not in fields:
        candidates = [e for e in EMAIL_RE.findall(msg.subject + "\n" + msg.body) if "auravest" not in e.lower()]
        if candidates:
            fields["email"] = candidates[0]

    if not fields.get("name") and not fields.get("email"):
        return None

    extra = {k: v for k, v in fields.items() if k not in {"name", "email", "company", "plan", "signed_up_at"}}
    return Signup(
        name=fields.get("name", "").strip(),
        email=fields.get("email", "").strip().lower(),
        plan=fields.get("plan", "").strip(),
        company=fields.get("company", "").strip(),
        signed_up_at=_parse_timestamp(fields.get("signed_up_at"), default_tz) or msg.date,
        source_message_id=msg.id,
        extra=extra,
    )


class AuravestSignupService:
    """Fetch and parse recent signup notifications."""

    def __init__(self, mail: MailSource, settings: Settings) -> None:
        self.mail = mail
        self.settings = settings
        try:
            self.tz: tzinfo = ZoneInfo(settings.weather_timezone)
        except Exception:  # noqa: BLE001 - unknown zone on host
            self.tz = timezone.utc

    def query(self, lookback_days: int | None = None) -> str:
        days = lookback_days or self.settings.auravest_lookback_days
        return f"from:{self.settings.auravest_sender} newer_than:{days}d"

    def fetch(self, lookback_days: int | None = None, max_results: int = 100) -> SignupReport:
        days = lookback_days or self.settings.auravest_lookback_days
        now = datetime.now(timezone.utc)
        try:
            messages = self.mail.search(self.query(days), max_results=max_results)
        except JarvisError as exc:
            return SignupReport(signups=[], lookback_days=days, scanned=0, generated_at=now, error=str(exc))
        signups: list[Signup] = []
        seen: set[str] = set()
        for msg in messages:
            s = parse_signup(msg, self.tz)
            if s is None:
                continue
            key = s.email or s.name.lower()
            if key in seen:
                continue
            seen.add(key)
            signups.append(s)
        signups.sort(key=lambda s: s.signed_up_at or now, reverse=True)
        return SignupReport(signups=signups, lookback_days=days, scanned=len(messages), generated_at=now)
