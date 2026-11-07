from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
import json
from pathlib import Path
import re
import unicodedata

from .models import Screening


def date_window(today: date, days: int) -> list[date]:
    return [today + timedelta(days=i) for i in range(days)]


def merge(events: list[Screening]) -> list[Screening]:
    by_uid = {event.uid: event for event in events}
    groups: dict[tuple, list[Screening]] = {}
    for event in by_uid.values():
        key = (event.start, _plain(event.title), _plain(event.venue))
        groups.setdefault(key, []).append(event)
    output = []
    for matches in groups.values():
        output.append(max(matches, key=lambda event: (event.source == "hay-cine-cdmx", len(event.description))))
    return output


def _plain(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def load_state(path: Path) -> dict[str, Screening]:
    if not path.exists():
        return {}
    return {item["uid"]: Screening.from_dict(item["event"]) for item in json.loads(path.read_text())["events"]}


def reconcile(current, previous, successful_sources, today, coverage_ends):
    output = {event.uid: event for event in current}
    for uid, old in previous.items():
        if uid in output or old.start.date() < today:
            continue
        covered = old.start.date() <= coverage_ends.get(old.source, old.start.date())
        if old.source in successful_sources and covered:
            output[uid] = replace(old, status="CANCELLED", description=old.description + "\nRemoved from source schedule.")
        else:
            output[uid] = old
    return list(output.values())


def save_state(path: Path, events: list[Screening]):
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {"schema": 1, "events": [{"uid": event.uid, "fingerprint": event.fingerprint, "event": event.to_dict()} for event in events]}
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
