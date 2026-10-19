"""Auditoria de calidad de datos de Apex Analytics.

Ejecuta comprobaciones de duplicados, faltantes, formatos/rangos y valores
extremos sobre las fuentes reales. NO modifica datos: solo reporta.

Uso:
    python scripts/audit_calidad.py
"""

from __future__ import annotations

import json
import statistics
import sys
import urllib.request
from collections import Counter
from pathlib import Path

import pandas as pd

# Permitir importar los modulos de la raiz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import historial  # noqa: E402
import prediccion  # noqa: E402
import simulacion  # noqa: E402

JOLPICA = "https://api.jolpi.ca/ergast/f1"


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "apex-audit/1.0"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def _section(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def _robust_outliers(series: pd.Series, k: float = 3.0) -> list:
    s = series.dropna()
    if len(s) < 10:
        return []
    med = statistics.median(s)
    mad = statistics.median([abs(x - med) for x in s]) or 1e-9
    return [x for x in s if abs(x - med) / (1.4826 * mad) > k]


def run_audit() -> dict:
    report: dict = {}

    _section("0. VOLUMEN")
    r24 = prediccion.fetch_season_results(2024)
    r25 = prediccion.fetch_season_results(2025)
    cal26 = _get(f"{JOLPICA}/2026.json")["MRData"]["RaceTable"]["Races"]
    df = pd.DataFrame(r24 + r25)
    report["volumen"] = {"resultados_2024": len(r24), "resultados_2025": len(r25), "calendario_2026": len(cal26)}
    print(report["volumen"])

    _section("1. DUPLICADOS")
    key = ["season", "round", "driver_id"]
    dup_results = int(df.duplicated(subset=key).sum())
    keys = list(simulacion.CIRCUITS)
    cnames = [c.name for c in simulacion.CIRCUITS.values()]
    dup_circuits = len(keys) - len(set(keys))
    dup_cnames = [k for k, v in Counter(cnames).items() if v > 1]
    comps = list(simulacion.COMPOUNDS)
    dup_compounds = len(comps) - len(set(comps))
    report["duplicados"] = {
        "resultados": dup_results,
        "circuitos_clave": dup_circuits,
        "circuitos_nombre": dup_cnames,
        "compuestos": dup_compounds,
    }
    print(report["duplicados"])

    ses = historial.fetch_sessions(2024)
    sample = next((s for s in ses if s.get("round") == 1), ses[0])
    sdf = pd.DataFrame(historial.fetch_stints(sample))
    ldf = pd.DataFrame(historial.fetch_laps(sample))
    report["muestra"] = {
        "session_key": sample["session_key"],
        "source": sample["source"],
        "stints": len(sdf),
        "stints_duplicados": int(sdf.duplicated(subset=["driver_key", "stint_number"]).sum()) if len(sdf) else 0,
        "vueltas": len(ldf),
        "vueltas_duplicadas": int(ldf.duplicated(subset=["driver_key", "lap_number"]).sum()) if len(ldf) else 0,
    }
    print(report["muestra"])

    _section("2. FALTANTES")
    faltantes = {}
    for col in ("position", "grid", "points", "laps", "status", "driver_id", "constructor_id", "circuit", "date"):
        faltantes[f"resultados.{col}"] = int(df[col].isna().sum())
    if len(sdf):
        faltantes["stints.compound_UNKNOWN"] = int((sdf["compound"] == "UNKNOWN").sum())
        faltantes["stints.tyre_age_nulos"] = int(sdf["tyre_age_at_start"].isna().sum())
        faltantes["stints.lap_start_nulos"] = int(sdf["lap_start"].isna().sum())
    if len(ldf):
        faltantes["vueltas.lap_duration_nulos"] = int(ldf["lap_duration"].isna().sum())
        faltantes["vueltas.lap_number_nulos"] = int(ldf["lap_number"].isna().sum())
    report["faltantes"] = faltantes
    print(faltantes)

    _section("3. FORMATOS Y RANGOS")
    bad_dates = int((~df["date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)).sum())
    bad_ids = int((~df["driver_id"].astype(str).str.match(r"^[a-z_]+$", na=False)).sum())
    rangos = {
        "fechas_invalidas": bad_dates,
        "driver_id_invalidos": bad_ids,
        "position_fuera": int((~((df["position"] >= 1) & (df["position"] <= 30))).sum()),
        "grid_fuera": int((~((df["grid"] >= 0) & (df["grid"] <= 30))).sum()),
        "points_fuera": int((~((df["points"] >= 0) & (df["points"] <= 30))).sum()),
        "laps_fuera": int((~((df["laps"] >= 0) & (df["laps"] <= 90))).sum()),
    }
    report["formatos_rangos"] = rangos
    print(rangos)

    _section("4. VALORES EXTREMOS")
    extremos = {
        "position": sorted(set(_robust_outliers(df["position"]))),
        "lap_duration_min": None,
        "lap_duration_max": None,
        "lap_duration_mediana": None,
        "vueltas_lentas_no_marcadas": 0,
    }
    if len(ldf):
        dur = ldf["lap_duration"].dropna()
        extremos.update(
            lap_duration_min=round(float(dur.min()), 3),
            lap_duration_max=round(float(dur.max()), 3),
            lap_duration_mediana=round(float(dur.median()), 3),
            vueltas_lentas_no_marcadas=int(((dur > dur.median() * 1.4) & (~ldf["is_pit_out_lap"])).sum()),
        )
    report["extremos"] = extremos
    print(extremos)

    _section("5. COHERENCIA ENTRE FUENTES")
    sj = {
        "source": "jolpica",
        "session_key": "jolpica-2024-1",
        "round": 1,
        "circuit_short_name": "Bahrain",
        "country_name": "Bahrain",
        "date_start": "2024-03-02",
    }
    jst = pd.DataFrame(historial.fetch_stints(sj))
    jlp = pd.DataFrame(historial.fetch_laps(sj))
    report["respaldo"] = {
        "stints": len(jst),
        "compound_UNKNOWN_pct": round(float((jst["compound"] == "UNKNOWN").mean() * 100), 1) if len(jst) else 0,
        "tyre_age_nulos_pct": round(float(jst["tyre_age_at_start"].isna().mean() * 100), 1) if len(jst) else 0,
        "vueltas": len(jlp),
        "out_laps": int(jlp["is_pit_out_lap"].sum()) if len(jlp) else 0,
    }
    print(report["respaldo"])

    return report


if __name__ == "__main__":
    run_audit()
