"""
data_loader.py (endurance)
----------------------------
Carga datos de vuelta de carreras de resistencia (IMSA WeatherTech, WEC —
incluyendo las 24 Hrs de Le Mans—, ELMS, Asian Le Mans, Le Mans Cup) desde
un dataset público construido con DuckDB, alojado en HuggingFace.

IMPORTANTE — nota de transparencia metodológica:
Este dataset es de un tercero (no oficial de la ACO/FIA/IMSA), documentado
públicamente en https://github.com/tobi/imsa_data. El esquema exacto de
columnas puede variar entre series/años. La primera vez que lo uses,
corre `describe_available_tables()` para confirmar los nombres de columna
reales antes de asumir que coinciden con los usados aquí — este loader
asume un esquema razonable basado en la documentación pública del
proyecto, pero no fue verificado contra una conexión en vivo.

Requiere el paquete `duckdb` (incluido en requirements.txt).
"""

import duckdb
import pandas as pd

DATASET_URI = "hf://datasets/tobil/imsa/imsa.duckdb"


def _connect():
    return duckdb.connect(database=":memory:")


def describe_available_tables() -> pd.DataFrame:
    """
    Utilidad de diagnóstico: lista las tablas disponibles en el dataset.
    Corre esto primero si algo falla, para confirmar nombres reales de
    tabla/columna antes de depurar el resto del pipeline.
    """
    con = _connect()
    query = f"SELECT * FROM duckdb_tables() WHERE database_name = 'imsa' OR true"
    try:
        con.execute(f"ATTACH '{DATASET_URI}' AS imsa (READ_ONLY)")
        return con.execute("SHOW ALL TABLES").fetchdf()
    finally:
        con.close()


def load_endurance_laps(series: str, year: int, event: str) -> pd.DataFrame:
    """
    Carga las vueltas de un evento específico de una serie de resistencia.

    Parámetros
    ----------
    series : str
        Ej. "imsa", "wec", "elms", "lemans_cup" (ver events.json del
        dataset para los valores exactos disponibles por temporada).
    year : int
        Temporada, ej. 2024.
    event : str
        Nombre o slug del evento, ej. "24-hours-of-le-mans".

    Retorna
    -------
    pd.DataFrame
        Columnas esperadas (a confirmar con describe_available_tables):
        driver, lap_number, lap_time, class/homologation, manufacturer,
        chassis, session, stint.
    """
    con = _connect()
    try:
        con.execute(f"ATTACH '{DATASET_URI}' AS imsa (READ_ONLY)")
        query = """
            SELECT *
            FROM imsa.laps
            WHERE series = ? AND year = ? AND event = ? AND session = 'race'
        """
        df = con.execute(query, [series, year, event]).fetchdf()
        return df
    finally:
        con.close()


def save_processed(df: pd.DataFrame, name: str):
    """Guarda un dataframe procesado como Parquet en data/processed/."""
    from pathlib import Path
    out_dir = Path(__file__).resolve().parents[2] / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def list_known_events() -> pd.DataFrame:
    """
    Intenta listar los eventos disponibles en el dataset (equivalente a un
    calendario de temporada). Depende de que el dataset exponga una tabla
    tipo 'events' — no verificado contra una conexión en vivo, por lo que
    esta función puede requerir ajuste una vez confirmes el esquema real
    con describe_available_tables().
    """
    con = _connect()
    try:
        con.execute(f"ATTACH '{DATASET_URI}' AS imsa (READ_ONLY)")
        return con.execute("SELECT * FROM imsa.events ORDER BY year DESC").fetchdf()
    except Exception as e:
        raise RuntimeError(
            "No se pudo leer una tabla de eventos con ese nombre. Corre "
            "describe_available_tables() para confirmar el esquema real "
            f"del dataset antes de reintentar. Detalle: {e}"
        )
    finally:
        con.close()


if __name__ == "__main__":
    # Diagnóstico rápido: confirma qué tablas/columnas trae el dataset
    # antes de asumir el esquema en el resto del pipeline.
    print(describe_available_tables())
