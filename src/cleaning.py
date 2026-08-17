"""
cleaning.py
------------
Limpia el dataframe crudo de vueltas antes de calcular degradación.

Reglas aplicadas (documentadas para el README/metodología):
1. Se excluyen vueltas sin LapTime (in/out laps sin tiempo registrado,
   vueltas de formación, etc.)
2. Se excluyen vueltas bajo Safety Car / Virtual Safety Car / bandera roja,
   porque distorsionan el ritmo real (TrackStatus != '1' en FastF1 indica
   condición distinta a "verde").
3. Se excluyen la primera vuelta de cada stint (out-lap) porque el piloto
   no está en ritmo de carrera todavía (salida de pits).
4. Se excluyen vueltas con LapTime anormalmente altas (outliers, ej. tráfico
   o incidente) usando un umbral relativo a la vuelta más rápida del stint.
"""

import pandas as pd


def clean_laps(laps: pd.DataFrame, outlier_threshold: float = 1.15) -> pd.DataFrame:
    """
    Aplica las reglas de limpieza descritas arriba.

    Parámetros
    ----------
    laps : pd.DataFrame
        Dataframe crudo proveniente de data_loader.load_race_laps
    outlier_threshold : float
        Multiplicador sobre la vuelta más rápida del stint; vueltas más
        lentas que este umbral se consideran outliers (tráfico, incidente).

    Retorna
    -------
    pd.DataFrame
        Dataframe limpio, con LapTimeSeconds como columna numérica lista
        para análisis.
    """
    df = laps.copy()

    # 1. Quitar vueltas sin tiempo registrado
    df = df.dropna(subset=["LapTime"])

    # Convertir Timedelta -> segundos (float), más fácil de graficar/modelar
    df["LapTimeSeconds"] = df["LapTime"].dt.total_seconds()

    # 2. Quitar vueltas bajo condiciones no verdes (SC/VSC/bandera roja)
    if "TrackStatus" in df.columns:
        df = df[df["TrackStatus"].astype(str).str.contains("1", na=False) &
                 ~df["TrackStatus"].astype(str).str.contains("[^1]", regex=True, na=False)]

    # 3. Quitar out-laps: primera vuelta de cada stint por piloto
    df = df.sort_values(["Driver", "Stint", "LapNumber"])
    df["IsOutLap"] = df.groupby(["Driver", "Stint"])["LapNumber"].transform("min") == df["LapNumber"]
    df = df[~df["IsOutLap"]]

    # 4. Quitar outliers relativos al mejor tiempo del stint
    stint_best = df.groupby(["Driver", "Stint"])["LapTimeSeconds"].transform("min")
    df = df[df["LapTimeSeconds"] <= stint_best * outlier_threshold]

    return df.drop(columns=["IsOutLap"])


def flag_missing_context(df: pd.DataFrame) -> pd.DataFrame:
    """
    Marca filas con datos de contexto incompletos (compuesto o edad de
    neumático faltante) para excluirlas del cálculo de degradación,
    sin perder la fila del dataframe general.
    """
    df = df.copy()
    df["HasTyreContext"] = df["Compound"].notna() & df["TyreLife"].notna()
    return df
