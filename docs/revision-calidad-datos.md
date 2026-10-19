# Revisión de calidad de datos — Apex Analytics · F1

Auditoría de **duplicados, faltantes, formatos/rangos y valores extremos** sobre
las fuentes reales del proyecto. La revisión es de **solo lectura**: no modifica
la base original. Cada decisión queda registrada con su justificación.

**Reproducible:** `python scripts/audit_calidad.py` (no escribe nada; imprime el informe).

**Periodo auditado:** resultados 2024 (entrenamiento) y 2025 (evaluación),
calendario 2026 y sesión Bahrain 2024 como muestra de telemetría.

---

## 1. Tabla de revisión

| Revisión | Hallazgo real | Decisión y justificación |
|---|---|---|
| **Duplicados** | **0 duplicados** en 958 resultados (479 de 2024 + 479 de 2025) según `(temporada, ronda, piloto)`. **0** en stints `(piloto, stint)` sobre 63 registros, **0** en vueltas `(piloto, vuelta)` sobre 1 129 registros, **0** en sesiones (24 `session_key` únicos). Catálogos: 25 circuitos con 25 claves únicas, 0 nombres repetidos, 5 compuestos únicos. | **No eliminar nada.** La combinación `(temporada, ronda, piloto)` es la granularidad correcta de un resultado: un piloto aparece una vez por carrera. Se conserva el 100 % de los registros. *Hallazgo histórico resuelto:* el catálogo tenía **3 entradas duplicadas de `Madrid`** (secuela de parcheos); se eliminaron en el commit `61f1c11`. |
| **Faltantes** | **0 nulos** en las 9 variables críticas de resultados (`position`, `grid`, `points`, `laps`, `status`, `driver_id`, `constructor_id`, `circuit`, `date`). **0 nulos** en `lap_start`, `lap_end` y `tyre_age_at_start` de los 63 stints. **0 nulos** en `lap_duration` y `lap_number` de las 1 129 vueltas. **Excepción estructural:** con la fuente de respaldo (Jolpica) el `compound` es `UNKNOWN` en el **100 %** de los stints y `tyre_age_at_start` es nulo en el **100 %**. | **No imputar.** Los faltantes de Jolpica no son errores: la API simplemente no publica compuesto ni edad del neumático. Imputar un compuesto inventaría información y sesgaría el análisis. Se marca `UNKNOWN`, se conserva la fila y la interfaz **declara la fuente activa**. En OpenF1 (fuente primaria) no hay faltantes. |
| **Formatos / rangos** | **0 fechas inválidas** (todas cumplen `YYYY-MM-DD`). **0 identificadores fuera** del patrón `[a-z_]+`. **0 valores fuera de rango**: `position` 1–20, `grid` 0–20, `points` 0–26, `laps` 0–78. | **No corregir.** Los rangos observados coinciden con la lógica del dominio. En particular, `grid = 0` es **válido**: significa salida desde el pit lane, no un dato faltante. No se aplicó ninguna normalización porque no había inconsistencia que corregir. |
| **Valores extremos** | `lap_duration`: mínimo **92.608 s**, mediana **97.056 s**, máximo **170.266 s** (1.75× la mediana). Las 5 vueltas más lentas son casi todas `is_pit_out_lap = True`. **1 vuelta lenta no marcada**: piloto 2, vuelta 10, **161.860 s**. `position` sin extremos. El método robusto marcó `points` 6–16 como extremos. | **No eliminar.** El máximo de 170.266 s está marcado como salida de boxes (evento real). La vuelta de 161.860 s **no es un error de datos**: corresponde a una vuelta bajo neutralización/incidente, un evento deportivo legítimo; eliminarla falsearía la carrera. **Limitación declarada:** el promedio por stint excluye solo las vueltas de boxes, por lo que una vuelta de safety car lo eleva. Los `points` son una variable **discreta**: el método de outliers robusto no aplica y sus marcas son **falsos positivos** (no se actúa). |

---

## 2. Evidencia por dimensión

### 2.1 Duplicados

| Conjunto | Granularidad evaluada | Registros | Duplicados |
|---|---|---|---|
| Resultados | `temporada + ronda + piloto` | 958 | **0** |
| Stints | `piloto + nº de stint` | 63 | **0** |
| Vueltas | `piloto + nº de vuelta` | 1 129 | **0** |
| Sesiones | `session_key` | 24 | **0** |
| Catálogo de circuitos | `clave` | 25 | **0** |
| Catálogo de circuitos | `nombre` | 25 | **0** |
| Catálogo de compuestos | `código` | 5 | **0** |

**Criterio aplicado:** se conserva un único registro solo cuando se confirma que
dos filas describen **el mismo evento** en la misma granularidad. No se elimina
nada que represente eventos distintos (p. ej., dos pilotos con la misma posición
en carreras diferentes, o dos stints del mismo piloto).

### 2.2 Faltantes

| Variable | Fuente primaria (OpenF1) | Respaldo (Jolpica) | Tratamiento |
|---|---|---|---|
| `position`, `grid`, `points`, `laps`, `status` | 0 % | 0 % | Sin acción |
| `lap_duration`, `lap_number` | 0 % | 0 % | Sin acción |
| `lap_start`, `lap_end` | 0 % | 0 % | Sin acción |
| `compound` | 0 % | **100 % `UNKNOWN`** | Marcar, no imputar |
| `tyre_age_at_start` | 0 % | **100 % nulo** | Mantener nulo |
| `Circuit.Location.lat/long` | n/d | 0 % | Degradar a "—" si faltara |

**Criterio aplicado:** un faltante se sustituye solo si existe una justificación
de dominio. Aquí no la hay para el compuesto: inventarlo alteraría la comparación
de stints. La ausencia se **hace visible** en la interfaz en lugar de ocultarse.

### 2.3 Formatos y rangos

| Comprobación | Resultado |
|---|---|
| Fechas `YYYY-MM-DD` | 0 inválidas |
| `driver_id` → `[a-z_]+` | 0 inválidos |
| `position` ∈ [1, 30] | 0 fuera · rango real 1–20 |
| `grid` ∈ [0, 30] | 0 fuera · rango real 0–20 |
| `points` ∈ [0, 30] | 0 fuera · rango real 0–26 |
| `laps` ∈ [0, 90] | 0 fuera · rango real 0–78 |

**Criterio aplicado:** se corrige un formato solo si es inconsistente con la
fuente. Todos los valores se contrastaron contra el rango esperado del dominio;
ninguno requirió modificación.

### 2.4 Valores extremos

| Métrica | Valor | Clasificación |
|---|---|---|
| Vuelta más rápida | 92.608 s | Legítima |
| Mediana | 97.056 s | Referencia |
| Vuelta más lenta | 170.266 s | **Legítima** (salida de boxes) |
| Vuelta lenta no marcada | 161.860 s (piloto 2, vuelta 10) | **Legítima** (neutralización/incidente) |
| Vueltas > 1.4× mediana | 2 (1 marcada, 1 no) | Ambas reales |
| `position` extremos | ninguno | — |
| `points` "extremos" 6–16 | — | **Falso positivo** (variable discreta) |

**Criterio aplicado:** un valor extremo se modifica **solo si se demuestra que es
un error** contrastándolo con la fuente. Ninguno lo fue. Se documenta la
limitación de que el promedio por stint es sensible a vueltas de safety car.

---

## 3. Tablas de hechos y catálogos

El proyecto no usa un almacén físico: las "tablas" existen como `DataFrame` en
memoria y diccionarios de catálogo. El modelo lógico es en **estrella**.

### 3.1 Tablas de hechos

| Tabla de hechos | Granularidad | Medidas | Atributos degenerados | Fuente |
|---|---|---|---|---|
| **`fact_resultados`** | temporada × ronda × piloto | `position`, `grid`, `points`, `laps` | `status` | Jolpica `/results` |
| **`fact_vueltas`** | sesión × piloto × vuelta | `lap_duration`, `is_pit_out_lap` | — | OpenF1 `/laps` · Jolpica `/laps` |
| **`fact_stints`** | sesión × piloto × stint | `lap_start`, `lap_end`, `laps_completed`, `avg_lap_s`, `best_lap_s` | `compound`, `tyre_age_at_start` | OpenF1 `/stints` · Jolpica (derivado) |
| **`fact_clima`** | circuito × día | `temperature_2m`, `humidity`, `wind_speed`, `precipitation`, `weather_code` | `is_day` | Open-Meteo (bajo demanda) |

### 3.2 Catálogos (dimensiones)

| Catálogo | Clave | Atributos |
|---|---|---|
| **`dim_circuito`** | `circuit_key` | `name`, `base_lap_time`, `pit_loss`, `deg_factor`, `typical_laps` |
| **`dim_piloto`** | `driver_key` | `full_name` |
| **`dim_equipo`** | `team_name` | color de equipo |
| **`dim_compuesto`** | `compound` | `name`, `base_pace`, `deg_rate`, `cliff_lap`, `cliff_drop`, `min_stint` |
| **`dim_sesion`** | `session_key` | `round`, `circuit_short_name`, `country_name`, `date_start`, `source` |
| **`dim_temporada`** | `season` + `round` | `raceName`, `date` |

### 3.3 Relaciones

```
dim_temporada 1 ── N fact_resultados N ── 1 dim_piloto
                                     N ── 1 dim_equipo
                                     N ── 1 dim_circuito

dim_sesion    1 ── N fact_vueltas    N ── 1 dim_piloto
dim_sesion    1 ── N fact_stints     N ── 1 dim_compuesto
dim_circuito  1 ── N fact_clima
```

**Por qué importa:** la granularidad de cada hecho define qué es un duplicado.
En `fact_resultados` la clave es `(season, round, driver_key)`; en `fact_vueltas`
es `(session_key, driver_key, lap_number)`; en `fact_stints` es
`(session_key, driver_key, stint_number)`. Las tres dieron **0 duplicados**.

---

## 4. Bitácora de decisiones

| ID | Fecha | Dimensión | Hallazgo | Decisión | Justificación | Evidencia |
|---|---|---|---|---|---|---|
| DC-01 | 2026-10-18 | Duplicados | 0 duplicados en resultados, stints, vueltas, sesiones y catálogos | Conservar todo | La granularidad es correcta y no hay repetición | `audit_calidad.py` §1 |
| DC-02 | 2026-10-18 | Duplicados | 3 entradas `Madrid` repetidas en el catálogo (histórico) | Eliminar las 3 | Eran claves idénticas; solo la última tenía efecto | Commit `61f1c11` |
| DC-03 | 2026-10-18 | Faltantes | 0 nulos en resultados y telemetría (OpenF1) | Sin acción | No hay nada que tratar | `audit_calidad.py` §2 |
| DC-04 | 2026-10-18 | Faltantes | Jolpica: 100 % `compound` `UNKNOWN` y 100 % `tyre_age` nulo | No imputar; marcar y declarar la fuente | Inventar compuesto sesgaría el análisis | `audit_calidad.py` §5 |
| DC-05 | 2026-10-18 | Formatos | 0 fechas e identificadores inválidos | Sin acción | Todos cumplen el formato esperado | `audit_calidad.py` §3 |
| DC-06 | 2026-10-18 | Rangos | `grid = 0` presente | Conservar | Es salida desde pit lane, valor válido | §3 |
| DC-07 | 2026-10-18 | Extremos | Vuelta de 170.266 s | Conservar | Está marcada como salida de boxes | §4 |
| DC-08 | 2026-10-18 | Extremos | Vuelta de 161.860 s no marcada | Conservar y documentar la limitación | Evento real (neutralización), no error | §4 |
| DC-09 | 2026-10-18 | Extremos | `points` 6–16 marcados como extremos | No actuar | Variable discreta; el método no aplica | §4 |

**Regla transversal:** la base original **nunca se sobrescribe**. La auditoría
solo lee; cualquier corrección se aplica en código (catálogos) y se registra aquí
con su commit.

---

## 5. Reproducibilidad

```bash
python scripts/audit_calidad.py
```

El script:
1. Descarga resultados 2024 y 2025 y el calendario 2026 (Jolpica).
2. Toma una sesión de muestra (Bahrain 2024) para stints y vueltas.
3. Calcula duplicados, faltantes, formatos/rangos y extremos.
4. Fuerza la ruta de respaldo (Jolpica) para medir el faltante estructural.
5. **No escribe ni modifica ningún dato.**

Salida esperada (resumen):

```
resultados 2024: 479 | resultados 2025: 479 | calendario 2026: 23
duplicados: 0 (resultados, stints, vueltas, sesiones, catálogos)
faltantes: 0 en resultados y telemetría OpenF1
formatos/rangos: 0 inválidos
extremos: máx. 170.266 s (pit-out) · 1 vuelta lenta no marcada (real)
respaldo Jolpica: 63 stints, 1129 vueltas, compound UNKNOWN 100 %
```
