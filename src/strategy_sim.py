"""
strategy_sim.py
------------------
Simula estrategias de carrera combinando número de paradas + compuestos +
vueltas de cambio, usando las curvas de degradación calculadas en
degradation.py, y compara el tiempo total estimado contra la estrategia
real del equipo.

Este módulo es el corazón de la "decisión integrada" (timing + compuesto)
que le da al proyecto su narrativa de negocio.
"""

from dataclasses import dataclass
import pandas as pd
from src.degradation import predict_lap_time
from src.regulations import validate_strategy

# Tiempo fijo aproximado que cuesta una parada en pit lane (segundos).
# En un proyecto real esto se calcula por circuito a partir de
# PitInTime/PitOutTime; aquí se deja como parámetro configurable.
DEFAULT_PIT_LOSS_SECONDS = 22.0


@dataclass
class StintPlan:
    compound: str
    laps: int  # número de vueltas que dura este stint


def simulate_strategy(
    stints: list[StintPlan],
    curves: pd.DataFrame,
    pit_loss_seconds: float = DEFAULT_PIT_LOSS_SECONDS,
) -> dict:
    """
    Calcula el tiempo total estimado de una estrategia dada.

    Parámetros
    ----------
    stints : list[StintPlan]
        Secuencia de stints, ej:
        [StintPlan("MEDIUM", 18), StintPlan("HARD", 32)]
        representa una estrategia de 1 parada.
    curves : pd.DataFrame
        Salida de degradation.compute_degradation_curve
    pit_loss_seconds : float
        Costo fijo de cada parada en boxes.

    Retorna
    -------
    dict con:
        total_time_seconds, n_stops, breakdown (lista de tiempos por stint)
    """
    total_time = 0.0
    breakdown = []

    for i, stint in enumerate(stints):
        stint_time = sum(
            predict_lap_time(stint.compound, lap_age, curves)
            for lap_age in range(stint.laps)
        )
        total_time += stint_time
        breakdown.append({
            "stint_index": i,
            "compound": stint.compound,
            "laps": stint.laps,
            "stint_time_seconds": stint_time,
        })

        # Cada stint después del primero implica que hubo una parada antes
        if i > 0:
            total_time += pit_loss_seconds

    return {
        "total_time_seconds": total_time,
        "n_stops": len(stints) - 1,
        "breakdown": breakdown,
    }


def compare_strategies(
    scenarios: dict[str, list[StintPlan]],
    curves: pd.DataFrame,
    pit_loss_seconds: float = DEFAULT_PIT_LOSS_SECONDS,
    gp: str = "",
) -> pd.DataFrame:
    """
    Corre simulate_strategy para varios escenarios nombrados y devuelve
    una tabla comparativa ordenada por tiempo total (mejor primero).

    Cada escenario se valida contra el reglamento de la FIA (ver
    src/regulations.py). El ranking por tiempo se calcula SOLO entre
    estrategias legales; las estrategias ilegales se muestran igual
    (con su tiempo simulado) pero no pueden ser "la recomendación",
    porque en la realidad no estarían permitidas.

    Parámetros
    ----------
    gp : str
        Nombre del Gran Premio, usado para aplicar reglas especiales de
        circuito (ej. Mónaco). Déjalo vacío para aplicar solo la regla
        general de dos compuestos.

    Ejemplo
    -------
    scenarios = {
        "1 parada (M-H)": [StintPlan("MEDIUM", 20), StintPlan("HARD", 32)],
        "2 paradas (S-M-S)": [StintPlan("SOFT", 15), StintPlan("MEDIUM", 20),
                                StintPlan("SOFT", 17)],
    }
    """
    rows = []
    for name, stints in scenarios.items():
        result = simulate_strategy(stints, curves, pit_loss_seconds)
        validation = validate_strategy(stints, gp=gp)
        rows.append({
            "strategy": name,
            "n_stops": result["n_stops"],
            "total_time_seconds": result["total_time_seconds"],
            "is_legal": validation.is_legal,
            "violations": "; ".join(validation.violations) if validation.violations else "",
        })

    df = pd.DataFrame(rows)

    # Delta se calcula respecto a la mejor estrategia LEGAL, no la más
    # rápida en el papel si esa resulta ser ilegal
    legal_df = df[df["is_legal"]]
    best_legal_time = legal_df["total_time_seconds"].min() if not legal_df.empty else df["total_time_seconds"].min()
    df["delta_vs_best_legal_seconds"] = df["total_time_seconds"] - best_legal_time

    df = df.sort_values(["is_legal", "total_time_seconds"], ascending=[False, True]).reset_index(drop=True)
    return df


def extract_real_strategy(clean_laps: pd.DataFrame, driver: str) -> list[StintPlan]:
    """
    Reconstruye la estrategia real que usó un piloto a partir de los datos
    de laps limpios, agrupando por Stint y tomando el compuesto y la
    cantidad de vueltas de cada uno. Útil para comparar "real vs. óptimo".
    """
    df = clean_laps[clean_laps["Driver"] == driver].dropna(subset=["Stint", "Compound"])
    stints = []
    for stint_num, group in df.groupby("Stint"):
        compound = group["Compound"].mode().iloc[0]
        laps = int(group["LapNumber"].max() - group["LapNumber"].min() + 1)
        stints.append(StintPlan(compound=compound, laps=laps))
    return stints
