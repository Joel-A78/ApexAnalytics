"""Dashboard de visualizacion y prediccion de resultados de Formula 1."""

from __future__ import annotations

import base64
import json
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import simulacion as sim
import historial
import prediccion

st.set_page_config(
    page_title="Apex Analytics · F1",
    layout="wide",
    page_icon="assets/media/apex-icon.png",
)

with open("assets/style.css", "r", encoding="utf-8") as _css_file:
    st.markdown(f"<style>{_css_file.read()}</style>", unsafe_allow_html=True)

try:
    with open("assets/media/apex-icon.ico", "rb") as _ico_file:
        _favicon_b64 = base64.b64encode(_ico_file.read()).decode("ascii")
    st.markdown(
        f'<link rel="icon" type="image/x-icon" '
        f'href="data:image/x-icon;base64,{_favicon_b64}">',
        unsafe_allow_html=True,
    )
except OSError:
    pass

try:
    LOCAL_TZ = ZoneInfo("America/Tijuana")
except ZoneInfoNotFoundError:
    LOCAL_TZ = datetime.now().astimezone().tzinfo

WEEKDAY_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MONTH_ES = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
]
MONTH_ES_LONG = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"
SESSION_LABELS: dict[str, str] = {
    "fp1": "Practica 1",
    "fp2": "Practica 2",
    "fp3": "Practica 3",
    "sprintQualifying": "Sprint Qualy",
    "sprint": "Sprint",
    "qualifying": "Clasificacion",
    "race": "Carrera",
}

COMPOUND_CSS = {
    "S": ("soft", "Soft"),
    "M": ("medium", "Medium"),
    "H": ("hard", "Hard"),
    "I": ("inter", "Inter"),
    "W": ("wet", "Wet"),
}


def fmt_date_short(d: date) -> str:
    return f"{d.day:02d} {MONTH_ES[d.month - 1]}"

def fmt_date_long(d: date) -> str:
    return f"{d.day:02d} de {MONTH_ES_LONG[d.month - 1]} de {d.year}"

def fmt_today_es(d: date) -> str:
    return f"{WEEKDAY_ES[d.weekday()]}, {fmt_date_long(d)}"


NAV_ITEMS: list[tuple[str, str]] = [
    ("overview", "Raceweek"),
    ("season", "Temporada"),
    ("prediction", "Simulacion"),
    ("telemetry", "Historial"),
]


def render_sidebar() -> str:
    import base64
    with open("assets/media/ApexAnalytics logo letras.png", "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode("ascii")
    _logo_src = f"data:image/png;base64,{_logo_b64}"

    with st.sidebar:
        st.markdown(
            f"""
            <div class="apex-brand">
              <img class="apex-logo" src="{_logo_src}" alt="Apex Analytics" />
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="nav-eyebrow"><span>Secciones</span></div>',
            unsafe_allow_html=True,
        )

        if "nav_section" not in st.session_state:
            st.session_state["nav_section"] = "overview"

        for index, (key, label) in enumerate(NAV_ITEMS, start=1):
            is_active = st.session_state["nav_section"] == key
            if st.button(
                f"{index:02d}   {label}",
                key=f"nav_btn_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["nav_section"] = key
                st.rerun()

        section = st.session_state["nav_section"]

        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
        now = datetime.now(LOCAL_TZ)
        st.caption(f"Formula 1 · 2026 · {now.strftime('%H:%M')} America/Tijuana")
        st.caption("Data drives victory.")
    return section


def render_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="command-header">
            <span class="eyebrow">PIT WALL</span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


SECTIONS: dict[str, tuple[str, str]] = {
    "overview": (
        "Raceweek",
        "Grandes Premios y sesiones de la semana en curso en el calendario de Formula 1.",
    ),
    "season": (
        "Temporada",
        "Resultados de cada ronda y evolucion de puntos del campeonato.",
    ),
    "prediction": (
        "Simulacion",
        "Simulador de paradas en boxes segun circuito, clima y degradacion de neumaticos.",
    ),
    "telemetry": (
        "Historial",
        "Comparativa de stints y prediccion de resultados (train 2024 / eval 2025).",
    ),
}


def render_credits_footer() -> None:
    import base64 as _b64
    from pathlib import Path

    def _logo_data_uri(filename: str) -> str | None:
        path = Path("assets/media") / filename
        if not path.exists():
            return None
        encoded = _b64.b64encode(path.read_bytes()).decode("ascii")
        mime_type = {
            ".png": "image/png",
            ".webp": "image/webp",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }.get(path.suffix.lower(), "application/octet-stream")
        return f"data:{mime_type};base64,{encoded}"

    fia_logo = _logo_data_uri("FiA logo.webp")
    formula1_logo = _logo_data_uri("F1 logo.png")
    fia_mark = (
        f'<img class="institution-logo fia-logo" src="{fia_logo}" alt="FIA" />'
        if fia_logo
        else '<span class="institution-mark fia-mark">FIA</span>'
    )
    formula1_mark = (
        f'<img class="institution-logo formula1-logo" src="{formula1_logo}" alt="Formula 1" />'
        if formula1_logo
        else '<span class="institution-mark f1-mark">F1</span>'
    )

    st.markdown(
                f"""
                <footer class="credits-footer">
                    <div class="credits-heading">
                        <span class="eyebrow">CREDITOS Y FUENTES</span>
                        <span class="credits-project">Apex Analytics · F1</span>
                    </div>
                    <div class="credits-grid">
                        <div class="credits-item">
                            <span class="credits-label">Calendario y carreras</span>
                            <a href="https://jolpi.ca/ergast/f1/" target="_blank" rel="noopener noreferrer">Jolpica / Ergast API</a>
                        </div>
                        <div class="credits-item">
                            <span class="credits-label">Telemetria y stints</span>
                            <span class="institution-links">
                                <a href="https://openf1.org/" target="_blank" rel="noopener noreferrer">OpenF1 API</a>
                                <span class="credits-alt">respaldo: Jolpica (tiempos de vuelta y paradas)</span>
                            </span>
                        </div>
                        <div class="credits-item">
                            <span class="credits-label">Clima</span>
                            <a href="https://open-meteo.com/" target="_blank" rel="noopener noreferrer">Open-Meteo API</a>
                        </div>
                        <div class="credits-item">
                            <span class="credits-label">Referencias institucionales</span>
                            <span class="institution-links">
                                <a href="https://www.fia.com/" target="_blank" rel="noopener noreferrer">{fia_mark}</a>
                                <a href="https://www.formula1.com/" target="_blank" rel="noopener noreferrer">{formula1_mark}</a>
                            </span>
                        </div>
                        <div class="credits-item">
                            <span class="credits-label">Multimedia y marca</span>
                            <span>Recursos locales del proyecto · autor no documentado</span>
                        </div>
                    </div>
                    <div class="credits-note">Los datos y marcas pertenecen a sus respectivos propietarios. Esta aplicación es un proyecto independiente.</div>
                </footer>
                """,
            unsafe_allow_html=True,
            )

    _render_interest_bar()


def _render_interest_bar() -> None:
    """KPI de interes de usuarios, visible al final del scroll."""
    interest = get_interest_stats()
    visits = interest["visits"]
    chips = "".join(
        f'<span class="interest-chip"><span class="interest-chip-name">{_section_label(k)}</span>'
        f'<span class="interest-chip-count">{v}</span></span>'
        for k, v in sorted(visits.items(), key=lambda kv: -kv[1])
    ) or '<span class="interest-empty">Sin actividad registrada</span>'

    st.markdown(
        f"""
        <div class="interest-bar">
          <div class="interest-heading">
            <span class="eyebrow">INTERES DE USUARIOS</span>
            <span class="interest-note">Metrica de la sesion actual</span>
          </div>
          <div class="interest-stats">
            <div class="interest-stat"><span class="interest-value">{interest['total_views']}</span><span class="interest-label">Vistas totales</span></div>
            <div class="interest-stat"><span class="interest-value">{interest['sections_visited']}/4</span><span class="interest-label">Secciones</span></div>
            <div class="interest-stat"><span class="interest-value">{interest['session_minutes']:.1f}</span><span class="interest-label">Minutos</span></div>
            <div class="interest-stat"><span class="interest-value">{interest['views_per_min']:.2f}</span><span class="interest-label">Vistas / min</span></div>
          </div>
          <div class="interest-chips">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_label(key: str) -> str:
    return {
        "overview": "Raceweek",
        "season": "Temporada",
        "prediction": "Simulacion",
        "telemetry": "Historial",
        "model": "Modelo",
    }.get(key, key)


def current_week_range(today: date | None = None) -> tuple[date, date]:
    today = today or datetime.now(LOCAL_TZ).date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    s = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_season_schedule(season: int) -> list[dict[str, Any]]:
    """Calendario de una temporada. El ano va como argumento para que la
    clave de cache cambie al cambiar de temporada."""
    url = f"{JOLPICA_BASE}/{season}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "race-analytics/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    races = (
        payload.get("MRData", {}).get("RaceTable", {}).get("Races", []) or []
    )
    return races


def get_season_schedule(season: int | None = None) -> list[dict[str, Any]]:
    """Calendario de la temporada activa (por defecto, el ano local actual)."""
    return fetch_season_schedule(season or datetime.now(LOCAL_TZ).year)


def get_next_race(season: int | None = None) -> dict[str, Any] | None:
    """Proxima carrera segun la fecha local.

    Si hay una carrera en curso (su fin de semana incluye hoy), se devuelve
    esa; en caso contrario, la primera con fecha >= hoy. Si todas pasaron,
    devuelve la ultima de la temporada.
    """
    today = datetime.now(LOCAL_TZ).date()
    try:
        races = get_season_schedule(season)
    except Exception:  # noqa: BLE001
        return None
    if not races:
        return None

    # 1) Carrera con fin de semana en curso
    for r in races:
        start, end = weekend_bounds(r)
        if start <= today <= end:
            return r

    # 2) Primera carrera futura
    for r in races:
        d = parse_iso_date(r.get("date"))
        if d and d >= today:
            return r

    # 3) Temporada terminada
    return races[-1]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_race_results(season: int, round_number: str) -> list[dict[str, Any]]:
    url = f"{JOLPICA_BASE}/{season}/{round_number}/results.json"
    req = urllib.request.Request(url, headers={"User-Agent": "race-analytics/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    races = payload.get("MRData", {}).get("RaceTable", {}).get("Races", []) or []
    if not races:
        return []
    return races[0].get("Results", []) or []


def session_label(key: str) -> str:
    return SESSION_LABELS.get(key, key)


def collect_sessions(race: dict[str, Any]) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []

    def _dt(block: dict[str, Any]) -> datetime | None:
        d = block.get("date")
        t = block.get("time")
        if not d:
            return None
        if t:
            return parse_iso_datetime(f"{d}T{t}")
        return parse_iso_datetime(f"{d}T00:00:00+00:00")

    for key, block_key in (
        ("fp1", "FirstPractice"),
        ("fp2", "SecondPractice"),
        ("fp3", "ThirdPractice"),
        ("sprintQualifying", "SprintQualifying"),
        ("sprint", "Sprint"),
        ("qualifying", "Qualifying"),
        ("race", None),
    ):
        if block_key is None:
            dt = _dt(race)
        else:
            dt = _dt(race.get(block_key, {}) or {})
        if dt:
            sessions.append({"key": key, "label": session_label(key), "dt": dt})
    return sessions


def weekend_bounds(race: dict[str, Any]) -> tuple[date, date]:
    dates: list[date] = []
    for sess in collect_sessions(race):
        local_dt = sess["dt"].astimezone(LOCAL_TZ)
        dates.append(local_dt.date())
    fallback = parse_iso_date(race.get("date"))
    if fallback:
        dates.append(fallback)
    if not dates:
        return date.min, date.max
    return min(dates), max(dates)


def events_in_week(races: list[dict[str, Any]], week_start: date, week_end: date) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for race in races:
        start, end = weekend_bounds(race)
        if start > week_end or end < week_start:
            continue
        matches.append(
            {
                "round": race.get("round"),
                "race_name": race.get("raceName"),
                "circuit": race.get("Circuit", {}).get("circuitName"),
                "locality": race.get("Circuit", {}).get("Location", {}).get("locality"),
                "country": race.get("Circuit", {}).get("Location", {}).get("country"),
                "url": race.get("url"),
                "sessions": collect_sessions(race),
                "weekend_start": start,
                "weekend_end": end,
            }
        )
    matches.sort(key=lambda r: r["weekend_start"])
    return matches


def render_session_chip(session: dict[str, Any]) -> str:
    dt = session["dt"].astimezone(LOCAL_TZ)
    weekday = dt.strftime("%a")
    day_num = dt.day
    time_str = dt.strftime("%H:%M")
    return (
        f"<span class='session-chip'>"
        f"<span class='day'>{weekday} {day_num:02d}</span>"
        f"<span class='label'>{session['label']}</span>"
        f"<span>{time_str}</span>"
        f"</span>"
    )


def render_event_card(event: dict[str, Any]) -> None:
    start = event["weekend_start"]
    end = event["weekend_end"]
    span = (
        f"{fmt_date_short(start)} – {fmt_date_short(end)} {end.year}"
        if start != end
        else fmt_date_short(start)
    )
    sessions_html = "".join(render_session_chip(s) for s in event["sessions"])
    place = ", ".join(filter(None, [event["locality"], event["country"]]))
    circuit = event["circuit"] or ""
    race_name = event["race_name"] or "Gran Premio"
    round_label = f"Ronda {event['round']}" if event["round"] else ""

    st.markdown(
        f"""
        <div class="race-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;flex-wrap:wrap;">
            <div style="flex:1;min-width:240px;">
              <span class="round-tag">{round_label or 'GP'}</span>
              <div class="race-name">{race_name}</div>
              <div class="circuit-name">{circuit} · {place}</div>
            </div>
            <div class="race-dates">{span}</div>
          </div>
          <div style="margin-top:0.7rem;">{sessions_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_compound_chip(short: str) -> str:
    css_class, label = COMPOUND_CSS.get(short, ("soft", short))
    return (
        f"<span class='compound-chip {css_class}'>"
        f"<span class='stripe'></span>{short} · {label}"
        f"</span>"
    )


def _render_calendar_card(row: dict[str, Any]) -> str:
    status = row.get("status", "upcoming")
    flag_html = ""
    if status == "next":
        flag_html = '<span class="cal-flag cal-flag-next">PROXIMO</span>'
    elif status == "past":
        flag_html = '<span class="cal-flag cal-flag-past">FINALIZADO</span>'
    flag_wrap = f'<div class="cal-flag-wrap">{flag_html}</div>' if flag_html else ""

    season = row.get("season", "")
    round_number = row.get("round", "")
    href = f"?section=season&season={season}&round={round_number}"
    hint = "Ver resultados" if status == "past" else "Ver detalle"

    return (
        f'<a class="cal-card cal-card-{status}" href="{href}" target="_self" '
        f'title="{row["name"]} · {hint}">'
        f'<div class="cal-header">'
        f'<span class="cal-round">R{round_number}</span>'
        f'{flag_wrap}'
        f'</div>'
        f'<div class="cal-name">{row["name"]}</div>'
        f'<div class="cal-circuit">{row["circuit"]}</div>'
        f'<div class="cal-meta">'
        f'<span class="cal-country">{row["country"]}</span>'
        f'<span class="cal-dates">{row["dates"]}</span>'
        f'</div>'
        f'<span class="cal-cta">{hint}</span>'
        f'</a>'
    )


def _get_circuit_coords(race: dict[str, Any]) -> tuple[float | None, float | None]:
    loc = race.get("Circuit", {}).get("Location", {}) or {}
    try:
        lat = float(loc.get("lat")) if loc.get("lat") is not None else None
        lon = float(loc.get("long")) if loc.get("long") is not None else None
    except (TypeError, ValueError):
        return None, None
    return lat, lon


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather(lat: float, lon: float) -> dict[str, Any] | None:
    current_fields = ",".join(
        [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "is_day",
        ]
    )
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current={current_fields}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
        f"&timezone=auto&forecast_days=3"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "apex-analytics/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


WMO_CODE: dict[int, str] = {
    0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado",
    3: "Nublado", 45: "Niebla", 48: "Niebla con escarcha",
    51: "Llovizna ligera", 53: "Llovizna", 55: "Llovizna densa",
    61: "Lluvia ligera", 63: "Lluvia", 65: "Lluvia fuerte",
    71: "Nieve ligera", 73: "Nieve", 75: "Nieve fuerte",
    80: "Chubascos ligeros", 81: "Chubascos", 82: "Chubascos violentos",
    95: "Tormenta", 96: "Tormenta con granizo", 99: "Tormenta fuerte con granizo",
}

WMO_ICON: dict[int, str] = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️",
    71: "🌨️", 73: "🌨️", 75: "❄️",
    80: "🌦️", 81: "🌧️", 82: "⛈️",
    95: "⛈️", 96: "⛈️", 99: "⛈️",
}


def render_circuit_map(race: dict[str, Any], fullscreen: bool = False) -> None:
    from circuits import generate_circuit_svg
    circuit_api_name = race.get("Circuit", {}).get("circuitName", "Circuito")
    circuit_key = match_circuit_key(race) or circuit_api_name

    lat, lon = _get_circuit_coords(race)
    locality = race.get("Circuit", {}).get("Location", {}).get("locality", "")
    country = race.get("Circuit", {}).get("Location", {}).get("country", "")
    coords_text = f"{lat:.4f}, {lon:.4f}" if lat is not None and lon is not None else "—"

    st.markdown(
        f"""
        <div class="circuit-coords">
          <span class="eyebrow">Circuito</span>
          <span class="circuit-name">{circuit_api_name}</span>
          <span class="circuit-place">{locality}, {country} · {coords_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    f1, f2, f3 = st.columns([1.3, 1, 1])
    with f1:
        sector_filter = st.selectbox(
            "Filtrar sectores",
            options=[
                "Todos",
                "Solo S1",
                "Solo S2",
                "Solo S3",
                "S1 + S2",
                "S1 + S3",
                "S2 + S3",
            ],
            index=0,
            key=f"sector_{circuit_key}",
        )
    with f2:
        show_corners = st.toggle(
            "Mostrar curvas",
            value=True,
            key=f"corners_{circuit_key}",
        )
    with f3:
        if fullscreen:
            if st.button("Salir", key="map_exit_fs", use_container_width=True):
                st.session_state["map_fullscreen"] = False
                st.rerun()
        else:
            if st.button("Pantalla completa", key="map_enter_fs", use_container_width=True):
                st.session_state["map_fullscreen"] = True
                st.rerun()

    selected = _parse_sector_filter(sector_filter)
    dimmed = ({c for c in ("S1", "S2", "S3") if c not in selected}) if selected else set()

    subtitle = f"{locality}, {country}" if locality else ""
    svg = generate_circuit_svg(
        circuit_api_name,
        subtitle,
        show_corners=show_corners,
        dim_sectors=dimmed,
        seed=circuit_key,
    )

    card_class = "circuit-card fullscreen" if fullscreen else "circuit-card"
    st.markdown(f'<div class="{card_class}">{svg}</div>', unsafe_allow_html=True)

    if selected:
        st.caption(f"Mostrando {', '.join(sorted(selected))} · los demas sectores quedan atenuados.")
    else:
        st.caption("Mostrando los 3 sectores del circuito.")


def _parse_sector_filter(value: str) -> set[str]:
    if value == "Todos":
        return set()
    return {part.strip() for part in value.replace("Solo ", "").split("+")}


def render_weather_card(race: dict[str, Any]) -> None:
    lat, lon = _get_circuit_coords(race)
    locality = race.get("Circuit", {}).get("Location", {}).get("locality", "")
    country = race.get("Circuit", {}).get("Location", {}).get("country", "")
    if lat is None or lon is None:
        st.info(f"Sin coordenadas para consultar clima de {locality}.")
        return
    try:
        data = fetch_weather(lat, lon)
    except Exception as exc:  # noqa: BLE001
        st.warning(f"No se pudo cargar el clima: {exc}")
        return
    if not data:
        st.warning("Open-Meteo no devolvio datos.")
        return

    cw = data.get("current", {}) or {}
    daily = data.get("daily", {}) or {}
    code = int(cw.get("weather_code", 0) or 0)
    desc = WMO_CODE.get(code, f"Codigo {code}")
    icon = WMO_ICON.get(code, "❓")
    temp = cw.get("temperature_2m", "—")
    wind = cw.get("wind_speed_10m", "—")
    wind_dir = cw.get("wind_direction_10m", "—")
    feels = cw.get("apparent_temperature", "—")
    humidity = cw.get("relative_humidity_2m", "—")
    gusts = cw.get("wind_gusts_10m", "—")
    pressure = cw.get("pressure_msl", "—")
    clouds = cw.get("cloud_cover", "—")
    precip = cw.get("precipitation", "—")

    stat_cells = "".join(
        f"<div class='wx-stat'><span class='wx-stat-label'>{label}</span>"
        f"<span class='wx-stat-value'>{value}</span></div>"
        for label, value in [
            ("Sensacion", f"{feels}°C" if isinstance(feels, (int, float)) else feels),
            ("Humedad", f"{humidity}%" if isinstance(humidity, (int, float)) else humidity),
            ("Rachas", f"{gusts} km/h" if isinstance(gusts, (int, float)) else gusts),
            ("Presion", f"{pressure} hPa" if isinstance(pressure, (int, float)) else pressure),
            ("Nubosidad", f"{clouds}%" if isinstance(clouds, (int, float)) else clouds),
            ("Precip.", f"{precip} mm" if isinstance(precip, (int, float)) else precip),
        ]
    )

    tmax_list = daily.get("temperature_2m_max", [])
    tmin_list = daily.get("temperature_2m_min", [])
    pop_list = daily.get("precipitation_probability_max", [])

    day_labels = ["Hoy", "Manana", "Pasado"]
    daily_codes = daily.get("weather_code", [])
    forecast_cells = []
    for i in range(min(3, len(tmax_list))):
        dcode = int(daily_codes[i]) if i < len(daily_codes) and daily_codes[i] is not None else code
        d_icon = WMO_ICON.get(dcode, "❓")
        pop = pop_list[i] if i < len(pop_list) else 0
        forecast_cells.append(
            f"<div class='wx-day'>"
            f"<div class='wx-day-label'>{day_labels[i]}</div>"
            f"<div class='wx-day-icon'>{d_icon}</div>"
            f"<div class='wx-day-temps'>{tmax_list[i]:.0f}°<span>/{tmin_list[i]:.0f}°</span></div>"
            f"<div class='wx-day-pop'>{pop}% lluvia</div>"
            f"</div>"
        )
    forecast_rows = "".join(forecast_cells)

    rain_risk = max(pop_list[:3]) if pop_list else 0
    if rain_risk >= 60:
        race_note = "Lluvia probable · considera neumaticos de lluvia"
        race_class = "wx-outlook-wet"
    elif rain_risk >= 30:
        race_note = "Lluvia posible · vigila la evolucion de la pista"
        race_class = "wx-outlook-mixed"
    else:
        race_note = "Condiciones secas esperadas · estrategia normal"
        race_class = "wx-outlook-dry"

    is_day = bool(cw.get("is_day", 1))
    track_temp = (
        (float(feels) + 9) if is_day and isinstance(feels, (int, float))
        else (float(feels) if isinstance(feels, (int, float)) else None)
    )
    track_temp_text = f"{track_temp:.0f}°C" if track_temp is not None else "—"

    st.markdown(
        f"""
        <div class="weather-card">
            <div class="wx-head">
                <span class="wx-head-eyebrow">Clima</span>
                <span class="wx-head-place">{locality}, {country}</span>
            </div>
            <div class="wx-main">
                <div class="wx-now">
                    <span class="wx-icon">{icon}</span>
                    <div class="wx-now-text">
                        <span class="wx-temp">{temp}<small>°C</small></span>
                        <span class="wx-desc">{desc}</span>
                    </div>
                </div>
                <div class="wx-wind">
                    <span class="wx-wind-icon">💨</span>
                    <div>
                        <div class="wx-wind-val">{wind} <small>km/h</small></div>
                        <div class="wx-wind-dir">dir {wind_dir}°</div>
                    </div>
                </div>
            </div>
            <div class="wx-stats">{stat_cells}</div>
            <div class="wx-outlook {race_class}">
                <span class="wx-outlook-icon">🏁</span>
                <div>
                    <div class="wx-outlook-title">Condiciones de carrera</div>
                    <div class="wx-outlook-note">{race_note}</div>
                </div>
                <div class="wx-outlook-track">
                    <span class="wx-outlook-track-label">Pista</span>
                    <span class="wx-outlook-track-value">~{track_temp_text}</span>
                </div>
            </div>
            <div class="wx-forecast-label">Proximos 3 dias</div>
            <div class="wx-forecast">{forecast_rows}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview() -> None:
    render_header(*SECTIONS["overview"])

    today = datetime.now(LOCAL_TZ).date()
    week_start, week_end = current_week_range(today)

    top_cols = st.columns([1.2, 1.5, 1])
    top_cols[0].markdown(
        f"<div class='eyebrow'>Semana en curso</div>"
        f"<div style='color:#FFFFFF;font-size:1.1rem;font-weight:700;margin-top:0.2rem;'>"
        f"{fmt_date_short(week_start)} – {fmt_date_short(week_end)} {week_end.year}</div>",
        unsafe_allow_html=True,
    )
    top_cols[1].markdown(
        f"<div class='eyebrow'>Hoy (America/Tijuana)</div>"
        f"<div style='color:#FFFFFF;font-size:1.1rem;font-weight:700;margin-top:0.2rem;'>"
        f"{fmt_today_es(today).capitalize()}</div>",
        unsafe_allow_html=True,
    )
    if top_cols[2].button("Actualizar", use_container_width=True, key="refresh_button"):
        fetch_season_schedule.clear()
        st.rerun()

    try:
        races = get_season_schedule()
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo cargar el calendario de Formula 1: {exc}")
        return

    events = events_in_week(races, week_start, week_end)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Eventos esta semana", len(events))
    k2.metric("Carreras en la temporada", len(races))
    next_race = get_next_race()

    if next_race and parse_iso_date(next_race.get("date")):
        race_date_obj = parse_iso_date(next_race["date"])
        days_until = (race_date_obj - today).days
        short_name = next_race["raceName"].replace(" Grand Prix", " GP").replace("Grand Prix", "GP")
        short_name = short_name[:18] if len(short_name) > 18 else short_name
        k3.metric(
            "Proxima carrera",
            short_name,
            fmt_date_short(race_date_obj),
        )
        k4.metric(
            "Cuenta regresiva",
            f"{days_until} dias" if days_until > 0 else "Hoy",
            next_race.get("Circuit", {}).get("Location", {}).get("country", "—"),
        )
    else:
        k3.metric("Proxima carrera", "—", None)
        k4.metric("Cuenta regresiva", "—", None)

    st.markdown("### Eventos de la semana")
    if not events:
        st.info("No hay Grandes Premios esta semana. Revisa el calendario completo de la temporada abajo.")
    else:
        for event in events:
            render_event_card(event)

    if next_race:
        next_label = next_race.get("raceName", "Proxima carrera")
        map_fullscreen = bool(st.session_state.get("map_fullscreen"))
        st.markdown(f"### Datos geométricos · {next_label}")

        if map_fullscreen:
            render_circuit_map(next_race, fullscreen=True)
        else:
            wx_col, map_col = st.columns([1, 2.05], gap="medium")
            with wx_col:
                render_weather_card(next_race)
            with map_col:
                render_circuit_map(next_race)

    if next_race:
        next_round = next_race.get("round")
    else:
        next_round = None

    st.markdown("### Calendario de la temporada")
    st.caption("Selecciona una carrera para ver sus resultados en la seccion Temporada.")
    cal_rows = []
    for r in races:
        start, end = weekend_bounds(r)
        rnd = str(r.get("round", ""))
        is_next = bool(next_round) and str(next_round) == rnd
        is_past = end < today
        status = "next" if is_next else ("past" if is_past else "upcoming")
        date_range = (
            f"{fmt_date_short(start)} – {fmt_date_short(end)}"
            if start != end
            else fmt_date_short(start)
        )
        cal_rows.append(
            {
                "season": r.get("season", datetime.now(LOCAL_TZ).year),
                "round": rnd,
                "name": r.get("raceName", "—"),
                "circuit": r.get("Circuit", {}).get("circuitName", ""),
                "country": r.get("Circuit", {}).get("Location", {}).get("country", ""),
                "dates": date_range,
                "status": status,
            }
        )

    cards_html = "".join(_render_calendar_card(row) for row in cal_rows)
    st.markdown(f'<div class="season-calendar">{cards_html}</div>', unsafe_allow_html=True)


CIRCUIT_ALIASES: dict[str, str] = {
    "sakhir": "Bahrain",
    "jeddah": "Jeddah",
    "melbourne": "Melbourne",
    "albert park": "Melbourne",
    "suzuka": "Suzuka",
    "shanghai": "Shanghai",
    "miami": "Miami",
    "imola": "Imola",
    "monaco": "Monaco",
    "monte carlo": "Monaco",
    "montreal": "Montreal",
    "barcelona": "Catalunya",
    "catalunya": "Catalunya",
    "spielberg": "Red Bull Ring",
    "red bull ring": "Red Bull Ring",
    "silverstone": "Silverstone",
    "budapest": "Hungaroring",
    "hungaroring": "Hungaroring",
    "spa": "Spa-Francorchamps",
    "spa-francorchamps": "Spa-Francorchamps",
    "francorchamps": "Spa-Francorchamps",
    "zandvoort": "Zandvoort",
    "monza": "Monza",
    "baku": "Baku",
    "marina bay": "Marina Bay",
    "singapore": "Marina Bay",
    "austin": "COTA",
    "cota": "COTA",
    "mexico city": "Mexico City",
    "mexico": "Mexico City",
    "sepang": "Sepang",
    "kuala lumpur": "Sepang",
    "madrid": "Madrid",
    "madring": "Madrid",
    "ifema": "Madrid",
    "interlagos": "Interlagos",
    "sao paulo": "Interlagos",
    "las vegas": "Las Vegas",
    "abu dhabi": "Abu Dhabi",
    "yas island": "Abu Dhabi",
}


def match_circuit_key(race: dict[str, Any]) -> str | None:
    if not race:
        return None
    locality = (race.get("Circuit", {}).get("Location", {}).get("locality") or "").strip().lower()
    circuit_name = (race.get("Circuit", {}).get("circuitName") or "").strip().lower()
    for needle in (locality, circuit_name):
        for alias, key in CIRCUIT_ALIASES.items():
            if alias and alias in needle:
                return key
    return None


COMPOUND_COLORS_OPENF1 = {
    "SOFT": "#E10600",
    "MEDIUM": "#FFD500",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#00B050",
    "WET": "#1E90FF",
    "UNKNOWN": "#6E6E76",
}

# Colores de equipo F1 (2024-2025). Se usan como dimension de color cuando el
# compuesto no esta disponible (fuente Jolpica).
TEAM_COLORS = {
    "red bull": "#3671C6",
    "ferrari": "#E8002D",
    "mercedes": "#27F4D2",
    "mclaren": "#FF8000",
    "aston martin": "#229971",
    "alpine": "#FF87BC",
    "williams": "#64C4FF",
    "racing bulls": "#6692FF",
    "rb": "#6692FF",
    "alphatauri": "#6692FF",
    "sauber": "#52E252",
    "kick sauber": "#52E252",
    "stake": "#52E252",
    "haas": "#B6BABD",
}

# Respaldo cuando el equipo tampoco es identificable (paleta distinguible en oscuro)
DRIVER_FALLBACK_COLORS = [
    "#3671C6", "#E8002D", "#27F4D2", "#FF8000", "#229971",
    "#FF87BC", "#64C4FF", "#52E252", "#B6BABD", "#9775FA",
    "#F06595", "#4C6EF5",
]

# Paleta secuencial por numero de stint (S1, S2, S3, ...). Distinta de la de
# compuestos para no confundir su semantica.
STINT_COLORS = [
    "#4C6EF5",  # S1 indigo
    "#9775FA",  # S2 violeta
    "#F06595",  # S3 rosa
    "#20C997",  # S4 teal
    "#FFA94D",  # S5 naranja
    "#63E6BE",  # S6
]


def _team_color(team_name: str, index: int) -> str:
    """Color de equipo si se reconoce; si no, se toma de la paleta de respaldo."""
    name = (team_name or "").strip().lower()
    for key, color in TEAM_COLORS.items():
        if key in name:
            return color
    return DRIVER_FALLBACK_COLORS[index % len(DRIVER_FALLBACK_COLORS)]


def _stint_color(stint_number: Any) -> str:
    try:
        idx = max(int(stint_number) - 1, 0)
    except (TypeError, ValueError):
        idx = 0
    return STINT_COLORS[idx % len(STINT_COLORS)]


def _compounds_known(stints_df: pd.DataFrame) -> bool:
    """True si al menos un stint trae compuesto real (no UNKNOWN)."""
    return bool((stints_df["compound"] != "UNKNOWN").any())


@st.cache_data(ttl=86400, show_spinner="Cargando calendario de sesiones...")
def _cached_sessions(year: int) -> list[dict[str, Any]]:
    return historial.fetch_sessions(year)


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_meetings(year: int) -> dict[Any, str]:
    return historial.fetch_meetings(year)


@st.cache_data(ttl=86400, show_spinner="Cargando pilotos...")
def _cached_drivers(session_key: str, source: str, round_number: int) -> dict[str, dict[str, str]]:
    session = {"session_key": session_key, "source": source, "round": round_number}
    return historial.fetch_drivers(session)


@st.cache_data(ttl=86400, show_spinner="Cargando stints...")
def _cached_stints(session_key: str, source: str, round_number: int) -> list[dict[str, Any]]:
    session = {"session_key": session_key, "source": source, "round": round_number}
    return historial.fetch_stints(session)


@st.cache_data(ttl=86400, show_spinner="Cargando vueltas...")
def _cached_laps(session_key: str, source: str, round_number: int) -> list[dict[str, Any]]:
    session = {"session_key": session_key, "source": source, "round": round_number}
    return historial.fetch_laps(session)


def session_drivers(session: dict[str, Any]) -> dict[str, dict[str, str]]:
    return _cached_drivers(session["session_key"], session["source"], int(session.get("round") or 0))


def session_stints(session: dict[str, Any]) -> list[dict[str, Any]]:
    return _cached_stints(session["session_key"], session["source"], int(session.get("round") or 0))


def session_laps(session: dict[str, Any]) -> list[dict[str, Any]]:
    return _cached_laps(session["session_key"], session["source"], int(session.get("round") or 0))


def _driver_label(d: dict[str, Any]) -> str:
    return f"{d.get('full_name', '?')} ({d.get('team_name', '?')})"


def _stint_metrics(stints: list[dict[str, Any]], laps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    laps_by_driver: dict[str, list[dict[str, Any]]] = {}
    for lap in laps:
        if lap.get("lap_duration") is None:
            continue
        laps_by_driver.setdefault(lap["driver_key"], []).append(lap)

    rows: list[dict[str, Any]] = []
    for s in stints:
        driver_key = s.get("driver_key")
        lap_start = s.get("lap_start")
        lap_end = s.get("lap_end")
        if driver_key is None or lap_start is None or lap_end is None:
            continue

        drv_laps = laps_by_driver.get(driver_key, [])
        relevant = [
            lap for lap in drv_laps
            if lap.get("lap_number") is not None
            and lap_start <= lap["lap_number"] <= lap_end
            and not lap.get("is_pit_out_lap")
            and lap.get("lap_duration") is not None
        ]
        if not relevant:
            continue
        times = [lap["lap_duration"] for lap in relevant]
        compound = (s.get("compound") or "UNKNOWN").upper()
        rows.append(
            {
                "driver_key": driver_key,
                "stint_number": s.get("stint_number"),
                "compound": compound,
                "lap_start": lap_start,
                "lap_end": lap_end,
                "laps_completed": len(relevant),
                "avg_lap_s": round(sum(times) / len(times), 3),
                "best_lap_s": round(min(times), 3),
                "tyre_age_at_start": s.get("tyre_age_at_start"),
            }
        )
    return rows


def _render_stint_timeline(
    stints_df: pd.DataFrame,
    drivers: dict[str, dict[str, Any]],
    height: int | None = None,
) -> None:
    if stints_df.empty:
        st.info("Sin datos de stints para graficar.")
        return

    by_compound = _compounds_known(stints_df)
    fig = go.Figure()
    drivers_in_data = sorted(stints_df["driver_key"].unique().tolist())
    seen: set[str] = set()

    for idx, drv_key in enumerate(drivers_in_data):
        sub = stints_df[stints_df["driver_key"] == drv_key].sort_values("stint_number")
        label = drivers.get(drv_key, {}).get("full_name", f"#{drv_key}")
        for _, s in sub.iterrows():
            if by_compound:
                color = COMPOUND_COLORS_OPENF1.get(s["compound"], "#6E6E76")
                tag = s["compound"]
                legend_key = f"c-{s['compound']}"
                legend_name = s["compound"].title()
                inside = "?" if s["compound"] == "UNKNOWN" else s["compound"][0]
            else:
                color = _stint_color(s["stint_number"])
                tag = f"Stint {s['stint_number']} (compuesto no disponible)"
                legend_key = f"s-{s['stint_number']}"
                legend_name = f"Stint {s['stint_number']}"
                inside = f"S{s['stint_number']}"

            text_fill = "#FFFFFF" if not by_compound or s["compound"] in ("SOFT", "INTERMEDIATE", "WET", "UNKNOWN") else "#0A0A0A"
            fig.add_trace(
                go.Bar(
                    x=[s["lap_end"] - s["lap_start"] + 1],
                    y=[label],
                    base=[s["lap_start"]],
                    orientation="h",
                    marker=dict(color=color, line=dict(color="#0A0A0A", width=1)),
                    text=inside,
                    textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(color=text_fill, size=9, family="JetBrains Mono, monospace"),
                    name=legend_name,
                    legendgroup=legend_key,
                    showlegend=legend_key not in seen,
                    hovertemplate=(
                        f"<b>{label}</b><br>{tag}<br>"
                        f"Laps {s['lap_start']}-{s['lap_end']} ({s['laps_completed']} vueltas)<br>"
                        f"Avg: {s['avg_lap_s']:.3f}s · Best: {s['best_lap_s']:.3f}s<extra></extra>"
                    ),
                )
            )
            seen.add(legend_key)

    legend_title = "Compuesto" if by_compound else "Stint"
    fig.update_layout(
        barmode="overlay",
        height=height or max(360, 52 * len(drivers_in_data) + 120),
        margin=dict(l=10, r=10, t=40, b=40),
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
        xaxis=dict(title="Vuelta", gridcolor="#1F1F1F", color="#8A92A6", zeroline=False),
        yaxis=dict(autorange="reversed", gridcolor="#1F1F1F", color="#FFFFFF"),
        title=dict(text="Timeline de stints por piloto", font=dict(color="#FFFFFF", size=14)),
        legend=dict(
            title=dict(text=legend_title, font=dict(color="#8A92A6", size=10)),
            bgcolor="#15151E",
            bordercolor="#1F1F1F",
            borderwidth=1,
            font=dict(size=10),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_pace_per_stint(
    stints_df: pd.DataFrame,
    drivers: dict[str, dict[str, Any]],
    height: int | None = None,
) -> None:
    if stints_df.empty:
        return

    by_compound = _compounds_known(stints_df)
    driver_index = {
        key: i for i, key in enumerate(sorted(stints_df["driver_key"].unique().tolist()))
    }
    fig = go.Figure()
    seen: set[str] = set()

    for _, s in stints_df.iterrows():
        dkey = s["driver_key"]
        info = drivers.get(dkey, {})
        label = info.get("full_name", f"#{dkey}")

        if by_compound:
            color = COMPOUND_COLORS_OPENF1.get(s["compound"], "#6E6E76")
            legend_key = f"c-{s['compound']}"
            legend_name = s["compound"].title()
            tag = s["compound"]
        else:
            color = _team_color(info.get("team_name", ""), driver_index.get(dkey, 0))
            legend_key = f"d-{dkey}"
            legend_name = label
            tag = "Compuesto no disponible"

        fig.add_trace(
            go.Scatter(
                x=[s["avg_lap_s"]],
                y=[s["best_lap_s"]],
                mode="markers",
                marker=dict(
                    size=max(10, min(38, s["laps_completed"] * 1.8)),
                    color=color,
                    line=dict(color="#0A0A0A", width=1.5),
                    opacity=0.9,
                ),
                name=legend_name,
                legendgroup=legend_key,
                showlegend=legend_key not in seen,
                hovertemplate=(
                    f"<b>{label}</b><br>Stint {s['stint_number']}<br>"
                    f"{tag}<br>"
                    f"Avg: {s['avg_lap_s']:.3f}s · Best: {s['best_lap_s']:.3f}s<br>"
                    f"{s['laps_completed']} vueltas<extra></extra>"
                ),
            )
        )
        seen.add(legend_key)

    fig.update_layout(
        title=dict(
            text="Pace por stint · avg vs best (tamaño = vueltas)",
            font=dict(color="#FFFFFF", size=14),
        ),
        xaxis=dict(title="Tiempo medio de vuelta (s)", gridcolor="#1F1F1F", color="#8A92A6", zeroline=False),
        yaxis=dict(title="Mejor vuelta del stint (s)", gridcolor="#1F1F1F", color="#8A92A6", zeroline=False),
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
        height=height or 440,
        margin=dict(l=10, r=10, t=50, b=40),
        legend=dict(
            title=dict(
                text="Compuesto" if by_compound else "Piloto",
                font=dict(color="#8A92A6", size=10),
            ),
            bgcolor="#15151E",
            bordercolor="#1F1F1F",
            borderwidth=1,
            font=dict(size=10),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_history_section(
    title_label: str,
    eyebrow_label: str,
    session: dict[str, Any],
    selected_driver_keys: list[str],
) -> None:
    circuit = session.get("circuit_short_name", "")
    country = session.get("country_name", "")
    date_start = str(session.get("date_start", ""))[:10]
    source = session.get("source", "openf1")

    source_note = (
        "Fuente: OpenF1"
        if source == "openf1"
        else "Fuente: Jolpica · compuesto no disponible"
    )
    st.markdown(
        f"""
        <div class="history-card">
          <div class="eyebrow">{eyebrow_label}</div>
          <div class="history-title">{title_label}</div>
          <div class="history-meta">{circuit}, {country} · {date_start} · {source_note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        drivers = session_drivers(session)
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo cargar pilotos: {exc}")
        return
    available = {k: v for k, v in drivers.items() if k in selected_driver_keys}
    if not available:
        st.warning("Selecciona al menos un piloto en los selectores de arriba.")
        return

    try:
        stints = session_stints(session)
        laps = session_laps(session)
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudieron cargar stints/vueltas: {exc}")
        return

    stints_metrics = _stint_metrics(stints, laps)
    stints_df = pd.DataFrame(stints_metrics)
    if stints_df.empty:
        st.info("No hay datos de stints para esta sesion.")
        return
    stints_df = stints_df[stints_df["driver_key"].isin(selected_driver_keys)].reset_index(drop=True)
    if stints_df.empty:
        st.info("Los pilotos seleccionados no tienen stints en esta sesion.")
        return

    st.markdown("### Ritmo por stint")
    if _compounds_known(stints_df):
        st.caption("Color: compuesto del neumatico (paleta Pirelli).")
    else:
        st.caption(
            "Color: el compuesto no esta disponible en esta fuente; "
            "el timeline se colorea por numero de stint y la dispersion por piloto (color de equipo)."
        )

    chart_height = max(380, 52 * len(available) + 130)
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        _render_stint_timeline(stints_df, available, height=chart_height)
    with col_b:
        _render_pace_per_stint(stints_df, available, height=chart_height)

    st.markdown("### Detalle de stints")
    table_rows = []
    for _, s in stints_df.iterrows():
        info = available.get(s["driver_key"], {})
        table_rows.append(
            {
                "Piloto": info.get("full_name", s["driver_key"]),
                "Equipo": info.get("team_name", ""),
                "Stint": int(s["stint_number"]),
                "Compuesto": s["compound"],
                "Vueltas": f"{int(s['lap_start'])}-{int(s['lap_end'])} ({int(s['laps_completed'])})",
                "Avg (s)": round(s["avg_lap_s"], 3),
                "Best (s)": round(s["best_lap_s"], 3),
            }
        )
    st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)


def render_history() -> None:
    render_header(
        "Historial de carreras",
        "Comparativa de stints por circuito · Train 2024 / Eval 2025",
    )

    mode = st.segmented_control(
        "Modo de comparacion",
        options=["single", "train_eval"],
        default="single",
        format_func=lambda m: {
            "single": "Comparar pilotos (mismo año)",
            "train_eval": "Train 2024 vs Eval 2025",
        }[m],
        label_visibility="collapsed",
        key="history_mode",
    ) or "single"

    if mode == "single":
        with st.container(border=True):
            c_year, c_race, c_drivers = st.columns([1, 2.1, 2.4], gap="medium")
            with c_year:
                year = st.selectbox("Temporada", options=[2025, 2024], index=0)

            try:
                sessions = _cached_sessions(year)
                meetings = _cached_meetings(year)
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo cargar el historial: {exc}")
                return
            if not sessions:
                st.warning(f"Sin carreras para {year}.")
                return

            def _session_label(s: dict[str, Any]) -> str:
                name = meetings.get(s.get("meeting_key"), s.get("circuit_short_name", "Carrera"))
                return f"R{s.get('round')} · {name} · {str(s.get('date_start', ''))[:10]}"

            with c_race:
                session_idx = st.selectbox(
                    "Carrera",
                    options=range(len(sessions)),
                    format_func=lambda i: _session_label(sessions[i]),
                )

            session = sessions[session_idx]
            session_display_name = meetings.get(
                session.get("meeting_key"), session.get("circuit_short_name", "Carrera")
            )

            try:
                drivers = session_drivers(session)
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo cargar pilotos: {exc}")
                return

            driver_keys_ordered = sorted(drivers, key=lambda k: drivers[k].get("full_name", ""))
            with c_drivers:
                selected_keys = st.multiselect(
                    "Pilotos a comparar",
                    options=driver_keys_ordered,
                    default=driver_keys_ordered[:3],
                    format_func=lambda k: _driver_label(drivers.get(k, {"full_name": k})),
                    max_selections=6,
                )

        if selected_keys:
            _render_history_section(
                title_label=session_display_name,
                eyebrow_label=f"{year} · Comparativa",
                session=session,
                selected_driver_keys=selected_keys,
            )
        else:
            st.info("Selecciona al menos un piloto.")

    else:
        with st.container(border=True):
            c_circuit, c_drivers2 = st.columns([1.4, 2.6], gap="medium")
            try:
                sessions_2024 = _cached_sessions(2024)
                sessions_2025 = _cached_sessions(2025)
                meetings_2024 = _cached_meetings(2024)
                meetings_2025 = _cached_meetings(2025)
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo cargar el historial: {exc}")
                return

            circuits = sorted(
                {s.get("circuit_short_name") for s in sessions_2024 + sessions_2025 if s.get("circuit_short_name")}
            )
            with c_circuit:
                circuit = st.selectbox("Circuito", options=circuits)

            s24 = next((s for s in sessions_2024 if s.get("circuit_short_name") == circuit), None)
            s25 = next((s for s in sessions_2025 if s.get("circuit_short_name") == circuit), None)

            if not s24 or not s25:
                st.warning(f"No hay datos para {circuit} en ambos años.")
                return

            try:
                drivers_24 = session_drivers(s24)
                drivers_25 = session_drivers(s25)
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudieron cargar pilotos: {exc}")
                return

            common = sorted(
                set(drivers_24.keys()) & set(drivers_25.keys()),
                key=lambda k: (drivers_24.get(k) or drivers_25.get(k) or {}).get("full_name", ""),
            )
            if not common:
                st.warning("No hay pilotos en comun entre 2024 y 2025 en este circuito.")
                return

            with c_drivers2:
                picks = st.multiselect(
                    "Pilotos a comparar",
                    options=common,
                    default=common[: min(4, len(common))],
                    format_func=lambda k: _driver_label(drivers_24.get(k) or drivers_25.get(k) or {"full_name": k}),
                    max_selections=6,
                )

        if picks:
            name_24 = meetings_2024.get(s24.get("meeting_key"), circuit)
            name_25 = meetings_2025.get(s25.get("meeting_key"), circuit)
            st.markdown("#### Train · 2024")
            _render_history_section(
                title_label=name_24,
                eyebrow_label="Train · 2024",
                session=s24,
                selected_driver_keys=picks,
            )
            st.markdown("#### Eval · 2025")
            _render_history_section(
                title_label=name_25,
                eyebrow_label="Eval · 2025",
                session=s25,
                selected_driver_keys=picks,
            )
        else:
            st.info("Selecciona al menos un piloto.")

    _render_model_content()


def render_season() -> None:
    render_header(*SECTIONS["season"])

    current_year = datetime.now(LOCAL_TZ).year
    year_options = [current_year, current_year - 1, current_year - 2]

    requested_year = st.session_state.get("season_year")
    year_default = year_options.index(requested_year) if requested_year in year_options else 0
    season = st.selectbox(
        "Temporada",
        options=year_options,
        index=year_default,
        key="season_year_widget",
    )

    try:
        races = fetch_season_schedule(season)
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo cargar la temporada {season}: {exc}")
        return

    if not races:
        st.info(f"No hay calendario disponible para {season}.")
        return

    race_options = {
        str(r.get("round")): r
        for r in races
        if r.get("round") is not None
    }
    round_list = list(race_options)

    requested_round = st.session_state.pop("season_round", None)
    round_default = round_list.index(str(requested_round)) if str(requested_round) in round_list else 0

    round_number = st.selectbox(
        "Ronda",
        options=round_list,
        index=round_default,
        format_func=lambda rnd: (
            f"R{rnd} · {race_options[rnd].get('raceName', 'Carrera')} · "
            f"{race_options[rnd].get('date', '')}"
        ),
    )
    selected_race = race_options[round_number]

    try:
        race_results = fetch_race_results(season, round_number)
    except Exception as exc:  # noqa: BLE001
        st.warning(f"No hay resultados publicados para esta ronda: {exc}")
        race_results = []

    st.markdown(
        f"""
        <div class="season-race-banner">
          <div class="eyebrow">Ronda {round_number} · {season}</div>
          <div class="season-race-name">{selected_race.get('raceName', 'Carrera')}</div>
          <div class="season-race-meta">{selected_race.get('Circuit', {}).get('circuitName', 'Circuito')} · {selected_race.get('date', '—')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not race_results:
        st.info("Esta ronda todavía no tiene resultados publicados.")
        return

    race_rows = []
    for result in race_results:
        driver = result.get("Driver", {})
        constructor = result.get("Constructor", {})
        fastest_lap = result.get("FastestLap", {}) or {}
        race_rows.append(
            {
                "Posicion": result.get("position", "—"),
                "Piloto": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                "Equipo": constructor.get("name", "—"),
                "Vueltas": result.get("laps", "—"),
                "Tiempo / estado": result.get("Time", {}).get("time", result.get("status", "—")),
                "Puntos": float(result.get("points", 0) or 0),
                "Vuelta rapida": fastest_lap.get("AverageSpeed", {}).get("speed", "—"),
            }
        )
    st.markdown("### Resultado de la ronda")
    st.dataframe(pd.DataFrame(race_rows), hide_index=True, use_container_width=True)

    with st.spinner("Calculando clasificacion acumulada..."):
        cumulative_points: dict[str, float] = {}
        for race in races:
            race_round = str(race.get("round"))
            if int(race_round) > int(round_number):
                continue
            try:
                results = fetch_race_results(season, race_round)
            except Exception:  # noqa: BLE001
                continue
            for result in results:
                driver = result.get("Driver", {})
                driver_name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip()
                if driver_name:
                    cumulative_points[driver_name] = cumulative_points.get(driver_name, 0) + float(result.get("points", 0) or 0)

    standings = (
        pd.DataFrame(
            [{"Piloto": name, "Puntos": points} for name, points in cumulative_points.items()]
        )
        .sort_values("Puntos", ascending=False)
        .reset_index(drop=True)
    )
    if standings.empty:
        st.info("Todavía no hay puntos acumulados para esta temporada.")
        return

    st.markdown("### Campeonato acumulado")
    chart = go.Figure(
        go.Bar(
            x=standings.head(10)["Puntos"],
            y=standings.head(10)["Piloto"],
            orientation="h",
            marker_color="#E10600",
            text=standings.head(10)["Puntos"],
            textposition="outside",
        )
    )
    chart.update_layout(
        height=max(300, 42 * min(10, len(standings)) + 80),
        margin=dict(l=10, r=50, t=20, b=20),
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
        xaxis=dict(title="Puntos", gridcolor="#1F1F1F", color="#8A92A6"),
        yaxis=dict(autorange="reversed", color="#FFFFFF"),
    )
    st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    st.dataframe(standings, hide_index=True, use_container_width=True)


def track_interest(section: str) -> None:
    """Registra interes de uso por seccion en la sesion actual."""
    if "interest_visits" not in st.session_state:
        st.session_state["interest_visits"] = {}
    visits = st.session_state["interest_visits"]
    visits[section] = visits.get(section, 0) + 1
    if "interest_first_seen" not in st.session_state:
        st.session_state["interest_first_seen"] = datetime.now(LOCAL_TZ)


def get_interest_stats() -> dict[str, Any]:
    visits = st.session_state.get("interest_visits", {})
    first_seen = st.session_state.get("interest_first_seen", datetime.now(LOCAL_TZ))
    total_views = sum(visits.values())
    session_minutes = max((datetime.now(LOCAL_TZ) - first_seen).total_seconds() / 60, 0.1)
    top_section = max(visits, key=visits.get) if visits else "—"
    return {
        "total_views": total_views,
        "sections_visited": len(visits),
        "top_section": _section_label(top_section),
        "session_minutes": round(session_minutes, 1),
        "views_per_min": round(total_views / session_minutes, 2),
        "visits": visits,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def _trained_model_report(train_year: int = 2024, eval_year: int = 2025) -> Any:
    train = prediccion.fetch_season_results(train_year)
    ev = prediccion.fetch_season_results(eval_year)
    return prediccion.train_and_evaluate(train, ev)


def _render_model_content() -> None:
    """KPIs y graficos del modelo predictivo. Se muestra dentro de Historial."""
    st.markdown("### Prediccion de resultados")
    st.caption(
        "Entrenamiento: temporada 2024 · Evaluacion: temporada 2025 · "
        "Modelo Ridge sobre posicion de salida y forma reciente."
    )

    try:
        report = _trained_model_report()
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo entrenar el modelo: {exc}")
        return

    eval_frame = report.eval_frame
    last_round = int(eval_frame["round"].max()) if not eval_frame.empty else 0
    last_race = eval_frame[eval_frame["round"] == last_round] if last_round else eval_frame
    top_pred = last_race.nsmallest(1, "predicted").iloc[0] if not last_race.empty else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Posicion predicha",
        f"P{top_pred['predicted']:.1f}" if top_pred is not None else "—",
        (top_pred["driver_name"] if top_pred is not None else None),
    )
    k2.metric(
        "Error de prediccion",
        f"{report.mae:.2f} pos",
        f"baseline {report.baseline_mae:.2f}",
    )
    k3.metric(
        "Precision del modelo",
        f"{report.podium_hit_rate:.0f}%",
        "acierto de podio",
    )
    k4.metric(
        "Correlacion de ranking",
        f"{report.rank_correlation:.2f}",
        "Spearman",
    )

    col_a, col_b = st.columns([1.4, 1])

    with col_a:
        fig_imp = go.Figure(
            go.Bar(
                x=list(report.feature_importance.values()),
                y=[_feature_label(k) for k in report.feature_importance.keys()],
                orientation="h",
                marker=dict(color=["#E10600", "#FFD500", "#FFFFFF", "#00B050"]),
                text=[f"{v*100:.0f}%" for v in report.feature_importance.values()],
                textposition="inside",
                textfont=dict(color="#0A0A0A", family="JetBrains Mono, monospace", size=11),
            )
        )
        fig_imp.update_layout(
            title=dict(text="Peso de cada variable", font=dict(color="#FFFFFF", size=14)),
            xaxis=dict(title="Importancia relativa", gridcolor="#1F1F1F", color="#8A92A6", tickformat=".0%"),
            yaxis=dict(gridcolor="#1F1F1F", color="#FFFFFF"),
            paper_bgcolor="#0A0A0A",
            plot_bgcolor="#0A0A0A",
            font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
            height=320,
            margin=dict(l=10, r=10, t=50, b=40),
        )
        st.plotly_chart(fig_imp, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        if not eval_frame.empty:
            fig_err = go.Figure(
                go.Histogram(
                    x=eval_frame["abs_error"],
                    nbinsx=14,
                    marker=dict(color="#E10600", line=dict(color="#0A0A0A", width=1)),
                )
            )
            fig_err.add_vline(
                x=report.mae,
                line=dict(color="#00E5FF", width=2, dash="dash"),
                annotation_text=f"MAE {report.mae:.2f}",
                annotation_font_color="#00E5FF",
            )
            fig_err.update_layout(
                title=dict(text="Distribucion del error absoluto", font=dict(color="#FFFFFF", size=14)),
                xaxis=dict(title="Error (posiciones)", gridcolor="#1F1F1F", color="#8A92A6"),
                yaxis=dict(title="Carreras", gridcolor="#1F1F1F", color="#8A92A6"),
                paper_bgcolor="#0A0A0A",
                plot_bgcolor="#0A0A0A",
                font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
                height=320,
                margin=dict(l=10, r=10, t=50, b=40),
            )
            st.plotly_chart(fig_err, use_container_width=True, config={"displayModeBar": False})

    st.markdown("### Predicciones de la ultima carrera evaluada")
    if not last_race.empty:
        table = last_race.sort_values("predicted").head(10).copy()
        table["Pos. real"] = table["position"].astype(int)
        table["Pos. predicha"] = table["predicted"].round(1)
        table["Error"] = table["abs_error"].round(2)
        table["Salida"] = table["grid"].astype(int)
        st.dataframe(
            table[["driver_name", "constructor_name", "Salida", "Pos. predicha", "Pos. real", "Error"]].rename(
                columns={"driver_name": "Piloto", "constructor_name": "Equipo"}
            ),
            hide_index=True,
            use_container_width=True,
        )

    baseline_delta = report.baseline_mae - report.mae
    st.info(
        f"El modelo reduce el error absoluto medio en {baseline_delta:.2f} posiciones frente al baseline "
        f"(predecir la posicion de salida). Correlacion de ranking {report.rank_correlation:.2f} "
        f"sobre {report.eval_rows} resultados de la temporada 2025."
    )


def _feature_label(name: str) -> str:
    return {
        "grid": "Posicion de salida",
        "driver_form": "Forma del piloto",
        "constructor_form": "Forma del equipo",
    }.get(name, name)


def render_prediction() -> None:
    render_header(*SECTIONS["prediction"])
    next_race = get_next_race()
    default_key = match_circuit_key(next_race) if next_race else None
    default_laps = sim.CIRCUITS[default_key].typical_laps if default_key else 58
    race_name = next_race.get("raceName") if next_race else "Proxima carrera"
    race_date = parse_iso_date(next_race.get("date")) if next_race else None
    race_circuit_api = next_race.get("Circuit", {}).get("circuitName") if next_race else None
    race_locality = next_race.get("Circuit", {}).get("Location", {}).get("locality") if next_race else None
    race_country = next_race.get("Circuit", {}).get("Location", {}).get("country") if next_race else None

    if next_race:
        date_str = fmt_date_long(race_date) if race_date else next_race.get("date", "—")
        st.markdown(
            f"""
            <div class="next-race-card">
              <div class="eyebrow">Proxima carrera · Raceweek</div>
              <div class="next-race-name">{race_name}</div>
              <div class="next-race-meta">{race_circuit_api} · {race_locality}, {race_country} · {date_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not default_key:
            st.warning(
                f"No tenemos datos de simulacion para {race_locality or race_circuit_api}. "
                "Puedes elegir otro circuito abajo."
            )
    else:
        st.info("No hay carreras proximas en el calendario de Formula 1. Configura manualmente.")

    presets = sorted(sim.CIRCUITS.keys())
    col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
    with col_a:
        default_idx = presets.index(default_key) if default_key in presets else (presets.index("Silverstone") if "Silverstone" in presets else 0)
        circuit_name = st.selectbox(
            "Circuito",
            options=presets,
            index=default_idx,
            help="Por defecto: proxima carrera de Raceweek. Cambialo para simular otro circuito.",
        )
    with col_b:
        total_laps = st.number_input("Vueltas totales", min_value=20, max_value=90, value=default_laps, step=1)
    with col_c:
        starting = st.selectbox("Neumatico de salida", options=sim.COMPOUND_ORDER, index=1)
    with col_d:
        monte_carlo = st.number_input("Simulaciones MC", min_value=1, max_value=500, value=50, step=10)
    noise_sigma = st.slider("Ruido por vuelta (s)", min_value=0.0, max_value=0.5, value=0.10, step=0.01)
    rain = st.checkbox("Considerar estrategias para lluvia (intermedio / wet)", value=False)

    circuit = sim.CIRCUITS[circuit_name]
    results = sim.recommend(circuit, int(total_laps), monte_carlo=int(monte_carlo), noise_sigma=float(noise_sigma))

    if not results:
        st.warning("No se encontraron estrategias validas para esta combinacion de vueltas y circuito.")
        return

    best = results[0]
    gap_to_best = [(r.total_time - best.total_time) for r in results]

    compounds_html = "".join(render_compound_chip(c) for c, _ in best.strategy.stints)
    pit_laps_text = ", ".join(str(l) for l in best.pit_laps) or "—"
    margin = gap_to_best[1] if len(gap_to_best) > 1 else None
    sigma_text = f"σ ±{best.sample_std:.2f} s" if best.sample_std else "σ —"

    # Estrategia + KPIs en una sola fila para evitar duplicar datos
    s_col, c1, c2, c3 = st.columns([2.3, 1.1, 1, 1.25], gap="small")
    with s_col:
        st.markdown(
            f"""
            <div class="strategy-inline">
              <span class="strategy-inline-tag">Pole position</span>
              <span class="strategy-inline-name">{best.strategy.name}</span>
              <span class="strategy-inline-chips">{compounds_html}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    c1.metric("Tiempo total", sim.format_time(best.total_time), "estrategia optima")
    c2.metric("Paradas", best.strategy.stops, f"pit {pit_laps_text}")
    c3.metric("Margen vs 2°", f"+{margin:.2f} s" if margin is not None else "—", sigma_text)

    if len(gap_to_best) > 1 and gap_to_best[1] < 1.0:
        st.caption(
            "Margen ajustado (<1 s): la eleccion es sensible a la variabilidad. "
            "Revisa la desviacion Monte Carlo antes de fijar el plan."
        )

    table_rows = [
        {
            "Estrategia": r.strategy.name,
            "Paradas": r.strategy.stops,
            "Stints": r.strategy.compounds,
            "Pit laps": ", ".join(str(l) for l in r.pit_laps) or "—",
            "Tiempo": sim.format_time(r.total_time),
            "Gap (s)": round(gap, 2),
            "Std MC (s)": round(r.sample_std, 2) if r.sample_std else None,
        }
        for r, gap in zip(results, gap_to_best)
    ]
    st.markdown("### Ranking de estrategias")
    st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)

    top_n = min(3, len(results))
    fig = go.Figure()
    palette = {
        "S": "#E10600",
        "M": "#FFD500",
        "H": "#FFFFFF",
        "I": "#00B050",
        "W": "#1E90FF",
    }
    for r in results[:top_n]:
        laps_x = [lap for lap, _, _ in r.per_lap]
        times_y = [t for _, t, _ in r.per_lap]
        compound_trace = [c for _, _, c in r.per_lap]
        for short, color in palette.items():
            mask = [i for i, c in enumerate(compound_trace) if c == short]
            if not mask:
                continue
            fig.add_trace(
                go.Scatter(
                    x=[laps_x[i] for i in mask],
                    y=[times_y[i] for i in mask],
                    mode="markers",
                    name=f"{r.strategy.name} · {short}",
                    marker=dict(size=7, color=color, line=dict(width=1, color="#000000")),
                    legendgroup=r.strategy.name,
                    showlegend=True,
                )
            )
        for pit_lap in r.pit_laps:
            fig.add_vline(
                x=pit_lap + 0.5,
                line=dict(color="#E10600", width=1.2, dash="dot"),
                opacity=0.7,
            )
    fig.update_layout(
        title=dict(text="Tiempo por vuelta · Top 3 estrategias", font=dict(color="#FFFFFF", size=16, family="Chivo, sans-serif")),
        xaxis=dict(title="Vuelta", gridcolor="#1F1F1F", color="#8A92A6"),
        yaxis=dict(title="Tiempo de vuelta (s)", gridcolor="#1F1F1F", color="#8A92A6"),
        template="plotly_dark",
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
        height=440,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(bgcolor="#000000", bordercolor="#1F1F1F", borderwidth=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _apply_query_navigation() -> None:
    """Lee los parametros de la URL (enlaces de Raceweek) y fija la navegacion.

    Debe ejecutarse ANTES de crear el radio del sidebar para que Streamlit tome
    el valor como estado inicial del widget.
    """
    try:
        params = st.query_params
        target = params.get("section")
        season = params.get("season")
        round_number = params.get("round")
    except Exception:  # noqa: BLE001
        return

    if not any((target, season, round_number)):
        return

    if target in ("overview", "season", "prediction", "telemetry"):
        st.session_state["nav_section"] = target
    if season:
        st.session_state["season_year"] = int(season)
    if round_number:
        st.session_state["season_round"] = str(round_number)

    try:
        st.query_params.clear()
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    _apply_query_navigation()
    section = render_sidebar()
    track_interest(section)

    # El modo pantalla completa pertenece solo a Raceweek
    if section != "overview":
        st.session_state["map_fullscreen"] = False

    if section == "overview":
        render_overview()
    elif section == "season":
        render_season()
    elif section == "prediction":
        render_prediction()
    else:
        render_history()

    render_credits_footer()


if __name__ == "__main__":
    main()
