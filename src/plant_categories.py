"""Categorías del dashboard industrial para un portafolio automotriz."""

from dataclasses import dataclass


@dataclass
class PlantCategory:
    id: str
    label: str
    icon: str
    status: str  # "available" | "coming_soon"
    description: str


CATEGORIES: list[PlantCategory] = [
    PlantCategory(
        id="plant_overview",
        label="Planta automotriz",
        icon="🏭",
        status="available",
        description="Resumen operativo de eficiencia, calidad, inventario y entregas.",
    ),
    PlantCategory(
        id="quality",
        label="Calidad y scrap",
        icon="✅",
        status="available",
        description="Análisis de defectos, retrabajo, cumplimiento de especificaciones y riesgo de cliente.",
    ),
    PlantCategory(
        id="inventory",
        label="Inventario y supply chain",
        icon="📦",
        status="available",
        description="Monitoreo de stock, proveedores, riesgo de faltante y OTIF.",
    ),
    PlantCategory(
        id="maintenance",
        label="Mantenimiento y paros",
        icon="⚙",
        status="available",
        description="Disponibilidad, MTBF, MTTR y minutos perdidos por máquina o línea.",
    ),
]


def get_category(category_id: str) -> PlantCategory:
    for c in CATEGORIES:
        if c.id == category_id:
            return c
    raise ValueError(f"Categoría desconocida: {category_id}")
