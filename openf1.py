"""Cliente ligero para la API publica de OpenF1 (https://openf1.org).

Endpoints usados:
  - /v1/sessions?year=Y&session_name=Race
  - /v1/drivers?session_key=K
  - /v1/stints?session_key=K
  - /v1/laps?session_key=K

Sin autenticacion, sin rate limits documentados.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

BASE = "https://api.openf1.org/v1"
TIMEOUT = 20


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    qs = ""
    if params:
        qs = "?" + "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    req = urllib.request.Request(f"{BASE}{path}{qs}", headers={"User-Agent": "apex-analytics/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def get_sessions(year: int, session_name: str = "Race") -> list[dict[str, Any]]:
    return _get_json("/sessions", {"year": year, "session_name": session_name})


def get_meetings(year: int) -> list[dict[str, Any]]:
    return _get_json("/meetings", {"year": year})


def get_drivers(session_key: int) -> list[dict[str, Any]]:
    return _get_json("/drivers", {"session_key": session_key})


def get_stints(session_key: int) -> list[dict[str, Any]]:
    return _get_json("/stints", {"session_key": session_key})


def get_laps(session_key: int) -> list[dict[str, Any]]:
    return _get_json("/laps", {"session_key": session_key})
