"""
regulations.py
-----------------
Reglas del Reglamento Deportivo de la FIA relevantes para validar si una
estrategia simulada sería LEGAL en una carrera real, no solo rápida en
el papel. Esto evita que el simulador recomiende una "estrategia óptima"
que en realidad estaría prohibida.

Reglas modeladas (temporada 2024-2025):

1. Regla general (todos los circuitos, carrera en seco):
   un piloto debe usar al menos DOS compuestos de neumático seco distintos
   durante la carrera. Esta obligación desaparece si en algún momento se
   usaron neumáticos de lluvia (intermedio o full wet), porque entonces
   se asume que las condiciones no fueron completamente secas.

2. Regla especial de Mónaco (desde 2025):
   además de la regla general, se exige un mínimo de TRES juegos de
   neumáticos usados en carrera y un mínimo de DOS paradas obligatorias
   (aplica tanto en seco como en mojado).

Fuente: FIA Sporting Regulations + comunicados oficiales de la FIA/F1
sobre la regla especial de Mónaco 2025.
"""

from dataclasses import dataclass, field

DRY_COMPOUNDS = {"SOFT", "MEDIUM", "HARD"}
WET_COMPOUNDS = {"INTERMEDIATE", "WET"}


@dataclass
class ValidationResult:
    is_legal: bool
    violations: list[str] = field(default_factory=list)

    def __bool__(self):
        return self.is_legal


def validate_strategy(stints: list, gp: str = "") -> ValidationResult:
    """
    Valida una lista de StintPlan contra las reglas de la FIA.

    Parámetros
    ----------
    stints : list[StintPlan]
        Secuencia de stints de la estrategia a validar.
    gp : str
        Nombre del Gran Premio (para detectar la regla especial de Mónaco).

    Retorna
    -------
    ValidationResult
        is_legal=True si cumple todas las reglas aplicables; si no,
        violations contiene la lista de reglas incumplidas en español,
        listas para mostrar en el dashboard.
    """
    violations = []

    compounds_used = {s.compound.upper() for s in stints}
    dry_compounds_used = compounds_used & DRY_COMPOUNDS
    wet_compounds_used = compounds_used & WET_COMPOUNDS
    n_stops = len(stints) - 1
    n_sets = len(stints)

    # Regla 1: dos compuestos secos distintos, salvo que se haya usado mojado
    if not wet_compounds_used and len(dry_compounds_used) < 2:
        violations.append(
            "Regla general FIA: en carrera seca se deben usar al menos dos "
            "compuestos de neumático seco distintos (SOFT/MEDIUM/HARD). "
            f"Esta estrategia solo usa: {', '.join(dry_compounds_used) or 'ninguno detectado'}."
        )

    # Regla 2: caso especial Mónaco (>= 2025)
    if "monaco" in gp.lower() or "mónaco" in gp.lower():
        if n_stops < 2:
            violations.append(
                "Regla especial Mónaco: se exige un mínimo de DOS paradas "
                f"obligatorias (esta estrategia tiene {n_stops})."
            )
        if n_sets < 3:
            violations.append(
                "Regla especial Mónaco: se exige el uso de al menos TRES "
                f"juegos de neumáticos en carrera (esta estrategia usa {n_sets})."
            )
        if not wet_compounds_used and len(dry_compounds_used) < 2:
            # Ya cubierto arriba, pero se deja explícito por claridad normativa
            pass

    return ValidationResult(is_legal=(len(violations) == 0), violations=violations)
