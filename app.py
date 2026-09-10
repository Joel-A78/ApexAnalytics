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

st.set_page_config(
    page_title="Apex Analytics · F1",
    layout="wide",
    page_icon="assets/media/ApexAnalytics logo icono.png",
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
    with open("assets/apex_logo_letras.png", "rb") as _f:
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
        "Eventos de la semana",
        "Grandes Premios y sesiones de la semana en curso en el calendario FIA.",
    ),
    "prediction": (
        "Prediccion y estrategia",
        "Simulador de paradas en boxes segun circuito, clima y degradacion de neumaticos.",
    ),
    "telemetry": (
        "Historial de carreras",
        "Resultados historicos, comparativas entre pilotos y evolucion temporada a temporada.",
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


def _open_video_background() -> None:
    import base64 as _b64
    with open("assets/media/F1 car fondo.mp4", "rb") as _vf:
        _video_b64 = _b64.b64encode(_vf.read()).decode("ascii")
    _video_src = f"data:video/mp4;base64,{_video_b64}"
    st.markdown(
        f"""
        <div class="overview-wrap">
          <video class="bg-video" autoplay muted loop playsinline preload="auto">
            <source src="{_video_src}" type="video/mp4">
          </video>
          <div class="bg-overlay"></div>
        """,
        unsafe_allow_html=True,
    )


def _close_video_background() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


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


def render_history() -> None:
    _open_video_background()
    render_header(*SECTIONS["telemetry"])
    st.info("Esta vista es un placeholder. Aqui veremos el historial de carreras con datos cargados.")
    st.markdown("### Siguientes pasos")
    st.markdown("- Cargar resultados historicos de temporadas previas.")
    st.markdown("- Comparar pilotos y companeros de equipo a lo largo del ano.")
    st.markdown("- Visualizar degradation y stint de neumaticos carrera a carrera.")
    _close_video_background()


def render_prediction() -> None:
    render_header(*SECTIONS["prediction"])
    st.caption("Modelo determinista + Monte Carlo opcional. Fuente: modulo `simulacion.py`.")

    presets = sorted(sim.CIRCUITS.keys())
    col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
    with col_a:
        circuit_name = st.selectbox("Circuito", options=presets, index=presets.index("Silverstone") if "Silverstone" in presets else 0)
    with col_b:
        total_laps = st.number_input("Vueltas totales", min_value=20, max_value=90, value=58, step=1)
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
