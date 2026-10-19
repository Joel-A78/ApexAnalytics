# Descripción de gráficos y filtros — Apex Analytics · F1

Pregunta que responde cada visualización, variables que utiliza, motivo de
selección y efecto de los filtros sobre los componentes del dashboard.

---

## Redacción base

> El dashboard se organizó en **cuatro secciones** —Raceweek, Temporada,
> Simulacion e Historial— cada una con un propósito de decisión: contextualizar
> la semana, explorar el campeonato, elegir una estrategia y comparar el
> rendimiento histórico. Se seleccionaron **KPIs de contexto, estrategia y
> modelo** (eventos de la semana, cuenta regresiva, tiempo de estrategia, número
> de paradas, MAE y acierto de podio) por su relación con el objetivo de
> **anticipar resultados y decisiones de carrera**. Se utilizó un **timeline de
> stints** para responder cuándo y cuánto duró cada tramo de carrera, y una
> **dispersión de ritmo** para comparar consistencia entre pilotos. Los filtros
> de **sector**, **pilotos** y **temporada/carrera** permiten acotar la consulta
> sin perder el contexto de la carrera.

---

## 1. Timeline de stints por piloto

| Aspecto | Detalle |
|---|---|
| **Pregunta** | ¿Cuándo paró cada piloto y cómo se repartió su carrera en stints? |
| **Variables** | `driver_key` (eje Y), `lap_start` (base de la barra), `lap_end` (longitud), `stint_number`, `compound`, `laps_completed` |
| **Tipo** | Barras horizontales apiladas por posición (tipo Gantt) |
| **Motivo de selección** | La posición horizontal representa **tiempo de carrera** y la longitud, **duración del stint**. Es la forma más directa de comparar la *forma* de la estrategia entre pilotos y de detectar paradas tempranas o tardías. |

## 2. Dispersión de ritmo por stint (*avg vs. best*)

| Aspecto | Detalle |
|---|---|
| **Pregunta** | ¿Qué piloto o compuesto tuvo mejor ritmo medio y cuán cerca estuvo su mejor vuelta del promedio? |
| **Variables** | `avg_lap_s` (eje X), `best_lap_s` (eje Y), `laps_completed` (tamaño del marcador), `compound` o piloto (color) |
| **Tipo** | Diagrama de dispersión con burbujas |
| **Motivo de selección** | Revela el **trade-off entre ritmo medio y pico de rendimiento**: un punto abajo y a la izquierda es mejor. El tamaño añade la **fiabilidad de la muestra** (más vueltas = más confiable). |

## 3. Tiempo por vuelta · Top 3 estrategias

| Aspecto | Detalle |
|---|---|
| **Pregunta** | ¿Cómo evoluciona el ritmo vuelta a vuelta en cada estrategia y dónde caen las paradas? |
| **Variables** | `vuelta` (eje X), `tiempo de vuelta` (eje Y), `compound` (color), `pit_laps` (líneas verticales) |
| **Tipo** | Dispersión de puntos por vuelta con líneas de referencia |
| **Motivo de selección** | Muestra la **degradación** y el **efecto del paso por boxes** en el mismo eje temporal. Las líneas verticales hacen visible el punto de quiebre de cada plan. |

## 4. Distribución del error absoluto del modelo

| Aspecto | Detalle |
|---|---|
| **Pregunta** | ¿El modelo comete errores pequeños y consistentes o tiene una cola de errores grandes? |
| **Variables** | `abs_error` (eje X), frecuencia de carreras (eje Y), `MAE` como línea de referencia |
| **Tipo** | Histograma |
| **Motivo de selección** | El promedio (MAE) oculta la forma del error. El histograma permite ver si hay **pocos errores catastróficos** que justifiquen revisar el modelo. |

## 5. Peso de cada variable del modelo

| Aspecto | Detalle |
|---|---|
| **Pregunta** | ¿Qué factores explican la predicción de posición? |
| **Variables** | `feature_importance` normalizada (eje X), nombre de la variable (eje Y) |
| **Tipo** | Barras horizontales |
| **Motivo de selección** | Comunica **interpretabilidad**: el usuario ve que la posición de salida domina y que la forma del equipo aporta el resto. Las barras horizontales ordenan magnitudes con etiquetas largas. |

## 6. Mapa del circuito con sectores y curvas

| Aspecto | Detalle |
|---|---|
| **Pregunta** | ¿Cómo es la geometría del circuito y dónde están los sectores y las curvas? |
| **Variables** | `pts` (trazado), `curvature` y `corner_idx` (curvas), `SECTOR_COLORS` (sectores) |
| **Tipo** | SVG con trazado coloreado por sector |
| **Motivo de selección** | El color por sector sigue la **convención de la F1**, así que no requiere aprendizaje. La numeración de curvas añade detalle sin saturar. |

---

## Filtros y componentes afectados

| Filtro | Opciones | Componentes que afecta | Consulta que habilita |
|---|---|---|---|
| **Filtrar sectores** | Todos · Solo S1 · Solo S2 · Solo S3 · combinaciones | Mapa del circuito: atenuación de sectores, marcadores S1/S2/S3 y leyenda | «Muéstrame solo el sector donde se gana tiempo» |
| **Pilotos a comparar** | Multiselección de 1 a 6 pilotos | Timeline de stints, dispersión de ritmo y tabla de detalle | «Compara solo a estos pilotos» |
| **Temporada y carrera** | 2024/2025 y ronda del calendario | Encabezado de sesión, pilotos disponibles, stints, vueltas, gráficos y tabla | «Analiza esta carrera concreta» |

**Filtros complementarios**

| Filtro | Efecto |
|---|---|
| **Mostrar curvas** (interruptor) | Activa o desactiva la numeración de curvas y su entrada en la leyenda |
| **Modo de comparación** | Cambia la estructura de Historial: una sesión (comparar pilotos) o dos sesiones (Train 2024 vs. Eval 2025) |

**Principio de proximidad:** cada filtro vive junto al componente que modifica, de
modo que el usuario percibe el efecto de su acción sin cambiar de pantalla.

---

## Criterio de claridad (fuente de diseño)

> Un dashboard es *"una presentación visual de la información más importante
> necesaria para lograr uno o más objetivos, consolidada y organizada en una sola
> pantalla para que la información pueda monitorearse de un solo vistazo."*

— **Stephen Few**, *Information Dashboard Design: The Effective Visual
Communication of Data* (O'Reilly, 2006).

Ese criterio se aplica así:

1. **Consolidación:** los KPIs críticos se agrupan en una fila al inicio de cada sección.
2. **Organización:** cada sección responde a una pregunta distinta y no mezcla contextos.
3. **Vistazo único:** la estrategia recomendada se muestra en un banner con su margen y desviación, sin obligar a leer la tabla.

Como apoyo, el orden de lectura sigue el mantra de **Ben Shneiderman**
(*The Eyes Have It*, 1996): *"panorama primero, luego zoom y filtrado, después
detalle bajo demanda"* — KPIs → filtros → gráficos → tabla de detalle.
