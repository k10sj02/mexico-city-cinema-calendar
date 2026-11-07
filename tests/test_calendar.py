from datetime import datetime
from zoneinfo import ZoneInfo

from icalendar import Calendar

from mexico_city_cinema_calendar.calendar import merge
from mexico_city_cinema_calendar.ics import render
from mexico_city_cinema_calendar.models import Screening, TZID


def sample(source="cineya-cdmx", source_id="1"):
    return Screening(source, source_id, "Película", datetime(2026, 12, 4, 20, 30, tzinfo=ZoneInfo(TZID)),
                     "Cine", "1 Calle, CDMX", "https://example.test", runtime_minutes=100)


def test_valid_ics_timezone_and_duration():
    raw = render([sample()])
    event = Calendar.from_ical(raw).walk("VEVENT")[0]
    assert event.decoded("DTSTART").tzinfo.key == TZID
    assert event.decoded("DTEND").hour == 22
    assert max(len(line.encode()) for line in raw.splitlines()) <= 75


def test_calendar_feed_names_can_be_distinct():
    raw = render([sample()], calendar_name="Mexico City Cinema — Evenings")
    parsed = Calendar.from_ical(raw)
    assert str(parsed["X-WR-CALNAME"]) == "Mexico City Cinema — Evenings"


def test_merge_removes_semantic_cross_source_duplicate():
    other = Screening(**{**sample().__dict__, "source": "hay-cine-cdmx", "source_id": "2"})
    assert len(merge([sample(), other])) == 1
