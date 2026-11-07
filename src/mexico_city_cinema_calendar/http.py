from __future__ import annotations

import time
import httpx

USER_AGENT = "MexicoCityCinemaCalendar/1.0 (+https://github.com/k10sj02/mexico-city-cinema-calendar)"


class Fetcher:
    def __init__(self, timeout: float = 30.0, attempts: int = 5):
        self.attempts = attempts
        self.client = httpx.Client(timeout=timeout, follow_redirects=True, headers={
            "User-Agent": USER_AGENT, "Accept-Language": "es-MX,es;q=0.9,en;q=0.7"
        })

    def get(self, url: str) -> str:
        last = None
        for attempt in range(self.attempts):
            try:
                response = self.client.get(url)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "")
                    delay = int(retry_after) if retry_after.isdigit() else min(5 * (attempt + 1), 20)
                    if attempt + 1 < self.attempts:
                        time.sleep(delay)
                        continue
                response.raise_for_status()
                return response.text
            except Exception as exc:
                last = exc
                if attempt + 1 < self.attempts:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"Unable to fetch {url}: {last}") from last
