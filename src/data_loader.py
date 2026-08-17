"""
data_loader.py
----------------
Carga sesiones de F1 usando FastF1 y devuelve datos de vueltas (laps)
listos para limpieza. Usa el sistema de cache de FastF1 para no volver
a descargar la misma sesión dos veces.

Uso típico:
    from src.data_loader import load_race_laps

    laps = load_race_laps(year=2024, gp="Spain", session="R")
"""

from pathlib import Path
import fastf1
import pandas as pd

# Carpeta donde FastF1 guarda su cache local (archivos .ff1pkl)
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "fastf1_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))


def load_race_laps(year: int, gp: str, session: str = "R") -> pd.DataFrame:
    """
    Descarga (o lee de cache) una sesión y devuelve el dataframe de vueltas.

    Parámetros
    ----------
    year : int
        Temporada, ej. 2024
    gp : str
        Nombre del Gran Premio, ej. "Spain", "Monaco", "Bahrain"
    session : str
        Tipo de sesión: "R" (carrera), "Q" (clasificación), "FP1"/"FP2"/"FP3"

    Retorna
    -------
    pd.DataFrame
        Dataframe crudo de vueltas de FastF1 (laps.laps), con columnas como
        Driver, LapNumber, LapTime, Compound, TyreLife, Stint, TrackStatus,
        PitInTime, PitOutTime, Position, etc.
    """
    race = fastf1.get_session(year, gp, session)
    race.load(laps=True, telemetry=False, weather=True, messages=False)

    laps = race.laps.copy()

    # Anexamos temperatura de pista/aire promedio de la sesión como contexto
    # (FastF1 trae weather data en resolución de tiempo, aquí solo tomamos
    # un resumen simple para no complicar el pipeline inicial)
    try:
        weather = race.weather_data
        laps["AirTemp"] = weather["AirTemp"].mean()
        laps["TrackTemp"] = weather["TrackTemp"].mean()
    except Exception:
        laps["AirTemp"] = None
        laps["TrackTemp"] = None

    laps["EventName"] = race.event["EventName"]
    laps["Year"] = year

    return laps


def load_multiple_races(races: list[dict]) -> pd.DataFrame:
    """
    Carga y concatena varias carreras.

    Parámetros
    ----------
    races : list[dict]
        Ej: [{"year": 2024, "gp": "Spain"}, {"year": 2024, "gp": "Bahrain"}]

    Retorna
    -------
    pd.DataFrame
        Todas las vueltas concatenadas, con columna EventName/Year para
        distinguir el origen de cada fila.
    """
    frames = []
    for race in races:
        df = load_race_laps(year=race["year"], gp=race["gp"], session=race.get("session", "R"))
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def save_processed(df: pd.DataFrame, name: str) -> Path:
    """Guarda un dataframe procesado como Parquet en data/processed/."""
    out_dir = Path(__file__).resolve().parents[1] / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def get_season_calendar(year: int) -> pd.DataFrame:
    """
    Devuelve el calendario de la temporada (nombre de GP, país, fechas de
    sesión) usando el schedule oficial que trae FastF1.
    """
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    cols = [c for c in [
        "RoundNumber", "EventName", "Country", "Location",
        "EventDate", "EventFormat", "Session5Date",
    ] if c in schedule.columns]
    return schedule[cols].sort_values("RoundNumber")


if __name__ == "__main__":
    # Prueba rápida: carga una carrera y muestra un resumen
    laps = load_race_laps(year=2024, gp="Spain", session="R")
    print(laps[["Driver", "LapNumber", "LapTime", "Compound", "TyreLife", "Stint"]].head(10))
    save_processed(laps, "spain_2024_raw")
