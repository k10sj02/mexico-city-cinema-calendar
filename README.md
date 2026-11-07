# Mexico City Cinema Calendar

An automated calendar of individual movie showtimes across Ciudad de México.

**Website:** https://k10sj02.github.io/mexico-city-cinema-calendar/

**Subscription:** https://k10sj02.github.io/mexico-city-cinema-calendar/mexico-city-cinema.ics

## Coverage

- CineYa citywide listings for Cinépolis and Cinemex (currently 100+ CDMX cinemas)
- Hay Cine listings for independent cinemas, Cineteca venues, cineclubs, UTOPÍAS and cultural spaces
- Start time, venue, address, runtime, language/format labels and source or ticket link when published
- `America/Mexico_City` timezone, stable UIDs, deduplication and cancellation handling

Schedules are published on a rolling basis, often only one or two weeks ahead. The feed refreshes every six hours and will populate December dates as venues publish them.

## Local use

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
mexico-city-cinema-calendar --strict
```

The project republishes factual showtime metadata and links back to each source. Confirm the cinema's official listing before attending.
