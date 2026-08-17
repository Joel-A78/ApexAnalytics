"""Dashboard industrial para un proyecto de portafolio automotriz en Tijuana."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.categories import CATEGORIES, get_category

st.set_page_config(
    page_title="Plant Performance Intelligence",
    layout="wide",
    page_icon="🏭",
)


def build_sample_plant_data() -> pd.DataFrame:
    dates = pd.date_range("2026-01-05", "2026-08-10", freq="D")
    rows: list[dict] = []

    lines = ["L1", "L2", "L3"]
    shifts = ["A", "B"]
    machines = {
        "L1": ["M-101", "M-102", "M-103"],
        "L2": ["M-201", "M-202"],
        "L3": ["M-301", "M-302", "M-303"],
    }
    defect_types = ["doble toque", "desalineación", "rayón superficial", "fuga", "soldadura"]
    customers = ["Ford", "GM", "Tesla", "Stellantis", "BMW"]
    suppliers = ["Prov-01", "Prov-02", "Prov-03", "Prov-04"]

    for date in dates:
        for line in lines:
            for shift in shifts:
                plan = 220 + (hash(f"{date:%Y%m%d}-{line}-{shift}") % 180)
                produced = int(plan * (0.92 + np.random.default_rng(len(rows) + 11).random() * 0.12))
                good_units = int(produced * (0.95 + np.random.default_rng(len(rows) + 7).random() * 0.04))
                scrap_units = max(produced - good_units, 0)
                downtime_min = int(18 + np.random.default_rng(len(rows) + 13).random() * 90)
                oee = round(0.66 + np.random.default_rng(len(rows) + 21).random() * 0.24, 3)
                defect_type = defect_types[(len(rows) + hash(f"{date:%Y%m%d}-{line}") % len(defect_types)) % len(defect_types)]
                customer = customers[(len(rows) + hash(f"{date:%Y%m%d}-{line}-{shift}") % len(customers)) % len(customers)]
                supplier = suppliers[(len(rows) + hash(f"{date:%Y%m%d}-{line}") % len(suppliers)) % len(suppliers)]
                otif = round(0.88 + np.random.default_rng(len(rows) + 17).random() * 0.12, 3)
                stock = int(120 + np.random.default_rng(len(rows) + 19).random() * 250)
                rows.append(
                    {
                        "date": date,
                        "line": line,
                        "shift": shift,
                        "machine": machines[line][(len(rows) + hash(f"{date:%Y%m%d}-{line}-{shift}") % len(machines[line])) % len(machines[line])],
                        "product": f"SKU-{(len(rows) % 9) + 101}",
                        "plan": plan,
                        "produced": produced,
                        "good_units": good_units,
                        "scrap_units": scrap_units,
                        "downtime_min": downtime_min,
                        "oee": oee,
                        "defect_type": defect_type,
                        "customer": customer,
                        "supplier": supplier,
                        "otif": otif,
                        "stock": stock,
                    }
                )

    return pd.DataFrame(rows)


def compute_kpis(df: pd.DataFrame) -> dict[str, float]:
    total_plan = df["plan"].sum()
    total_produced = df["produced"].sum()
    total_good = df["good_units"].sum()
    total_scrap = df["scrap_units"].sum()
    avg_oee = df["oee"].mean()
    avg_otif = df["otif"].mean()
    scrap_pct = (total_scrap / total_produced) * 100 if total_produced else 0
    compliance = (total_good / total_plan) * 100 if total_plan else 0
    critical_stock = (df["stock"] < 150).mean() * 100

    return {
        "oee": round(avg_oee * 100, 2),
        "scrap_pct": round(scrap_pct, 2),
        "compliance": round(compliance, 2),
        "otif": round(avg_otif * 100, 2),
        "critical_stock": round(critical_stock, 2),
    }


sample_data = build_sample_plant_data()

with st.sidebar:
    st.markdown("### 🏭 Área funcional")
    available_categories = [c for c in CATEGORIES if c.status == "available"]
    selected_id = st.radio(
        "Selecciona una vista",
        options=[c.id for c in available_categories],
        format_func=lambda cid: f"{get_category(cid).icon} {get_category(cid).label}",
        label_visibility="collapsed",
    )

active = get_category(selected_id)

st.markdown(
    f"""
    <div style="padding: 1rem 1rem 1rem 0; border-bottom: 1px solid #2a3f5f; margin-bottom: 1rem;">
        <div style="font-size:2.2rem;">{active.icon}</div>
        <h1 style="margin: 0.2rem 0;">{active.label}</h1>
        <p style="margin: 0; color: #cfe2ff;">{active.description}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

summary_tab, quality_tab, inventory_tab, maintenance_tab = st.tabs(
    [
        "📊 Resumen general",
        "✅ Calidad y scrap",
        "📦 Inventario y OTIF",
        "🛠️ Mantenimiento y paros",
    ]
)

kpis = compute_kpis(sample_data)

with summary_tab:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("OEE promedio", f"{kpis['oee']}%")
    k2.metric("Scrap total", f"{kpis['scrap_pct']}%")
    k3.metric("Cumplimiento de plan", f"{kpis['compliance']}%")
    k4.metric("OTIF", f"{kpis['otif']}%")

    line_summary = (
        sample_data.groupby("line", as_index=False)
        .agg(
            plan=("plan", "sum"),
            produced=("produced", "sum"),
            good_units=("good_units", "sum"),
            downtime_min=("downtime_min", "sum"),
            oee=("oee", "mean"),
        )
    )
    line_summary["scrap_pct"] = (1 - line_summary["good_units"] / line_summary["produced"]) * 100

    fig_production = px.line(
        line_summary,
        x="line",
        y=["plan", "produced"],
        title="Producción real vs. plan por línea",
        markers=True,
    )
    st.plotly_chart(fig_production, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig_oee = px.bar(
            line_summary,
            x="line",
            y="oee",
            color="oee",
            title="OEE por línea",
            labels={"line": "Línea", "oee": "OEE promedio"},
        )
        st.plotly_chart(fig_oee, use_container_width=True)

    with col_b:
        fig_scrap = px.bar(
            line_summary,
            x="line",
            y="scrap_pct",
            color="scrap_pct",
            title="Scrap por línea",
            labels={"line": "Línea", "scrap_pct": "% de scrap"},
        )
        st.plotly_chart(fig_scrap, use_container_width=True)

with quality_tab:
    defect_summary = (
        sample_data.groupby("defect_type", as_index=False)["scrap_units"]
        .sum()
        .sort_values("scrap_units", ascending=False)
    )

    st.subheader("Pareto de defectos")
    fig_defects = px.bar(
        defect_summary,
        x="defect_type",
        y="scrap_units",
        color="defect_type",
        title="Unidades rechazadas por tipo de defecto",
        labels={"defect_type": "Tipo de defecto", "scrap_units": "Unidades rechazadas"},
    )
    st.plotly_chart(fig_defects, use_container_width=True)

    quality_by_line = (
        sample_data.groupby("line", as_index=False)
        .agg(scrap_pct=("scrap_units", lambda s: (s.sum() / sample_data.loc[sample_data["line"].eq(s.name), "produced"].sum()) * 100 if False else 0),)
    )
    quality_by_line = (
        sample_data.groupby("line", as_index=False)
        .agg(
            produced=("produced", "sum"),
            scrap_units=("scrap_units", "sum"),
        )
    )
    quality_by_line["scrap_pct"] = (quality_by_line["scrap_units"] / quality_by_line["produced"]) * 100

    fig_quality = px.bar(
        quality_by_line,
        x="line",
        y="scrap_pct",
        color="scrap_pct",
        title="Scrap por línea",
        labels={"line": "Línea", "scrap_pct": "% scrap"},
    )
    st.plotly_chart(fig_quality, use_container_width=True)

with inventory_tab:
    inventory = sample_data.groupby("supplier", as_index=False).agg(
        stock=("stock", "mean"),
        otif=("otif", "mean"),
    )

    st.subheader("Riesgo de inventario y proveedores")
    fig_stock = px.bar(
        inventory,
        x="supplier",
        y="stock",
        color="stock",
        title="Stock promedio por proveedor",
    )
    st.plotly_chart(fig_stock, use_container_width=True)

    fig_otif = px.bar(
        inventory,
        x="supplier",
        y="otif",
        color="otif",
        title="Cumplimiento OTIF por proveedor",
    )
    st.plotly_chart(fig_otif, use_container_width=True)

    stock_risk = sample_data.copy()
    stock_risk["risk_flag"] = np.where(stock_risk["stock"] < 150, "Alto", "Normal")
    risk_summary = stock_risk.groupby("risk_flag", as_index=False).size()
    st.dataframe(risk_summary, hide_index=True)

with maintenance_tab:
    downtime = (
        sample_data.groupby("machine", as_index=False)
        .agg(downtime_min=("downtime_min", "sum"), oee=("oee", "mean"))
        .sort_values("downtime_min", ascending=False)
    )

    st.subheader("Paros y mantenibilidad")
    fig_downtime = px.bar(
        downtime,
        x="machine",
        y="downtime_min",
        color="downtime_min",
        title="Minutos perdidos por máquina",
    )
    st.plotly_chart(fig_downtime, use_container_width=True)

    fig_oee_machine = px.bar(
        downtime,
        x="machine",
        y="oee",
        color="oee",
        title="OEE por máquina",
    )
    st.plotly_chart(fig_oee_machine, use_container_width=True)

    st.caption(
        "Contexto del portafolio: este dashboard simula una planta proveedora automotriz exportando a EUA, "
        "con foco en eficiencia, calidad, inventario y mantenimiento."
    )
