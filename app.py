"""Dashboard de visualizacion y prediccion de resultados de Formula 1."""

from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import simulacion as sim
import openf1

st.set_page_config(
    page_title="Apex Analytics · F1",
    layout="wide",
    page_icon="C:\\Users\\djate\\Downloads\\Car project\\assets\\media\\ApexAnalytics-logo-icono.ico"
)

with open("assets/style.css", "r", encoding="utf-8") as _css_file:
    st.markdown(f"<style>{_css_file.read()}</style>", unsafe_allow_html=True)

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

        section = st.radio(
            "Secciones",
            options=["overview", "prediction", "telemetry"],
            format_func=lambda s: {
                "overview": "Raceweek",
                "prediction": "Simulacion",
                "telemetry": "Historial",
            }[s],
            label_visibility="collapsed",
        )

        st.markdown("---")
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
        "Grandes Premios y sesiones de la semana en curso en el calendario FIA.",
    ),
    "prediction": (
        "Simulacion",
        "Simulador de paradas en boxes segun circuito, clima y degradacion de neumaticos.",
    ),
    "telemetry": (
        "Historial",
        "Comparativas de ritmo medio y degradacion por stint (en construccion).",
    ),
}


def render_placeholder(title: str, subtitle: str, ideas: list[str]) -> None:
    render_header(title, subtitle)
    st.info("Esta vista es un placeholder. Aun no hay datos cargados.")
    st.markdown("### Siguientes pasos")
    for idea in ideas:
        st.markdown(f"- {idea}")


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


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_season_schedule(season: int | None = None) -> list[dict[str, Any]]:
    season = season or datetime.now(LOCAL_TZ).year
    url = f"{JOLPICA_BASE}/{season}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "race-analytics/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    races = (
        payload.get("MRData", {}).get("RaceTable", {}).get("Races", []) or []
    )
    return races


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
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode"
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


def _sector_offsets(lat: float, lon: float) -> list[tuple[float, float, str]]:
    """Aproxima las posiciones de los 3 sectores alrededor del centro del circuito."""
    d = 0.003
    return [
        (lat + d, lon - d * 0.6, "S1"),
        (lat - d * 0.4, lon + d * 0.9, "S2"),
        (lat + d * 0.7, lon + d * 0.5, "S3"),
    ]


def render_circuit_map(race: dict[str, Any]) -> None:
    from circuits import generate_circuit_svg
    circuit_api_name = race.get("Circuit", {}).get("circuitName", "Circuito")
    circuit_key = match_circuit_key(race) or circuit_api_name
    svg = generate_circuit_svg(circuit_key)

    lat, lon = _get_circuit_coords(race)
    locality = race.get("Circuit", {}).get("Location", {}).get("locality", "")
    country = race.get("Circuit", {}).get("Location", {}).get("country", "")
    coords_text = f"{lat:.4f}, {lon:.4f}" if lat is not None and lon is not None else "—"

    st.markdown(
        f"""
        <div class="circuit-card">
          <div class="circuit-coords">
            <span class="eyebrow">Circuito</span>
            <span class="circuit-name">{circuit_api_name}</span>
            <span class="circuit-place">{locality}, {country} · {coords_text}</span>
          </div>
          {svg}
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    cw = data.get("current_weather", {}) or {}
    daily = data.get("daily", {}) or {}
    code = int(cw.get("weathercode", 0))
    desc = WMO_CODE.get(code, f"Codigo {code}")
    icon = WMO_ICON.get(code, "❓")
    temp = cw.get("temperature", "—")
    wind = cw.get("windspeed", "—")
    wind_dir = cw.get("winddirection", "—")

    tmax_list = daily.get("temperature_2m_max", [])
    tmin_list = daily.get("temperature_2m_min", [])
    pop_list = daily.get("precipitation_probability_max", [])

    day_labels = []
    for i in range(min(3, len(tmax_list))):
        if i == 0:
            day_labels.append("Hoy")
        elif i == 1:
            day_labels.append("Manana")
        else:
            day_labels.append("Pasado manana")

    forecast_rows = "".join(
        f"<div class='wx-day'>"
        f"<div class='wx-day-label'>{day_labels[i]}</div>"
        f"<div class='wx-day-temps'>{tmax_list[i]:.0f}° / {tmin_list[i]:.0f}°</div>"
        f"<div class='wx-day-pop'>Lluvia: {pop_list[i] if i < len(pop_list) else 0}%</div>"
        f"</div>"
        for i in range(min(3, len(tmax_list)))
    )

    st.markdown(
        f"""
        <div class="weather-card">
            <div class="wx-header">
                <div>
                    <div class="eyebrow">Clima · {locality}, {country}</div>
                    <div class="wx-now">
                        <span class="wx-icon">{icon}</span>
                        <span class="wx-temp">{temp}°C</span>
                    </div>
                    <div class="wx-desc">{desc}</div>
                </div>
                <div class="wx-wind">
                    <div class="wx-wind-val">{wind} km/h</div>
                    <div class="wx-wind-dir">dir {wind_dir}°</div>
                </div>
            </div>
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
    if top_cols[2].button("Actualizar", use_container_width=True):
        fetch_season_schedule.clear()
        st.rerun()

    try:
        races = fetch_season_schedule()
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo cargar el calendario FIA: {exc}")
        return

    events = events_in_week(races, week_start, week_end)

    k1, k2, k3 = st.columns(3)
    k1.metric("Eventos esta semana", len(events))
    k2.metric("Carreras en la temporada", len(races))
    next_race = next((r for r in races if parse_iso_date(r.get("date")) and parse_iso_date(r["date"]) >= today), None)
    k3.metric(
        "Proxima carrera",
        next_race["raceName"] if next_race else "—",
        (
            fmt_date_short(parse_iso_date(next_race["date"]))
            if next_race and parse_iso_date(next_race.get("date"))
            else None
        ),
    )

    st.markdown("### Eventos de la semana")
    if not events:
        st.info("No hay Grandes Premios esta semana. Revisa el calendario completo de la temporada abajo.")
    else:
        for event in events:
            render_event_card(event)

    if next_race:
        st.markdown("### Datos geométricos")
        wx_col, map_col = st.columns([1, 1.4], gap="medium")
        with wx_col:
            render_weather_card(next_race)
        with map_col:
            render_circuit_map(next_race)

    with st.expander("Calendario completo de la temporada"):
        calendar_rows = []
        for r in races:
            start, end = weekend_bounds(r)
            calendar_rows.append(
                {
                    "Ronda": r.get("round"),
                    "Gran Premio": r.get("raceName"),
                    "Circuito": r.get("Circuit", {}).get("circuitName"),
                    "Pais": r.get("Circuit", {}).get("Location", {}).get("country"),
                    "Inicio": fmt_date_short(start),
                    "Fin": fmt_date_short(end),
                }
            )
        st.dataframe(pd.DataFrame(calendar_rows), hide_index=True, use_container_width=True)


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


def get_next_race() -> dict[str, Any] | None:
    today = datetime.now(LOCAL_TZ).date()
    try:
        races = fetch_season_schedule()
    except Exception:  # noqa: BLE001
        return None
    for r in races:
        d = parse_iso_date(r.get("date"))
        if d and d >= today:
            return r
    return races[-1] if races else None


def _open_video_background(fixed: bool = False) -> None:
    import base64 as _b64
    with open("assets/media/F1 car fondo.mp4", "rb") as _vf:
        _video_b64 = _b64.b64encode(_vf.read()).decode("ascii")
    _video_src = f"data:video/mp4;base64,{_video_b64}"
    wrap_class = "overview-wrap fixed-bg" if fixed else "overview-wrap"
    st.markdown(
        f"""
        <div class="{wrap_class}">
          <video class="bg-video" autoplay muted loop playsinline preload="auto">
            <source src="{_video_src}" type="video/mp4">
          </video>
          <div class="bg-overlay"></div>
        """,
        unsafe_allow_html=True,
    )


def _close_video_background() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


COMPOUND_COLORS_OPENF1 = {
    "SOFT": "#E10600",
    "MEDIUM": "#FFD500",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#00B050",
    "WET": "#1E90FF",
    "UNKNOWN": "#6E6E76",
}


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_sessions(year: int) -> list[dict[str, Any]]:
    return openf1.get_sessions(year)


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_meetings(year: int) -> dict[int, str]:
    meetings = openf1.get_meetings(year)
    return {m["meeting_key"]: m.get("meeting_name", "") for m in meetings}


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_drivers(session_key: int) -> list[dict[str, Any]]:
    return openf1.get_drivers(session_key)


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_stints(session_key: int) -> list[dict[str, Any]]:
    return openf1.get_stints(session_key)


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_laps(session_key: int) -> list[dict[str, Any]]:
    return openf1.get_laps(session_key)


def _driver_label(d: dict[str, Any]) -> str:
    return f"{d.get('full_name', '?')} ({d.get('team_name', '?')})"


def _stint_metrics(stints: list[dict[str, Any]], laps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    laps_by_driver: dict[int, list[dict[str, Any]]] = {}
    for lap in laps:
        if lap.get("lap_duration") is None or lap.get("lap_number") is None:
            continue
        laps_by_driver.setdefault(lap["driver_number"], []).append(lap)

    rows: list[dict[str, Any]] = []
    for s in stints:
        lap_start = s.get("lap_start")
        lap_end = s.get("lap_end")
        if lap_start is None or lap_end is None:
            continue
        drv_laps = laps_by_driver.get(s["driver_number"], [])
        relevant = [
            lap for lap in drv_laps
            if lap_start <= lap["lap_number"] <= lap_end
            and not lap.get("is_pit_out_lap")
            and lap.get("lap_duration") is not None
        ]
        if not relevant:
            continue
        times = [lap["lap_duration"] for lap in relevant]
        compound = (s.get("compound") or "UNKNOWN").upper()
        rows.append(
            {
                "driver_number": s["driver_number"],
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


def _render_stint_timeline(stints_df: pd.DataFrame, drivers: dict[int, dict[str, Any]]) -> None:
    if stints_df.empty:
        st.info("Sin datos de stints para graficar.")
        return

    fig = go.Figure()
    drivers_in_data = sorted(stints_df["driver_number"].unique().tolist())
    for idx, drv_num in enumerate(drivers_in_data):
        sub = stints_df[stints_df["driver_number"] == drv_num].sort_values("stint_number")
        label = drivers.get(drv_num, {}).get("full_name", f"#{drv_num}")
        for _, s in sub.iterrows():
            fig.add_trace(
                go.Bar(
                    x=[s["lap_end"] - s["lap_start"] + 1],
                    y=[label],
                    base=[s["lap_start"]],
                    orientation="h",
                    marker=dict(
                        color=COMPOUND_COLORS_OPENF1.get(s["compound"], "#6E6E76"),
                        line=dict(color="#0A0A0A", width=1),
                    ),
                    text=f"{s['compound'][0]}",
                    textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(color="#0A0A0A", size=10, family="JetBrains Mono, monospace"),
                    hovertemplate=(
                        f"<b>{label}</b><br>"
                        f"Stint {s['stint_number']} · {s['compound']}<br>"
                        f"Laps {s['lap_start']}-{s['lap_end']} ({s['laps_completed']} vueltas)<br>"
                        f"Avg: {s['avg_lap_s']:.3f}s · Best: {s['best_lap_s']:.3f}s<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

    fig.update_layout(
        barmode="overlay",
        height=max(120, 60 * len(drivers_in_data) + 60),
        margin=dict(l=10, r=10, t=30, b=30),
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
        xaxis=dict(title="Vuelta", gridcolor="#1F1F1F", color="#8A92A6"),
        yaxis=dict(autorange="reversed", gridcolor="#1F1F1F", color="#FFFFFF"),
        title=dict(text="Timeline de stints por piloto", font=dict(color="#FFFFFF", size=14)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_pace_per_stint(stints_df: pd.DataFrame, drivers: dict[int, dict[str, Any]]) -> None:
    if stints_df.empty:
        return
    fig = go.Figure()
    for _, s in stints_df.iterrows():
        label = drivers.get(s["driver_number"], {}).get("full_name", f"#{s['driver_number']}")
        fig.add_trace(
            go.Scatter(
                x=[s["avg_lap_s"]],
                y=[s["best_lap_s"]],
                mode="markers",
                marker=dict(
                    size=max(8, min(36, s["laps_completed"] * 1.6)),
                    color=COMPOUND_COLORS_OPENF1.get(s["compound"], "#6E6E76"),
                    line=dict(color="#0A0A0A", width=1),
                    opacity=0.85,
                ),
                name=f"{label} · {s['compound']}",
                hovertemplate=(
                    f"<b>{label}</b><br>Stint {s['stint_number']} · {s['compound']}<br>"
                    f"Avg: {s['avg_lap_s']:.3f}s · Best: {s['best_lap_s']:.3f}s<br>"
                    f"{s['laps_completed']} vueltas<extra></extra>"
                ),
                showlegend=True,
            )
        )
    fig.update_layout(
        title=dict(text="Pace por stint · avg vs best (tamano = vueltas)", font=dict(color="#FFFFFF", size=14)),
        xaxis=dict(title="Tiempo medio de vuelta (s)", gridcolor="#1F1F1F", color="#8A92A6"),
        yaxis=dict(title="Mejor vuelta del stint (s)", gridcolor="#1F1F1F", color="#8A92A6"),
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#FFFFFF", family="Chivo, sans-serif"),
        height=420,
        margin=dict(l=10, r=10, t=50, b=40),
        legend=dict(bgcolor="#15151E", bordercolor="#1F1F1F", borderwidth=1, font=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_history_section(
    title_label: str,
    eyebrow_label: str,
    session: dict[str, Any],
    selected_driver_numbers: list[int],
) -> None:
    session_key = session["session_key"]
    circuit = session.get("circuit_short_name", "")
    country = session.get("country_name", "")
    date_start = session.get("date_start", "")[:10]

    st.markdown(
        f"""
        <div class="history-card">
          <div class="eyebrow">{eyebrow_label}</div>
          <div class="history-title">{title_label}</div>
          <div class="history-meta">{circuit}, {country} · {date_start}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        drivers = _cached_drivers(session_key)
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo cargar drivers: {exc}")
        return
    drivers_by_num = {d["driver_number"]: d for d in drivers}
    available = [d for d in drivers if d["driver_number"] in selected_driver_numbers]
    if not available:
        st.warning("Selecciona al menos un piloto en los selectores de arriba.")
        return

    try:
        stints = _cached_stints(session_key)
        laps = _cached_laps(session_key)
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudieron cargar stints/laps: {exc}")
        return

    stints_metrics = _stint_metrics(stints, laps)
    stints_df = pd.DataFrame(stints_metrics)
    if stints_df.empty:
        st.info("No hay datos de stints para esta sesion.")
        return
    stints_df = stints_df[stints_df["driver_number"].isin(selected_driver_numbers)].reset_index(drop=True)
    if stints_df.empty:
        st.info("Los pilotos seleccionados no tienen stints en esta sesion.")
        return

    available_by_num = {d["driver_number"]: d for d in available}

    col_a, col_b = st.columns(2)
    with col_a:
        _render_stint_timeline(stints_df, available_by_num)
    with col_b:
        _render_pace_per_stint(stints_df, available_by_num)

    st.markdown("### Tabla de stints")
    table_rows = []
    for _, s in stints_df.iterrows():
        label = available_by_num.get(s["driver_number"], {}).get("full_name", f"#{s['driver_number']}")
        team = available_by_num.get(s["driver_number"], {}).get("team_name", "")
        table_rows.append(
            {
                "Piloto": label,
                "Equipo": team,
                "Stint": int(s["stint_number"]),
                "Compuesto": s["compound"],
                "Vueltas": f"{int(s['lap_start'])}-{int(s['lap_end'])} ({int(s['laps_completed'])})",
                "Avg (s)": round(s["avg_lap_s"], 3),
                "Best (s)": round(s["best_lap_s"], 3),
            }
        )
    st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)


def render_history() -> None:
    _open_video_background(fixed=True)
    render_header(
        "Historial de carreras",
        "Comparativa de stints por circuito · Train 2024 / Eval 2025",
    )

    if "history_mode" not in st.session_state:
        st.session_state["history_mode"] = "single"

    def _set_mode(value: str) -> None:
        st.session_state["history_mode"] = value

    mode = st.session_state["history_mode"]
    st.markdown(
        f"""
        <div class="mode-toggle">
          <div class="mode-label">Modo de comparacion</div>
          <div class="mode-pills">
            <div class="mode-pill {'active' if mode == 'single' else ''}">Comparar pilotos (mismo ano)</div>
            <div class="mode-pill {'active' if mode == 'train_eval' else ''}">Train 2024 vs Eval 2025</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    btn_a, btn_b, _ = st.columns([1, 1, 4])
    with btn_a:
        if st.button("Comparar pilotos (mismo ano)", key="mode_btn_single", use_container_width=True):
            _set_mode("single")
            st.rerun()
    with btn_b:
        if st.button("Train 2024 vs Eval 2025", key="mode_btn_train_eval", use_container_width=True):
            _set_mode("train_eval")
            st.rerun()
    mode = st.session_state["history_mode"]

    if mode == "single":
        col_y, col_d = st.columns([1, 3])
        with col_y:
            year = st.selectbox("Temporada", options=[2025, 2024], index=0)
        try:
            sessions = _cached_sessions(year)
            meetings = _cached_meetings(year)
        except Exception as exc:  # noqa: BLE001
            st.error(f"No se pudo cargar OpenF1: {exc}")
            _close_video_background()
            return
        if not sessions:
            st.warning(f"Sin carreras para {year}.")
            _close_video_background()
            return

        session_labels = [
            f"R{s['meeting_key'] % 100} · {meetings.get(s['meeting_key'], s['circuit_short_name'])} · {s['date_start'][:10]}"
            for s in sessions
        ]
        with col_d:
            session_idx = st.selectbox(
                "Carrera",
                options=range(len(sessions)),
                format_func=lambda i: session_labels[i],
            )

        session = sessions[session_idx]
        session_display_name = meetings.get(session["meeting_key"], session.get("circuit_short_name", "Carrera"))
        try:
            drivers = _cached_drivers(session["session_key"])
        except Exception as exc:  # noqa: BLE001
            st.error(f"No se pudo cargar drivers: {exc}")
            _close_video_background()
            return

        driver_opts = sorted(drivers, key=lambda d: d.get("full_name", ""))
        driver_numbers = st.multiselect(
            "Pilotos a comparar",
            options=[d["driver_number"] for d in driver_opts],
            default=[d["driver_number"] for d in driver_opts[:3]],
            format_func=lambda n: _driver_label(next((d for d in driver_opts if d["driver_number"] == n), {"full_name": f"#{n}"})),
            max_selections=6,
        )

        if driver_numbers:
            _render_history_section(
                title_label=session_display_name,
                eyebrow_label=f"{year} · Comparativa",
                session=session,
                selected_driver_numbers=driver_numbers,
            )
        else:
            st.info("Selecciona al menos un piloto.")

    else:
        st.caption("Entrenamiento: 2024 · Evaluacion: 2025")
        try:
            sessions_2024 = _cached_sessions(2024)
            sessions_2025 = _cached_sessions(2025)
            meetings_2024 = _cached_meetings(2024)
            meetings_2025 = _cached_meetings(2025)
        except Exception as exc:  # noqa: BLE001
            st.error(f"No se pudo cargar OpenF1: {exc}")
            _close_video_background()
            return

        circuits = sorted({s.get("circuit_short_name") for s in sessions_2024 + sessions_2025 if s.get("circuit_short_name")})
        circuit = st.selectbox("Circuito", options=circuits)

        s24 = next((s for s in sessions_2024 if s.get("circuit_short_name") == circuit), None)
        s25 = next((s for s in sessions_2025 if s.get("circuit_short_name") == circuit), None)

        if not s24 or not s25:
            st.warning(f"No hay datos para {circuit} en ambos anos.")
            _close_video_background()
            return

        try:
            drivers_24 = {d["driver_number"]: d for d in _cached_drivers(s24["session_key"])}
            drivers_25 = {d["driver_number"]: d for d in _cached_drivers(s25["session_key"])}
        except Exception as exc:  # noqa: BLE001
            st.error(f"No se pudieron cargar drivers: {exc}")
            _close_video_background()
            return

        common = sorted(set(drivers_24.keys()) & set(drivers_25.keys()))
        if not common:
            st.warning("No hay pilotos en comun entre 2024 y 2025 en este circuito.")
            _close_video_background()
            return

        default_picks = common[: min(4, len(common))]
        picks = st.multiselect(
            "Pilotos a comparar",
            options=common,
            default=default_picks,
            format_func=lambda n: _driver_label(drivers_24.get(n) or drivers_25.get(n) or {"full_name": f"#{n}"}),
            max_selections=6,
        )

        if picks:
            name_24 = meetings_2024.get(s24["meeting_key"], circuit)
            name_25 = meetings_2025.get(s25["meeting_key"], circuit)
            st.markdown("#### Train · 2024")
            _render_history_section(
                title_label=name_24,
                eyebrow_label="Train · 2024",
                session=s24,
                selected_driver_numbers=picks,
            )
            st.markdown("#### Eval · 2025")
            _render_history_section(
                title_label=name_25,
                eyebrow_label="Eval · 2025",
                session=s25,
                selected_driver_numbers=picks,
            )
        else:
            st.info("Selecciona al menos un piloto.")

    _close_video_background()


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
        st.info("No hay carreras proximas en el calendario FIA. Configura manualmente.")

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

    st.markdown(
        f"""
        <div class="strategy-banner">
            <span class="eyebrow">Estrategia ganadora</span>
            <div style="color:#FFFFFF;font-size:1.5rem;font-weight:800;margin-top:0.3rem;text-transform:uppercase;">
                {best.strategy.name}
            </div>
            <div style="color:#C0C0C0;font-size:0.9rem;margin-top:0.4rem;">
                Tiempo proyectado: <b style="color:#FFFFFF">{sim.format_time(best.total_time)}</b> ·
                Paradas: <b style="color:#FFFFFF">{best.strategy.stops}</b> ·
                Ventanas de pit: <b style="color:#FFFFFF">{pit_laps_text}</b>
            </div>
            <div style="margin-top:0.6rem;">{compounds_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tiempo total", sim.format_time(best.total_time))
    c2.metric("Paradas", best.strategy.stops)
    c3.metric("Margen vs 2°", f"+{gap_to_best[1]:.2f} s" if len(gap_to_best) > 1 else "—")
    c4.metric("Stints", best.strategy.compounds)

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

    with st.expander("Parametros del modelo"):
        st.json(
            {
                "circuito": circuit.name,
                "vuelta_base_s": circuit.base_lap_time,
                "pit_loss_s": circuit.pit_loss,
                "deg_factor": circuit.deg_factor,
                "overtaking_difficulty": circuit.overtaking_difficulty,
                "safety_car_prob": circuit.safety_car_prob,
                "compounds": {
                    k: {
                        "name": c.name,
                        "base_pace": c.base_pace,
                        "deg_rate": c.deg_rate,
                        "cliff_lap": c.cliff_lap,
                        "cliff_drop": c.cliff_drop,
                        "min_stint": c.min_stint,
                    }
                    for k, c in sim.COMPOUNDS.items()
                },
            }
        )


def main() -> None:
    section = render_sidebar()
    title, subtitle = SECTIONS[section]

    if section == "overview":
        render_overview()
    elif section == "prediction":
        render_prediction()
    else:
        render_history()


if __name__ == "__main__":
    main()
