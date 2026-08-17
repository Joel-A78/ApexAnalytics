"""
degradation.py
----------------
Calcula curvas de degradación de neumáticos: cuánto tiempo se pierde por
vuelta a medida que el neumático envejece, por compuesto.

Enfoque: regresión lineal simple (LapTimeSeconds ~ TyreLife) por compuesto,
lo cual da una pendiente interpretable en segundos/vuelta de degradación.
Es intencionalmente simple para que el resultado sea explicable en una
entrevista ("el compuesto medium pierde X décimas por vuelta").
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def compute_degradation_curve(clean_laps: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa por compuesto y ajusta una regresión LapTimeSeconds ~ TyreLife.

    Retorna
    -------
    pd.DataFrame con columnas:
        Compound, slope_sec_per_lap, intercept_sec, n_laps, r_squared
    """
    df = clean_laps.dropna(subset=["Compound", "TyreLife", "LapTimeSeconds"])

    rows = []
    for compound, group in df.groupby("Compound"):
        if len(group) < 5:
            # Muy pocos datos para una regresión confiable
            continue
        X = group[["TyreLife"]].values
        y = group["LapTimeSeconds"].values
        model = LinearRegression().fit(X, y)
        r_squared = model.score(X, y)

        rows.append({
            "Compound": compound,
            "slope_sec_per_lap": model.coef_[0],
            "intercept_sec": model.intercept_,
            "n_laps": len(group),
            "r_squared": r_squared,
        })

    return pd.DataFrame(rows).sort_values("slope_sec_per_lap")


def predict_lap_time(compound: str, tyre_life: int, curves: pd.DataFrame) -> float:
    """
    Predice el tiempo de vuelta esperado dado un compuesto y una edad de
    neumático, usando la curva de degradación ya calculada.
    """
    row = curves[curves["Compound"] == compound]
    if row.empty:
        raise ValueError(f"No hay curva de degradación calculada para el compuesto '{compound}'")
    slope = row["slope_sec_per_lap"].values[0]
    intercept = row["intercept_sec"].values[0]
    return intercept + slope * tyre_life


def detect_cliff(clean_laps: pd.DataFrame, compound: str, window: int = 3, jump_threshold: float = 0.5) -> int | None:
    """
    Detecta el punto de "cliff": la vuelta de vida del neumático donde el
    ritmo promedio cae abruptamente (más que jump_threshold segundos
    respecto a la media móvil anterior). Devuelve la edad de neumático
    donde ocurre, o None si no se detecta un cliff claro.
    """
    df = clean_laps[clean_laps["Compound"] == compound].dropna(subset=["TyreLife", "LapTimeSeconds"])
    if df.empty:
        return None

    avg_by_life = df.groupby("TyreLife")["LapTimeSeconds"].mean().sort_index()
    rolling = avg_by_life.rolling(window=window, min_periods=1).mean()

    diffs = avg_by_life - rolling.shift(1)
    cliff_points = diffs[diffs > jump_threshold]

    if cliff_points.empty:
        return None
    return int(cliff_points.index[0])
