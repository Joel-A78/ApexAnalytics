"""Cliente ligero para la API publica de OpenF1 (https://openf1.org).

Endpoints usados:
  - /v1/sessions?year=Y&session_name=Race
  - /v1/meetings?year=Y
  - /v1/drivers?session_key=K
  - /v1/stints?session_key=K
  - /v1/laps?session_key=K

Sin autenticacion, sin rate limits documentados. Cada respuesta se proyecta a
los campos realmente consumidos por la app para no retener payload innecesario
(la API devuelve ~16 campos por vuelta y la app usa 4).
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

BASE = "https://api.openf1.org/v1"
TIMEOUT = 20

# Campos minimos necesarios por endpoint
FIELDS = {
    "sessions": (
        "session_key",
        "session_name",
        "meeting_key",
        "circuit_short_name",
        "country_name",
        "date_start",
    ),
    "meetings": ("meeting_key", "meeting_name"),
    "drivers": ("driver_number", "full_name", "team_name"),
    "stints": (
        "stint_number",
        "driver_number",
        "lap_start",
        "lap_end",
        "compound",
        "tyre_age_at_start",
    ),
    "laps": ("driver_number", "lap_number", "lap_duration", "is_pit_out_lap"),
}


def _project(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    """Conserva solo los campos consumidos por la app."""
    return [{f: row.get(f) for f in fields} for row in rows]


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    qs = ""
    if params:
        qs = "?" + "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    req = urllib.request.Request(f"{BASE}{path}{qs}", headers={"User-Agent": "apex-analytics/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def get_sessions(year: int, session_name: str = "Race") -> list[dict[str, Any]]:
    rows = _get_json("/sessions", {"year": year, "session_name": session_name})
    return _project(rows, FIELDS["sessions"])


def get_meetings(year: int) -> list[dict[str, Any]]:
    rows = _get_json("/meetings", {"year": year})
    return _project(rows, FIELDS["meetings"])


def get_drivers(session_key: int) -> list[dict[str, Any]]:
    rows = _get_json("/drivers", {"session_key": session_key})
    return _project(rows, FIELDS["drivers"])


def get_stints(session_key: int) -> list[dict[str, Any]]:
    rows = _get_json("/stints", {"session_key": session_key})
    return _project(rows, FIELDS["stints"])


def get_laps(session_key: int) -> list[dict[str, Any]]:
    rows = _get_json("/laps", {"session_key": session_key})
    return _project(rows, FIELDS["laps"])
