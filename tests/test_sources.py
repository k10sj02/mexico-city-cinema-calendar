from datetime import date

from mexico_city_cinema_calendar.sources.cineya import CineYaSource
from mexico_city_cinema_calendar.sources.haycine import HayCineSource


CINEYA = '''<h1 class="titulo-cine">Cinemex Test</h1><span class="cine-direccion-texto">Calle 1, CDMX</span>
<a class="enlace-comprar-entrada" href="https://tickets.test"></a>
<article class="tarjeta-horarios-pelicula"><a class="cine-nombre" href="/mx/pelicula/test/">Película</a>
<div class="cine-metadatos-linea">Drama · 1 h 40 min</div><div class="horarios-dia" data-dia="2026-12-04">
<li class="pastilla-horario"><strong data-inicia="2026-12-04T20:30">20:30</strong><span class="badge-idioma">SUB</span><span class="badge-formato">PLATINUM</span></li>
</div></article>'''


def test_cineya_parser():
    source = CineYaSource(None)
    events, covered = source._parse("/mx/cine/test/", CINEYA, {date(2026, 12, 4)})
    assert len(events) == 1
    assert events[0].runtime_minutes == 100
    assert events[0].language == "SUB"
    assert covered == [date(2026, 12, 4)]


def test_haycine_source_identity_is_stable():
    assert HayCineSource.name == "hay-cine-cdmx"
