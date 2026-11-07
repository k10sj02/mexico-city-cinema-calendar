from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import hashlib
import json
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from ..models import Screening, TZID


class HayCineSource:
    name = "hay-cine-cdmx"
    base_url = "https://haycine.com/"

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.coverage_end: date | None = None

    def fetch(self, days: list[date]) -> list[Screening]:
        with ThreadPoolExecutor(max_workers=5) as pool:
            payloads = list(pool.map(self._get, days[:21]))
        events, covered = [], []
        for payload in payloads:
            schedule = payload.get("schedule") or {}
            schedule_date = date.fromisoformat(schedule["date"])
            covered.append(schedule_date)
            venues = {venue["id"]: venue for venue in schedule.get("venues", [])}
            for film in schedule.get("films", []):
                for show in film.get("screenings", []):
                    if show.get("date") != schedule["date"]:
                        continue
                    venue = venues.get(show.get("venueId"))
                    if not venue or not show.get("time"):
                        continue
                    start = datetime.fromisoformat(f"{show['date']}T{show['time']}").replace(tzinfo=ZoneInfo(TZID))
                    raw_id = show.get("id") or f"{film['id']}|{show['venueId']}|{show['date']}|{show['time']}|{show.get('room','')}"
                    source_id = hashlib.sha256(str(raw_id).encode()).hexdigest()[:24]
                    url = show.get("bookingUrl") or show.get("sourceUrl") or venue.get("url") or self.base_url
                    events.append(Screening(
                        self.name, source_id, film.get("title", "Untitled screening"), start,
                        venue.get("name", "Mexico City cinema"), venue.get("address", "Ciudad de México"),
                        url, description=f"Zona: {venue.get('area', '')}".strip(),
                        runtime_minutes=film.get("runtimeMinutes"), format=show.get("room", ""),
                    ))
        if covered:
            self.coverage_end = max(covered)
        return events

    def _get(self, day: date) -> dict:
        html = self.fetcher.get(f"{self.base_url}?date={day.isoformat()}")
        soup = BeautifulSoup(html, "html.parser")
        node = soup.select_one("script#cinema-bootstrap")
        if not node:
            raise RuntimeError(f"Hay Cine data missing for {day}")
        return json.loads(node.string or node.get_text())
