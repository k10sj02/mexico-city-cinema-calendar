from __future__ import annotations

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from .calendar import date_window, load_state, merge, reconcile, save_state
from .http import Fetcher
from .ics import render
from .models import TZID
from .sources import CineYaSource, HayCineSource


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="public/mexico-city-cinema.ics")
    parser.add_argument("--state", default="data/state.json")
    parser.add_argument("--days", type=int, default=21)
    parser.add_argument("--today", type=date.fromisoformat)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    today = args.today or datetime.now(ZoneInfo(TZID)).date()
    wanted = date_window(today, args.days)
    sources = [CineYaSource(Fetcher()), HayCineSource(Fetcher())]
    collected, errors, successful, coverage = [], {}, set(), {}
    for source in sources:
        try:
            events = source.fetch(wanted)
            collected.extend(events)
            successful.add(source.name)
            if source.coverage_end:
                coverage[source.name] = source.coverage_end
            print(f"{source.name}: {len(events)} screenings", file=sys.stderr)
        except Exception as exc:
            errors[source.name] = str(exc)
            print(f"WARNING {source.name}: {exc}", file=sys.stderr)
    if args.strict and errors:
        return 2
    state_path = Path(args.state)
    events = reconcile(merge(collected), load_state(state_path), successful, today, coverage)
    if not events:
        return 3
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(events), newline="")
    save_state(state_path, events)
    report = {"generated": datetime.now(ZoneInfo(TZID)).isoformat(), "count": len(events),
              "sources_ok": sorted(successful), "errors": errors, "coverage_ends": {k: v.isoformat() for k, v in coverage.items()}}
    output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
