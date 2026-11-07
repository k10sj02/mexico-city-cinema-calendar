from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Screening, TZID


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def fold(line: str) -> list[str]:
    output, prefix, rest = [], "", line
    while len((prefix + rest).encode()) > 75:
        budget, used, cut = 75 - len(prefix.encode()), 0, 0
        for index, char in enumerate(rest):
            size = len(char.encode())
            if used + size > budget:
                break
            used += size
            cut = index + 1
        output.append(prefix + rest[:cut])
        rest, prefix = rest[cut:], " "
    output.append(prefix + rest)
    return output


def render(
    events: list[Screening], generated_at: datetime | None = None,
    calendar_name: str = "Mexico City Cinema — All Showtimes",
) -> str:
    now = generated_at or datetime.now(timezone.utc)
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Mexico City Cinema Calendar//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{calendar_name}",
             f"X-WR-TIMEZONE:{TZID}", "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"]
    for event in sorted(events, key=lambda value: (value.start, value.venue, value.title)):
        details = [event.description]
        if event.language:
            details.append(f"Idioma: {event.language}")
        if event.format:
            details.append(f"Formato: {event.format}")
        details.append(f"Fuente: {event.url}")
        lines.extend(["BEGIN:VEVENT", f"UID:{event.uid}", f"DTSTAMP:{stamp}",
                      f"DTSTART;TZID={TZID}:{event.start.strftime('%Y%m%dT%H%M%S')}"])
        if event.runtime_minutes:
            end = event.start + timedelta(minutes=event.runtime_minutes)
            lines.append(f"DTEND;TZID={TZID}:{end.strftime('%Y%m%dT%H%M%S')}")
        lines.extend([f"SUMMARY:{escape('🎬 ' + event.title + ' | ' + event.venue)}",
                      f"LOCATION:{escape(event.address)}",
                      f"DESCRIPTION:{escape(chr(10).join(filter(None, details)))}",
                      f"URL:{event.url}", f"STATUS:{event.status}", "TRANSP:TRANSPARENT",
                      f"X-MEXICO-CITY-CINEMA-SOURCE:{event.source}", "END:VEVENT"])
    lines.append("END:VCALENDAR")
    return "\r\n".join(part for line in lines for part in fold(line)) + "\r\n"
