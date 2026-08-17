"""
regulations.py (endurance)
-----------------------------
Reglas de resistencia (WEC / Le Mans / IMSA) relevantes para validar un
plan de stints por piloto. A diferencia de F1 (donde la restricción es
sobre compuestos de neumático), en resistencia la restricción central es
sobre TIEMPO DE MANEJO por piloto, para prevenir fatiga.

Reglas modeladas (temporada 2025, Le Mans/WEC):

1. Ningún piloto puede manejar más de 4 horas continuas dentro de
   cualquier ventana de 6 horas.
2. Ningún piloto puede manejar más de 14 horas en total durante la carrera.
3. En LMP2 y LMGT3, los pilotos de categoría Bronze o Silver deben manejar
   un mínimo de 6 horas en total (esta regla NO aplica a pilotos Gold o
   Platinum).
4. Cada auto debe tener entre 2 y 3 pilotos en su alineación.

Fuente: reglamento especial 24 Hrs de Le Mans 2025 (ACO/FIA WEC).

Nota: el reglamento real es más detallado (ventanas de descanso mínimo,
reglas de temperatura ambiente que reducen el tiempo continuo permitido,
categorización exacta de pilotos). Este módulo cubre las reglas de mayor
impacto en la planeación de estrategia, documentadas como alcance en el
README.
"""

from dataclasses import dataclass, field

MAX_CONTINUOUS_HOURS = 4.0
MAX_CONTINUOUS_WINDOW_HOURS = 6.0
MAX_TOTAL_HOURS_PER_DRIVER = 14.0
MIN_TOTAL_HOURS_BRONZE_SILVER = 6.0
MIN_DRIVERS_PER_CAR = 2
MAX_DRIVERS_PER_CAR = 3

DRIVER_GRADES_REQUIRING_MINIMUM = {"BRONZE", "SILVER"}


@dataclass
class DriverStint:
    driver: str
    grade: str  # "PLATINUM" | "GOLD" | "SILVER" | "BRONZE"
    stint_hours: list[float] = field(default_factory=list)  # duración de cada stint que maneja


@dataclass
class ValidationResult:
    is_legal: bool
    violations: list[str] = field(default_factory=list)

    def __bool__(self):
        return self.is_legal


def validate_lineup(drivers: list[DriverStint], category: str = "LMGT3") -> ValidationResult:
    """
    Valida una alineación de pilotos (cada uno con su lista de stints)
    contra las reglas de tiempo de manejo de resistencia.

    Parámetros
    ----------
    drivers : list[DriverStint]
        Un DriverStint por piloto del auto, con sus stints planeados.
    category : str
        "LMGT3" o "LMP2" activan la regla de mínimo de 6h para pilotos
        Bronze/Silver; otras categorías (Hypercar) no la requieren.
    """
    violations = []

    if not (MIN_DRIVERS_PER_CAR <= len(drivers) <= MAX_DRIVERS_PER_CAR):
        violations.append(
            f"Se requieren entre {MIN_DRIVERS_PER_CAR} y {MAX_DRIVERS_PER_CAR} "
            f"pilotos por auto (esta alineación tiene {len(drivers)})."
        )

    for d in drivers:
        total_hours = sum(d.stint_hours)

        # Regla: ningún stint individual mayor a 4h
        for i, stint_h in enumerate(d.stint_hours):
            if stint_h > MAX_CONTINUOUS_HOURS:
                violations.append(
                    f"{d.driver}: el stint #{i+1} dura {stint_h:.1f}h, supera el "
                    f"máximo de {MAX_CONTINUOUS_HOURS}h continuas."
                )

        # Regla: máximo total por piloto
        if total_hours > MAX_TOTAL_HOURS_PER_DRIVER:
            violations.append(
                f"{d.driver}: acumula {total_hours:.1f}h de manejo, supera el "
                f"máximo total de {MAX_TOTAL_HOURS_PER_DRIVER}h."
            )

        # Regla: mínimo para Bronze/Silver en LMP2/LMGT3
        if category.upper() in {"LMP2", "LMGT3"} and d.grade.upper() in DRIVER_GRADES_REQUIRING_MINIMUM:
            if total_hours < MIN_TOTAL_HOURS_BRONZE_SILVER:
                violations.append(
                    f"{d.driver} ({d.grade}): acumula {total_hours:.1f}h, por debajo "
                    f"del mínimo de {MIN_TOTAL_HOURS_BRONZE_SILVER}h exigido a "
                    f"pilotos Bronze/Silver en {category}."
                )

    return ValidationResult(is_legal=(len(violations) == 0), violations=violations)
