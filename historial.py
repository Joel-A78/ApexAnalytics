"""Proveedor de datos de historial con estrategia de respaldo.

Intenta primero **OpenF1** (trae compuesto real, edad del neumatico y vueltas
de salida de boxes). Si OpenF1 no responde, cae a **Jolpica/Ergast**, que
entrega tiempos de vuelta y vueltas de parada; a partir de ellos se derivan
los stints.

Ambos proveedores se normalizan a la misma forma:

    sesion  -> {"source", "session_key", "round", "meeting_key",
                "circuit_short_name", "country_name", "date_start"}
    piloto  -> {driver_key: {"full_name", "team_name"}}
    stint   -> {"driver_key", "stint_number", "lap_start", "lap_end",
                "compound", "tyre_age_at_start"}
    vuelta  -> {"driver_key", "lap_number", "lap_duration", "is_pit_out_lap"}

`driver_key` es un texto: el dorsal en OpenF1, el `driverId` en Jolpica.
Cuando el compuesto no esta disponible se marca "UNKNOWN".
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Any

import openf1

JOLPICA = "https://api.jolpi.ca/ergast/f1"
PAGE = 100
TIMEOUT = 30
THROTTLE = 0.5  # s entre paginas para respetar el limite de Jolpica
RETRIES = 5
RETRY_CODES = {429, 500, 502, 503, 504}


def _get_json(url: str) -> Any:
    """GET con reintentos y backoff exponencial para 429 / errores de servidor."""
    delay = 1.0
    for attempt in range(RETRIES):
        req = urllib.request.Request(url, headers={"User-Agent": "apex-analytics/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in RETRY_CODES and attempt < RETRIES - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError(f"No se pudo obtener {url}")


def _parse_lap_time(value: Any) -> float | None:
    if not value:
        return None
    text = str(value)
    try:
        if ":" in text:
            minutes, rest = text.split(":", 1)
            return int(minutes) * 60 + float(rest)
        return float(text)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- Jolpica ----

def _jolpica_races(year: int) -> list[dict[str, Any]]:
    """Calendario de la temporada (una sola pagina, 23-24 carreras)."""
    data = _get_json(f"{JOLPICA}/{year}.json")
    return data.get("MRData", {}).get("RaceTable", {}).get("Races", []) or []


def _jolpica_pages(year: int, round_number: int, resource: str, key: str) -> list[dict[str, Any]]:
    """Recorre un recurso paginado (`laps` o `pitstops`) y aplana sus items."""
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        url = f"{JOLPICA}/{year}/{round_number}/{resource}.json?limit={PAGE}&offset={offset}"
        data = _get_json(url)
        mrd = data.get("MRData", {})
        races = mrd.get("RaceTable", {}).get("Races", []) or []
        if not races:
            break
        rows.extend(races[0].get(key, []) or [])
        total = _to_int(mrd.get("total")) or 0
        offset += PAGE
        if offset >= total:
            break
        time.sleep(THROTTLE)
    return rows


def _jolpica_sessions(year: int) -> list[dict[str, Any]]:
    sessions = []
    for race in _jolpica_races(year):
        round_number = _to_int(race.get("round"))
        if round_number is None:
            continue
        sessions.append(
            {
                "source": "jolpica",
                "session_key": f"jolpica-{year}-{round_number}",
                "round": round_number,
                "meeting_key": round_number,
                "circuit_short_name": race.get("Circuit", {}).get("circuitName", ""),
                "country_name": race.get("Circuit", {}).get("Location", {}).get("country", ""),
                "date_start": race.get("date", ""),
            }
        )
    return sessions


def _jolpica_drivers(year: int, round_number: int) -> dict[str, dict[str, str]]:
    data = _get_json(f"{JOLPICA}/{year}/{round_number}/results.json")
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", []) or []
    drivers: dict[str, dict[str, str]] = {}
    for race in races:
        for result in race.get("Results", []) or []:
            code = result.get("Driver", {}).get("driverId")
            if not code:
                continue
            given = result.get("Driver", {}).get("givenName", "")
            family = result.get("Driver", {}).get("familyName", "")
            drivers[code] = {
                "full_name": f"{given} {family}".strip(),
                "team_name": result.get("Constructor", {}).get("name", ""),
            }
    return drivers


@lru_cache(maxsize=16)
def _jolpica_laps(year: int, round_number: int) -> dict[str, dict[int, float]]:
    """{driverId: {lap_number: segundos}}. Cacheado: se reutiliza entre
    stints y vueltas para no repetir las ~12 paginas."""
    laps: dict[str, dict[int, float]] = {}
    for lap in _jolpica_pages(year, round_number, "laps", "Laps"):
        number = _to_int(lap.get("number"))
        if number is None:
            continue
        for timing in lap.get("Timings", []) or []:
            seconds = _parse_lap_time(timing.get("time"))
            code = timing.get("driverId")
            if seconds is None or not code:
                continue
            laps.setdefault(code, {})[number] = seconds
    return laps


@lru_cache(maxsize=16)
def _jolpica_pits(year: int, round_number: int) -> dict[str, list[int]]:
    """{driverId: [vueltas de parada]}"""
    pits: dict[str, list[int]] = {}
    for stop in _jolpica_pages(year, round_number, "pitstops", "PitStops"):
        code = stop.get("driverId")
        lap = _to_int(stop.get("lap"))
        if code and lap is not None:
            pits.setdefault(code, []).append(lap)
    return pits


def _jolpica_stints(year: int, round_number: int) -> list[dict[str, Any]]:
    """Deriva stints partiendo las vueltas en cada parada."""
    laps = _jolpica_laps(year, round_number)
    pits = _jolpica_pits(year, round_number)
    out: list[dict[str, Any]] = []

    for driver, driver_laps in laps.items():
        if not driver_laps:
            continue
        last_lap = max(driver_laps)
        boundaries = sorted(set(pits.get(driver, [])))
        segments: list[tuple[int, int]] = []
        start = 1
        for pit_lap in boundaries:
            if pit_lap >= start:
                segments.append((start, pit_lap))
                start = pit_lap + 1
        segments.append((start, last_lap))

        for number, (lap_start, lap_end) in enumerate(segments, start=1):
            if not any(lap_start <= l <= lap_end for l in driver_laps):
                continue
            out.append(
                {
                    "driver_key": driver,
                    "stint_number": number,
                    "lap_start": lap_start,
                    "lap_end": lap_end,
                    # Jolpica no publica compuesto ni edad del neumatico
                    "compound": "UNKNOWN",
                    "tyre_age_at_start": None,
                }
            )
    return out


def _jolpica_lap_rows(year: int, round_number: int) -> list[dict[str, Any]]:
    """Normaliza las vueltas y marca las de salida de boxes (lap posterior a parada)."""
    laps = _jolpica_laps(year, round_number)
    pits = _jolpica_pits(year, round_number)
    rows: list[dict[str, Any]] = []
    for driver, driver_laps in laps.items():
        out_laps = {lap + 1 for lap in pits.get(driver, [])}
        for lap_number, duration in driver_laps.items():
            rows.append(
                {
                    "driver_key": driver,
                    "lap_number": lap_number,
                    "lap_duration": duration,
                    "is_pit_out_lap": lap_number in out_laps,
                }
            )
    return rows


# ----------------------------------------------------------------- OpenF1 ----

def _openf1_sessions(year: int) -> list[dict[str, Any]]:
    rows = openf1.get_sessions(year)
    return [
        {
            "source": "openf1",
            "session_key": row["session_key"],
            "round": row.get("meeting_key"),
            "meeting_key": row.get("meeting_key"),
            "circuit_short_name": row.get("circuit_short_name", ""),
            "country_name": row.get("country_name", ""),
            "date_start": row.get("date_start", ""),
        }
        for row in rows
    ]


def _openf1_drivers(session: dict[str, Any]) -> dict[str, dict[str, str]]:
    rows = openf1.get_drivers(session["session_key"])
    return {
        str(row["driver_number"]): {
            "full_name": row.get("full_name", ""),
            "team_name": row.get("team_name", ""),
        }
        for row in rows
    }


def _openf1_stints(session: dict[str, Any]) -> list[dict[str, Any]]:
    rows = openf1.get_stints(session["session_key"])
    return [
        {
            "driver_key": str(row["driver_number"]),
            "stint_number": row.get("stint_number"),
            "lap_start": row.get("lap_start"),
            "lap_end": row.get("lap_end"),
            "compound": (row.get("compound") or "UNKNOWN").upper(),
            "tyre_age_at_start": row.get("tyre_age_at_start"),
        }
        for row in rows
    ]


def _openf1_laps(session: dict[str, Any]) -> list[dict[str, Any]]:
    rows = openf1.get_laps(session["session_key"])
    return [
        {
            "driver_key": str(row["driver_number"]),
            "lap_number": row.get("lap_number"),
            "lap_duration": row.get("lap_duration"),
            "is_pit_out_lap": bool(row.get("is_pit_out_lap")),
        }
        for row in rows
    ]


# ---------------------------------------------------------------- Publico ----

def fetch_sessions(year: int) -> list[dict[str, Any]]:
    """Sesiones del ano. OpenF1 primero; Jolpica si falla."""
    try:
        sessions = _openf1_sessions(year)
        if sessions:
            return sessions
    except Exception:  # noqa: BLE001
        pass
    return _jolpica_sessions(year)


def fetch_meetings(year: int) -> dict[Any, str]:
    """{meeting_key: nombre del GP}. Se omite si OpenF1 no responde."""
    try:
        rows = openf1.get_meetings(year)
        return {r["meeting_key"]: r.get("meeting_name", "") for r in rows}
    except Exception:  # noqa: BLE001
        return {}


def fetch_drivers(session: dict[str, Any]) -> dict[str, dict[str, str]]:
    if session.get("source") == "openf1":
        return _openf1_drivers(session)
    return _jolpica_drivers(int(session["session_key"].split("-")[1]), int(session["round"]))


def fetch_stints(session: dict[str, Any]) -> list[dict[str, Any]]:
    if session.get("source") == "openf1":
        return _openf1_stints(session)
    _, year, round_number = session["session_key"].split("-")
    return _jolpica_stints(int(year), int(round_number))


def fetch_laps(session: dict[str, Any]) -> list[dict[str, Any]]:
    if session.get("source") == "openf1":
        return _openf1_laps(session)
    _, year, round_number = session["session_key"].split("-")
    return _jolpica_lap_rows(int(year), int(round_number))
