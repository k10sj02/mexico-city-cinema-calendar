from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import hashlib
import re
import time
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from ..models import Screening, TZID


class CineYaSource:
    name = "cineya-cdmx"
    base_url = "https://cineya.lat"
    city_url = f"{base_url}/mx/ciudad-de-mexico/"

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.coverage_end: date | None = None

    def fetch(self, days: list[date]) -> list[Screening]:
        soup = BeautifulSoup(self.fetcher.get(self.city_url), "html.parser")
        paths = sorted({a.get("href") for a in soup.select('a[href^="/mx/cine/"]') if a.get("href")})
        if len(paths) < 50:
            raise RuntimeError(f"CineYa returned only {len(paths)} CDMX cinemas")
        with ThreadPoolExecutor(max_workers=2) as pool:
            pages = list(pool.map(self._get, paths))
        wanted = set(days)
        events = []
        dates = []
        for path, html in pages:
            parsed, covered = self._parse(path, html, wanted)
            events.extend(parsed)
            dates.extend(covered)
        if dates:
            self.coverage_end = max(dates)
        return events

    def _get(self, path: str) -> tuple[str, str]:
        html = self.fetcher.get(urljoin(self.base_url, path))
        time.sleep(0.35)
        return path, html

    def _parse(self, path: str, html: str, wanted: set[date]) -> tuple[list[Screening], list[date]]:
        soup = BeautifulSoup(html, "html.parser")
        name = soup.select_one("h1.titulo-cine")
        if not name:
            raise RuntimeError(f"CineYa cinema page changed: {path}")
        venue = name.get_text(" ", strip=True)
        address_node = soup.select_one(".cine-direccion-texto")
        address = address_node.get_text(" ", strip=True) if address_node else "Ciudad de México"
        purchase = soup.select_one("a.enlace-comprar-entrada")
        purchase_url = purchase.get("href", "") if purchase else ""
        page_url = urljoin(self.base_url, path)
        events, covered = [], []
        for article in soup.select("article.tarjeta-horarios-pelicula"):
            title_link = article.select_one("a.cine-nombre")
            if not title_link:
                continue
            title = title_link.get_text(" ", strip=True)
            movie_url = urljoin(self.base_url, title_link.get("href", page_url))
            runtime = _runtime(article.select_one(".cine-metadatos-linea"))
            for day in article.select(".horarios-dia[data-dia]"):
                event_date = date.fromisoformat(day["data-dia"])
                if event_date not in wanted:
                    continue
                covered.append(event_date)
                for item in day.select("li.pastilla-horario"):
                    time_node = item.select_one("strong[data-inicia]")
                    if not time_node:
                        continue
                    start = datetime.fromisoformat(time_node["data-inicia"]).replace(tzinfo=ZoneInfo(TZID))
                    language = _text(item.select_one(".badge-idioma"))
                    format_label = _text(item.select_one(".badge-formato"))
                    identity = f"{path}|{title}|{start.isoformat()}|{language}|{format_label}"
                    source_id = hashlib.sha256(identity.encode()).hexdigest()[:24]
                    details = [value for value in [f"Idioma: {language}" if language else "",
                                                   f"Formato: {format_label}" if format_label else "",
                                                   f"Boletos: {purchase_url}" if purchase_url else ""] if value]
                    events.append(Screening(
                        self.name, source_id, title, start, venue, address, movie_url,
                        description="\n".join(details), runtime_minutes=runtime,
                        language=language, format=format_label,
                    ))
        return events, covered


def _text(node) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _runtime(node) -> int | None:
    match = re.search(r"(?:(\d+)\s*h)?\s*(\d+)\s*min", _text(node))
    return int(match.group(1) or 0) * 60 + int(match.group(2)) if match else None
