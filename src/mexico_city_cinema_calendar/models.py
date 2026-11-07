from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json

TZID = "America/Mexico_City"


@dataclass(frozen=True)
class Screening:
    source: str
    source_id: str
    title: str
    start: datetime
    venue: str
    address: str
    url: str
    description: str = ""
    runtime_minutes: int | None = None
    language: str = ""
    format: str = ""
    status: str = "CONFIRMED"

    @property
    def uid(self) -> str:
        raw = f"{self.source}|{self.source_id}".encode()
        return hashlib.sha256(raw).hexdigest()[:32] + "@mexico-city-cinema-calendar"

    @property
    def fingerprint(self) -> str:
        value = asdict(self)
        value["start"] = self.start.isoformat()
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    def to_dict(self) -> dict:
        value = asdict(self)
        value["start"] = self.start.isoformat()
        return value

    @classmethod
    def from_dict(cls, value: dict) -> "Screening":
        value = dict(value)
        value["start"] = datetime.fromisoformat(value["start"])
        return cls(**value)
