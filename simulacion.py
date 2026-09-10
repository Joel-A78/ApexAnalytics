"""Simulador de estrategias de carrera para Formula 1.

Modela la degradacion lineal de los neumaticos por compuesto y circuito,
evalua estrategias de 1, 2 y 3 paradas y recomienda la de menor tiempo
total proyectado. Pensado para uso rapido desde el dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

COMPOUND_ORDER: tuple[str, ...] = ("S", "M", "H", "I", "W")


@dataclass(frozen=True)
class Compound:
    name: str
    short: str
    base_pace: float
    deg_rate: float
    cliff_lap: int
    cliff_drop: float
    min_stint: int


@dataclass(frozen=True)
class Circuit:
    name: str
    base_lap_time: float
    pit_loss: float
    deg_factor: float
    overtaking_difficulty: float
    safety_car_prob: float
    notes: str


@dataclass(frozen=True)
class Strategy:
    name: str
    stints: tuple[tuple[str, int], ...]

    @property
    def stops(self) -> int:
        return max(len(self.stints) - 1, 0)

    @property
    def compounds(self) -> str:
        return "-".join(c for c, _ in self.stints)


@dataclass
class StrategyResult:
    strategy: Strategy
    total_time: float
    pit_laps: list[int]
    per_lap: list[tuple[int, float, str]]
    sample_std: float = 0.0


COMPOUNDS: dict[str, Compound] = {
    "S": Compound("Soft", "S", 0.0, 0.045, 14, 0.6, 8),
    "M": Compound("Medium", "M", 0.4, 0.030, 22, 0.5, 14),
    "H": Compound("Hard", "H", 0.8, 0.022, 35, 0.4, 22),
    "I": Compound("Intermediate", "I", 2.0, 0.025, 20, 0.5, 6),
    "W": Compound("Wet", "W", 4.0, 0.030, 25, 0.5, 5),
}


CIRCUITS: dict[str, Circuit] = {
    "Bahrain": Circuit("Bahrain", 91.0, 22.0, 1.10, 0.40, 0.18, "Alta abrasion, castigo rear."),
    "Jeddah": Circuit("Jeddah", 89.0, 21.0, 1.00, 0.55, 0.10, "Calles rapidas, muros cerca."),
    "Melbourne": Circuit("Melbourne", 80.0, 20.0, 0.95, 0.55, 0.12, "Mixto, degradacion media."),
    "Suzuka": Circuit("Suzuka", 91.0, 21.5, 1.00, 0.55, 0.10, "Escenario clasico, ritmo alto."),
    "Shanghai": Circuit("Shanghai", 95.0, 20.0, 1.00, 0.55, 0.10, "Rectas largas, frenadas fuertes."),
    "Miami": Circuit("Miami", 91.0, 20.0, 0.95, 0.55, 0.12, "Asfalto nuevo, baja abrasion."),
    "Imola": Circuit("Imola", 75.0, 22.0, 1.05, 0.80, 0.10, "Estrecho, dificil adelantar."),
    "Monaco": Circuit("Monaco", 73.0, 21.5, 0.85, 0.95, 0.08, "Pista mas estrecha, undercut manda."),
    "Montreal": Circuit("Montreal", 72.0, 19.5, 1.00, 0.60, 0.18, "Frenadas fuertes, alta SC."),
    "Catalunya": Circuit("Barcelona", 77.0, 20.0, 1.08, 0.70, 0.10, "Alto deg termico."),
    "Red Bull Ring": Circuit("Red Bull Ring", 67.0, 19.0, 0.95, 0.50, 0.10, "Pista corta, 1 parada comun."),
    "Silverstone": Circuit("Silverstone", 88.0, 19.0, 1.05, 0.60, 0.08, "Curvas de alta velocidad."),
    "Hungaroring": Circuit("Hungaroring", 77.0, 20.0, 1.05, 0.85, 0.10, "Monaco-like, estrategia manda."),
    "Spa-Francorchamps": Circuit("Spa-Francorchamps", 106.0, 21.0, 1.00, 0.50, 0.18, "Cambios de clima, eccpp."),
    "Zandvoort": Circuit("Zandvoort", 72.0, 21.0, 1.00, 0.80, 0.10, "Bancadas inclinadas."),
    "Monza": Circuit("Monza", 81.0, 20.0, 0.95, 0.70, 0.10, "Templo de la velocidad, 1 parada."),
    "Baku": Circuit("Baku", 103.0, 22.0, 0.95, 0.60, 0.20, "Alta SC, muros cerca."),
    "Marina Bay": Circuit("Marina Bay", 95.0, 23.0, 1.05, 0.85, 0.25, "Nocturna, alta SC."),
    "COTA": Circuit("COTA", 95.0, 20.0, 1.05, 0.65, 0.10, "Mix completo, variedad de estrategias."),
    "Mexico City": Circuit("Mexico City", 78.0, 21.0, 1.00, 0.60, 0.12, "Altitud, motor manda."),
    "Interlagos": Circuit("Interlagos", 71.0, 22.0, 1.05, 0.50, 0.22, "Variable, SC probable."),
    "Las Vegas": Circuit("Las Vegas", 84.0, 21.0, 0.95, 0.60, 0.10, "Rectas larguisimas."),
    "Abu Dhabi": Circuit("Abu Dhabi", 87.0, 21.0, 1.00, 0.60, 0.08, "Cierre de temporada."),
}


def lap_time(compound: Compound, circuit: Circuit, lap_in_stint: int) -> float:
    linear_deg = compound.deg_rate * circuit.deg_factor * max(lap_in_stint - 1, 0)
    cliff = compound.cliff_drop if lap_in_stint >= compound.cliff_lap else 0.0
    return circuit.base_lap_time + compound.base_pace + linear_deg + cliff


def simulate(strategy: Strategy, circuit: Circuit, total_laps: int) -> StrategyResult:
    laps: list[tuple[int, float, str]] = []
    pit_laps: list[int] = []
    total = 0.0
    lap_in_stint = 0
    stint_idx = 0
    current = COMPOUNDS[strategy.stints[0][0]]
    stint_remaining = strategy.stints[0][1]

    for lap in range(1, total_laps + 1):
        lap_in_stint += 1
        stint_remaining -= 1
        t_lap = lap_time(current, circuit, lap_in_stint)
        is_pit_lap = stint_remaining == 0 and stint_idx < len(strategy.stints) - 1
        if is_pit_lap:
            total += t_lap + circuit.pit_loss
            pit_laps.append(lap)
            stint_idx += 1
            current = COMPOUNDS[strategy.stints[stint_idx][0]]
            lap_in_stint = 0
            stint_remaining = strategy.stints[stint_idx][1]
        else:
            total += t_lap
        laps.append((lap, t_lap, current.short))

    return StrategyResult(
        strategy=strategy,
        total_time=total,
        pit_laps=pit_laps,
        per_lap=laps,
    )


def generate_strategies(total_laps: int, include_wet: bool = False) -> list[Strategy]:
    strats: list[Strategy] = []

    s_first = ("S", "M", "H")
    s_second = ("S", "M", "H")

    for c1 in s_first:
        for c2 in s_second:
            if c1 == c2:
                continue
            l1 = max(COMPOUNDS[c1].min_stint, total_laps // 2 - 3)
            l2 = total_laps - l1
            if l2 < COMPOUNDS[c2].min_stint or l1 < COMPOUNDS[c1].min_stint:
                continue
            if l2 < 10:
                continue
            strats.append(Strategy(f"1-stop {c1}-{c2}", ((c1, l1), (c2, l2))))

    for c1 in ("S", "M"):
        for c2 in ("M", "H"):
            for c3 in ("S", "M", "H"):
                l1 = max(COMPOUNDS[c1].min_stint, total_laps // 3 - 2)
                l3 = max(COMPOUNDS[c3].min_stint, total_laps // 3 - 2)
                l2 = total_laps - l1 - l3
                if any(l < mn for l, mn in zip((l1, l2, l3), (COMPOUNDS[c].min_stint for c in (c1, c2, c3)))):
                    continue
                if l2 < 10:
                    continue
                strats.append(Strategy(f"2-stop {c1}-{c2}-{c3}", ((c1, l1), (c2, l2), (c3, l3))))

    if include_wet:
        for c1 in ("I", "W"):
            for c2 in ("I", "W"):
                if c1 == c2:
                    continue
                l1 = max(COMPOUNDS[c1].min_stint, total_laps // 2 - 3)
                l2 = total_laps - l1
                if l2 < COMPOUNDS[c2].min_stint or l1 < COMPOUNDS[c1].min_stint:
                    continue
                strats.append(Strategy(f"1-stop {c1}-{c2}", ((c1, l1), (c2, l2))))

    return strats


def _simulate_mc(strategy: Strategy, circuit: Circuit, total_laps: int, noise_sigma: float, rng) -> float:
    total = 0.0
    lap_in_stint = 0
    stint_idx = 0
    current = COMPOUNDS[strategy.stints[0][0]]
    stint_remaining = strategy.stints[0][1]
    for _ in range(1, total_laps + 1):
        lap_in_stint += 1
        stint_remaining -= 1
        noise = rng.gauss(0, noise_sigma) if noise_sigma > 0 else 0.0
        t_lap = lap_time(current, circuit, lap_in_stint) + noise
        is_pit_lap = stint_remaining == 0 and stint_idx < len(strategy.stints) - 1
        if is_pit_lap:
            total += t_lap + circuit.pit_loss
            stint_idx += 1
            current = COMPOUNDS[strategy.stints[stint_idx][0]]
            lap_in_stint = 0
            stint_remaining = strategy.stints[stint_idx][1]
        else:
            total += t_lap
    return total


def recommend(
    circuit: Circuit,
    total_laps: int,
    monte_carlo: int = 1,
    noise_sigma: float = 0.0,
    seed: int | None = None,
) -> list[StrategyResult]:
    import random as _random
    import statistics as _stats

    rng = _random.Random(seed) if seed is not None else _random.Random()
    strategies = generate_strategies(total_laps)
    results: list[StrategyResult] = []
    for strat in strategies:
        if monte_carlo <= 1 or noise_sigma <= 0:
            results.append(simulate(strat, circuit, total_laps))
            continue
        totals = [_simulate_mc(strat, circuit, total_laps, noise_sigma, rng) for _ in range(int(monte_carlo))]
        deterministic = simulate(strat, circuit, total_laps)
        results.append(
            StrategyResult(
                strategy=strat,
                total_time=_stats.fmean(totals),
                pit_laps=deterministic.pit_laps,
                per_lap=deterministic.per_lap,
                sample_std=_stats.pstdev(totals) if len(totals) > 1 else 0.0,
            )
        )
    results.sort(key=lambda r: r.total_time)
    return results


def format_time(seconds: float) -> str:
    if seconds < 0:
        return "-"
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}.{int((seconds - int(seconds)) * 100):02d}"


def recommend_for_circuit(circuit_name: str, total_laps: int, starting: str = "M", monte_carlo: int = 1, noise_sigma: float = 0.0) -> list[StrategyResult]:
    circuit = CIRCUITS[circuit_name]
    all_results = recommend(circuit, total_laps, monte_carlo=monte_carlo, noise_sigma=noise_sigma)
    return all_results
