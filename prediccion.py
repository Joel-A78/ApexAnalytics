"""Modelo de prediccion de posiciones finales en Formula 1.

Estrategia de validacion temporal:
  - Entrenamiento: temporada 2024
  - Evaluacion:    temporada 2025

Features:
  - grid: posicion de salida (predictor mas fuerte)
  - driver_form: posicion media historica del piloto (rolling, causales)
  - constructor_form: posicion media historica del constructor (rolling)
  - circuit_avg: posicion media del piloto en ese circuito (rolling)

Target:
  - position: posicion final en carrera

Modelo: Ridge regression (interpretable, rapido). Se reporta tambien
un baseline trivial ("predecir la posicion de salida") para comparar.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

JOLPICA = "https://api.jolpi.ca/ergast/f1"


def fetch_season_results(year: int) -> list[dict[str, Any]]:
    """Descarga todos los resultados de carrera de una temporada (con paginacion)."""
    limit = 100
    offset = 0
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()

    while True:
        url = f"{JOLPICA}/{year}/results.json?limit={limit}&offset={offset}"
        req = urllib.request.Request(url, headers={"User-Agent": "apex-analytics/1.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
        mrd = payload.get("MRData", {})
        races = mrd.get("RaceTable", {}).get("Races", []) or []
        if not races:
            break

        for race in races:
            round_no = _to_int(race.get("round")) or 0
            circuit = race.get("Circuit", {}).get("circuitId", "")
            date = race.get("date", "")
            for res in race.get("Results", []) or []:
                drv = res.get("Driver", {})
                con = res.get("Constructor", {})
                position = _to_int(res.get("position"))
                if position is None:
                    continue
                key = (year, round_no, drv.get("driverId", ""))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "season": year,
                        "round": round_no,
                        "circuit": circuit,
                        "date": date,
                        "driver_id": drv.get("driverId", ""),
                        "driver_name": f"{drv.get('givenName', '')} {drv.get('familyName', '')}".strip(),
                        "constructor_id": con.get("constructorId", ""),
                        "constructor_name": con.get("name", ""),
                        "grid": _to_int(res.get("grid")),
                        "position": position,
                        "points": _to_float(res.get("points")),
                        "status": res.get("status", ""),
                        "laps": _to_int(res.get("laps")),
                    }
                )

        total = _to_int(mrd.get("total")) or 0
        offset += limit
        if offset >= total:
            break

    return rows


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_feature_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Construye features causales (solo informacion previa a cada carrera)."""
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values(["season", "round", "driver_id"]).reset_index(drop=True)

    driver_history: dict[str, list[int]] = {}
    constructor_history: dict[str, list[int]] = {}

    driver_form: list[float] = []
    constructor_form: list[float] = []
    recent_form: list[float] = []

    for row in df.itertuples(index=False):
        drv = row.driver_id
        con = row.constructor_id

        driver_form.append(_mean(driver_history.get(drv, [])))
        constructor_form.append(_mean(constructor_history.get(con, [])))
        recent_form.append(_mean(driver_history.get(drv, [])[-3:]))

        driver_history.setdefault(drv, []).append(row.position)
        constructor_history.setdefault(con, []).append(row.position)

    df["driver_form"] = driver_form
    df["constructor_form"] = constructor_form
    df["recent_form"] = recent_form
    df["grid"] = df["grid"].fillna(20)
    return df


def _mean(values: list[int]) -> float:
    if not values:
        return np.nan
    return float(sum(values)) / len(values)


FEATURES = ["grid", "driver_form", "constructor_form", "recent_form"]


@dataclass
class ModelReport:
    model: Ridge
    feature_cols: list[str]
    train_rows: int
    eval_rows: int
    mae: float
    rmse: float
    baseline_mae: float
    baseline_rmse: float
    accuracy_pm1: float
    accuracy_pm3: float
    baseline_acc_pm3: float
    podium_hit_rate: float
    baseline_podium_hit_rate: float
    rank_correlation: float
    feature_importance: dict[str, float] = field(default_factory=dict)
    eval_frame: pd.DataFrame = field(default_factory=pd.DataFrame)


def train_and_evaluate(
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
) -> ModelReport:
    train_df = build_feature_frame(train_rows)
    eval_df = build_feature_frame(eval_rows)

    if train_df.empty or eval_df.empty:
        raise ValueError("Datos insuficientes para entrenar/evaluar.")

    for col in ("driver_form", "constructor_form", "recent_form"):
        fill = train_df[col].mean()
        if pd.isna(fill):
            fill = 10.0
        train_df[col] = train_df[col].fillna(fill)
        eval_df[col] = eval_df[col].fillna(fill)

    x_train = train_df[FEATURES].to_numpy(dtype=float)
    y_train = train_df["position"].to_numpy(dtype=float)
    x_eval = eval_df[FEATURES].to_numpy(dtype=float)
    y_eval = eval_df["position"].to_numpy(dtype=float)

    model = Ridge(alpha=1.0)
    model.fit(x_train, y_train)
    preds = model.predict(x_eval)

    baseline_preds = eval_df["grid"].to_numpy(dtype=float)

    mae = float(mean_absolute_error(y_eval, preds))
    rmse = float(np.sqrt(mean_squared_error(y_eval, preds)))
    baseline_mae = float(mean_absolute_error(y_eval, baseline_preds))
    baseline_rmse = float(np.sqrt(mean_squared_error(y_eval, baseline_preds)))

    accuracy_pm1 = float(np.mean(np.abs(preds - y_eval) <= 1) * 100)
    accuracy_pm3 = float(np.mean(np.abs(preds - y_eval) <= 3) * 100)
    baseline_acc_pm3 = float(np.mean(np.abs(baseline_preds - y_eval) <= 3) * 100)

    eval_out = eval_df[["round", "circuit", "driver_name", "constructor_name", "grid", "position"]].copy()
    eval_out["predicted"] = preds
    eval_out["abs_error"] = np.abs(preds - y_eval)

    podium_hits, baseline_podium_hits, total_slots = _podium_hit_rate(eval_out)
    rank_correlation = _spearman(preds, y_eval)

    importance = {
        name: float(abs(coef))
        for name, coef in zip(FEATURES, model.coef_)
    }
    total = sum(importance.values()) or 1.0
    importance = {k: v / total for k, v in importance.items()}

    return ModelReport(
        model=model,
        feature_cols=FEATURES,
        train_rows=len(train_df),
        eval_rows=len(eval_df),
        mae=mae,
        rmse=rmse,
        baseline_mae=baseline_mae,
        baseline_rmse=baseline_rmse,
        accuracy_pm1=accuracy_pm1,
        accuracy_pm3=accuracy_pm3,
        baseline_acc_pm3=baseline_acc_pm3,
        podium_hit_rate=(podium_hits / total_slots * 100) if total_slots else 0.0,
        baseline_podium_hit_rate=(baseline_podium_hits / total_slots * 100) if total_slots else 0.0,
        rank_correlation=rank_correlation,
        feature_importance=importance,
        eval_frame=eval_out,
    )


def _podium_hit_rate(eval_out: pd.DataFrame) -> tuple[int, int, int]:
    """Cuenta cuantos podios reales coinciden con los 3 mejores predichos (y del baseline)."""
    hits = 0
    baseline_hits = 0
    slots = 0
    for _, group in eval_out.groupby("round"):
        actual_top3 = set(group.nsmallest(3, "position")["driver_name"])
        pred_top3 = set(group.nsmallest(3, "predicted")["driver_name"])
        grid_top3 = set(group.nsmallest(3, "grid")["driver_name"])
        hits += len(actual_top3 & pred_top3)
        baseline_hits += len(actual_top3 & grid_top3)
        slots += 3
    return hits, baseline_hits, slots


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Correlacion de Spearman sin dependencia de scipy."""
    try:
        ra = pd.Series(a).rank().to_numpy(dtype=float)
        rb = pd.Series(b).rank().to_numpy(dtype=float)
        if ra.std() == 0 or rb.std() == 0:
            return 0.0
        return float(np.corrcoef(ra, rb)[0, 1])
    except Exception:  # noqa: BLE001
        return 0.0


def predict_from_grid(model: Ridge, grid_position: int, forms: dict[str, float] | None = None) -> float:
    forms = forms or {}
    x = np.array([[
        float(grid_position),
        float(forms.get("driver_form", 10.0)),
        float(forms.get("constructor_form", 10.0)),
        float(forms.get("recent_form", 10.0)),
    ]])
    return float(model.predict(x)[0])


def accuracy_by_season_flag(report: ModelReport) -> float:
    return report.accuracy_pm3
