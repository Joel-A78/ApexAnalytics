# Diccionario de datos — Apex Analytics · F1

Definición de todas las variables que el proyecto **consume, normaliza o produce**,
organizadas por origen. Cada variable se documenta con: **nombre · descripción ·
tipo / unidad · rango o categorías · tratamiento de valores faltantes**.

**Convenciones**
- *Req.* = constante o campo obligatorio definido en código; no puede faltar.
- *Descarte* = la observación se elimina del cálculo.
- *Imputación* = el valor faltante se reemplaza por un valor por defecto.
- *Degradación* = el valor se muestra como "—" o cadena vacía, sin romper la vista.
- UTC = hora universal · TZ = zona local `America/Tijuana` · s = segundos.

**Proveedores de datos**

| Dominio | Fuente primaria | Respaldo | Módulo |
|---|---|---|---|
| Calendario y resultados | Jolpica/Ergast | — | `app.py`, `prediccion.py` |
| Clima | Open-Meteo | — | `app.py` |
| Estrategia de carrera | Catálogo interno | — | `simulacion.py` |
| Trazado del circuito | Geometría procedural | — | `circuits.py` |
| Historial de stints | OpenF1 | **Jolpica** (`/laps` + `/pitstops`) | `historial.py` |

---

## 1. Calendario y sesiones — Jolpica `GET /f1/{año}.json`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `round` | Número de ronda del campeonato | Entero | 1–24 | Descarte del selector; en calendario queda vacío |
| `raceName` | Nombre oficial del Gran Premio | Texto | Categórico ("Azerbaijan Grand Prix") | Degradación a "Carrera" |
| `date` | Fecha de la carrera | Fecha ISO `YYYY-MM-DD` | Año de la temporada activa | **Descarte**: se excluye de `get_next_race` y del calendario |
| `time` | Hora de salida | Hora ISO `HH:MM:SSZ` (UTC) | 00:00:00–23:59:59 | **Imputación** a 00:00 UTC para ordenar sesiones |
| `Circuit.circuitName` | Nombre del circuito | Texto | Categórico | Degradación a "Circuito" |
| `Circuit.Location.locality` | Ciudad | Texto | Categórico | Degradación a cadena vacía |
| `Circuit.Location.country` | País | Texto | Categórico | Degradación a "—" |
| `Circuit.Location.lat` | Latitud | Decimal (grados) | −90 a 90 | `try/except` → `None` → se omite el clima y se muestra "—" |
| `Circuit.Location.long` | Longitud | Decimal (grados) | −180 a 180 | Igual que `lat` |
| `FirstPractice` | Práctica 1 (`date` + `time`) | Objeto fecha/hora ISO | — | Si falta, la sesión no se lista |
| `SecondPractice` | Práctica 2 | Objeto fecha/hora ISO | — | Igual |
| `ThirdPractice` | Práctica 3 | Objeto fecha/hora ISO | — | Igual |
| `SprintQualifying` | Clasificación sprint | Objeto fecha/hora ISO | — | Igual |
| `Sprint` | Carrera sprint | Objeto fecha/hora ISO | — | Igual |
| `Qualifying` | Clasificación | Objeto fecha/hora ISO | — | Igual |
| `url` | Enlace Wikipedia del GP | URL | — | No se consume en KPIs |

**Derivadas del calendario**

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `weekend_start` | Primer día del fin de semana | Fecha (TZ local) | Año de temporada | `date.min` si no hay sesiones |
| `weekend_end` | Último día del fin de semana | Fecha (TZ local) | Año de temporada | `date.max` si no hay sesiones |
| `days_until` | Días a la próxima carrera | Entero (días) | −400 a 400 (0 = "Hoy") | Se omite el KPI si no hay fecha parseable |
| `next_race` | Próxima carrera vigente | Objeto | Fin de semana en curso o futura | `None` → se oculta la sección de datos geométricos |
| `is_past` | Carrera ya disputada | Booleano | {True, False} | Derivada: `weekend_end < hoy` |

---

## 2. Resultados de carrera — Jolpica `GET /f1/{año}/results.json`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `position` | Posición final en carrera | Entero | 1–20 | **Descarte**: filas sin posición no entran al dataset |
| `positionText` | Posición como texto | Texto | 1–20, "R", "D", "E", "W", "F", "N" | No se consume; solo trazabilidad |
| `points` | Puntos obtenidos | Decimal (puntos) | 0–26 | **Imputación** a `0.0` |
| `grid` | Posición de salida | Entero | 0 (pit lane) a 20 | **Imputación** a 20 |
| `laps` | Vueltas completadas | Entero (vueltas) | 0–78 | Degradación a "—" |
| `status` | Estado final | Texto | "Finished", "+1 Lap", "Accident", "Engine", "Gearbox"… | Cadena vacía; respaldo de `Time.time` |
| `Driver.driverId` | Identificador del piloto | Texto | Categórico (`max_verstappen`) | Cadena vacía; llave de agrupación |
| `Driver.givenName` | Nombre de pila | Texto | Categórico | Concatenado + `strip()` |
| `Driver.familyName` | Apellido | Texto | Categórico | Igual |
| `Driver.code` | Sigla de 3 letras | Texto | 3 letras mayúsculas | No se consume |
| `Driver.nationality` | Nacionalidad | Texto | Categórico | No se consume |
| `Constructor.constructorId` | Identificador del equipo | Texto | Categórico (`red_bull`) | Cadena vacía; llave de agrupación |
| `Constructor.name` | Nombre del equipo | Texto | Categórico | Degradación a "—" |
| `Constructor.nationality` | Nacionalidad del equipo | Texto | Categórico | No se consume |
| `Time.time` | Tiempo total / diferencia del ganador | Texto (`H:MM:SS.mmm` o `+X.XXX`) | — | Respaldo a `status` |
| `FastestLap.AverageSpeed.speed` | Velocidad media de la vuelta rápida | Decimal (km/h) | ~180–260 | Degradación a "—" |
| `cumulative_points` | Puntos acumulados del piloto hasta la ronda | Decimal (puntos) | 0–600 | **Imputación** a 0 por piloto |

---

## 3. Clima actual — Open-Meteo `current=`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `temperature_2m` | Temperatura del aire a 2 m | Decimal (°C) | −20 a 50 | Degradación a "—" |
| `apparent_temperature` | Sensación térmica | Decimal (°C) | −25 a 55 | "—"; bloquea el cálculo de `track_temp` |
| `relative_humidity_2m` | Humedad relativa | Entero (%) | 0–100 | "—" |
| `precipitation` | Precipitación instantánea | Decimal (mm) | 0–50 | "—" |
| `weather_code` | Código WMO del cielo | Entero (categórico) | 0,1,2,3,45,48,51,53,55,61,63,65,71,73,75,80,81,82,95,96,99 | **Imputación** a 0 ("Despejado") |
| `cloud_cover` | Cobertura nubosa | Entero (%) | 0–100 | "—" |
| `pressure_msl` | Presión a nivel del mar | Decimal (hPa) | 950–1050 | "—" |
| `wind_speed_10m` | Velocidad del viento a 10 m | Decimal (km/h) | 0–150 | "—" |
| `wind_direction_10m` | Dirección del viento | Entero (grados) | 0–359 | "—" |
| `wind_gusts_10m` | Rachas de viento | Decimal (km/h) | 0–200 | "—" |
| `is_day` | Indicador día/noche | Booleano 0/1 | {0, 1} | **Imputación** a 1 (día) |

**Derivadas del clima**

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `track_temp` | Temperatura de pista estimada (`apparent_temperature + 9` si es de día) | Decimal (°C) | −25 a 64 | "—" si falta `apparent_temperature` |
| `rain_risk` | Máxima probabilidad de lluvia a 3 días | Entero (%) | 0–100 | **Imputación** a 0 si la lista está vacía |
| `race_class` | Clase de condición de carrera | Texto (CSS) | `wx-outlook-dry` (<30 %), `wx-outlook-mixed` (≥30 %), `wx-outlook-wet` (≥60 %) | Derivada de `rain_risk` |
| `race_note` | Mensaje de condiciones | Texto | 3 mensajes categóricos | Derivada de `rain_risk` |

---

## 4. Clima diario (pronóstico) — Open-Meteo `daily=`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `temperature_2m_max` | Temperatura máxima diaria | Decimal (°C) | −20 a 55 | Si la lista está vacía, no se dibuja el pronóstico |
| `temperature_2m_min` | Temperatura mínima diaria | Decimal (°C) | −30 a 45 | Igual |
| `precipitation_probability_max` | Probabilidad máxima de lluvia del día | Entero (%) | 0–100 | **Imputación** a 0 |
| `weather_code` | Código WMO diario | Entero | Misma escala WMO del grupo 3 | **Imputación** al `weather_code` actual |

---

## 5. Catálogo de circuitos — `simulacion.Circuit`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `name` | Nombre del circuito | Texto | 25 categorías (Bahrain…Abu Dhabi, Madrid, Sepang) | Req. |
| `base_lap_time` | Vuelta base del circuito | Decimal (s) | 67–106 | Req. |
| `pit_loss` | Pérdida de tiempo por paso por boxes | Decimal (s) | 19.0–23.0 | Req. |
| `deg_factor` | Multiplicador de degradación del circuito | Decimal (adimensional) | 0.85–1.10 | Req. |
| `typical_laps` | Vueltas típicas de carrera | Entero (vueltas) | 44–78 | **Imputación** a 58 |

> **Retirados:** `overtaking_difficulty`, `safety_car_prob` y `notes` se eliminaron porque
> ningún cálculo ni vista los consumía (3 campos × 25 circuitos).

---

## 6. Catálogo de compuestos — `simulacion.Compound`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `name` | Nombre del compuesto | Texto | Soft, Medium, Hard, Intermediate, Wet | Req. |
| `short` | Código del compuesto | Texto | S, M, H, I, W | Req. |
| `base_pace` | Delta de ritmo base contra el soft | Decimal (s) | 0.0–4.0 | Req. |
| `deg_rate` | Degradación lineal por vuelta | Decimal (s/vuelta) | 0.022–0.045 | Req. |
| `cliff_lap` | Vuelta del cambio abrupto de rendimiento | Entero (vueltas) | 14–35 | Req. |
| `cliff_drop` | Caída adicional al cruzar el cliff | Decimal (s) | 0.4–0.6 | Req. |
| `min_stint` | Stint mínimo viable | Entero (vueltas) | 5–22 | Req. |

---

## 7. Simulación de estrategia — derivadas de `simulacion.py`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `stints` | Secuencia de (compuesto, vueltas) | Tupla de pares | Compuestos válidos, vueltas ≥ `min_stint` | Req. |
| `stops` | Número de paradas | Entero | 0–2 | Derivada: `len(stints) − 1` |
| `total_time` | Tiempo total proyectado | Decimal (s) | ~4200–7800 | Req. |
| `pit_laps` | Vueltas de paso por boxes | Lista de enteros | 1–90 | Lista vacía si 0 paradas |
| `per_lap` | Serie (vuelta, tiempo, compuesto) | Lista de tuplas | — | Req. |
| `sample_std` | Desviación estándar Monte Carlo | Decimal (s) | 0–30 | **Imputación** a 0.0 si no hay Monte Carlo |
| `monte_carlo` | Número de simulaciones | Entero | 1–500 | **Imputación** a 50 |
| `noise_sigma` | Ruido gaussiano por vuelta | Decimal (s) | 0.00–0.50 | **Imputación** a 0.10 |
| `gap_to_best` | Margen contra la mejor estrategia | Decimal (s) | 0–200 | 0.0 para la óptima |
| `starting_compound` | Compuesto de salida | Texto | S, M, H, I, W | **Imputación** a "M" |
| `rain` | Incluir estrategias de lluvia | Booleano | {True, False} | **Imputación** a `False` |

---

## 8. Modelo normalizado de historial — `historial.py`

Capa que unifica OpenF1 y Jolpica bajo una misma forma. A continuación, las variables
normalizadas que expone a la interfaz.

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `source` | Proveedor de origen de la sesión | Texto (categórico) | `openf1`, `jolpica` | Req. |
| `session_key` | Clave de sesión normalizada | Texto | `openf1`: entero como texto · `jolpica`: `jolpica-{año}-{ronda}` | Req. |
| `round` | Ronda de la carrera | Entero | 1–24 | Req. |
| `meeting_key` | Clave del Gran Premio | Entero | OpenF1: id real · Jolpica: = `round` | Req. |
| `circuit_short_name` | Nombre del circuito | Texto | Categórico | Degradación a cadena vacía |
| `country_name` | País | Texto | Categórico | Cadena vacía |
| `date_start` | Fecha (y hora) de la sesión | Texto ISO | 2023–2026 | Se corta a 10 caracteres; vacío si falta |
| `driver_key` | **Llave de piloto agnóstica** | Texto | OpenF1: dorsal · Jolpica: `driverId` | Req. |
| `full_name` | Nombre completo del piloto | Texto | Categórico | Degradación a `#{driver_key}` |
| `team_name` | Equipo del piloto | Texto | Categórico | Cadena vacía |
| `stint_number` | Ordinal del stint | Entero | 1–7 | `.get()` → `None` |
| `lap_start` | Primera vuelta del stint | Entero (vueltas) | 1–78 | **Descarte** del stint |
| `lap_end` | Última vuelta del stint | Entero (vueltas) | 1–78 | **Descarte** del stint |
| `compound` | Compuesto del neumático | Texto | SOFT, MEDIUM, HARD, INTERMEDIATE, WET, **UNKNOWN** | **Imputación** a "UNKNOWN" |
| `tyre_age_at_start` | Edad del neumático al montar | Entero (vueltas) | 0–40 | `None` cuando la fuente no lo publica (siempre en Jolpica) |
| `lap_number` | Número de vuelta | Entero (vueltas) | 1–78 | **Descarte** de la vuelta |
| `lap_duration` | Duración de la vuelta | Decimal (s) | 60–120 | **Descarte** de la vuelta |
| `is_pit_out_lap` | Vuelta de salida de boxes | Booleano | {True, False} | **Derivada** en Jolpica: la vuelta siguiente a cada parada |

---

## 9. Sesiones — OpenF1 `GET /v1/sessions` y `/v1/meetings`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `session_key` | Identificador único de sesión | Entero | Llave | Req. |
| `session_name` | Tipo de sesión | Texto | Race, Sprint, Qualifying, Practice | Se filtra por "Race"; descarte si falta |
| `meeting_key` | Identificador del Gran Premio | Entero | Llave | Req. |
| `meeting_name` | Nombre del GP (endpoint `/meetings`) | Texto | Categórico | Degradación a `circuit_short_name` |
| `circuit_short_name` | Nombre corto del circuito | Texto | Categórico | Cadena vacía |
| `country_name` | País | Texto | Categórico | Cadena vacía |
| `date_start` | Fecha y hora de inicio | Fecha/hora ISO | 2023–2026 | Se usa `[:10]` |

> **Proyección de payload:** OpenF1 devuelve 14 campos por sesión; la app retiene **6**.

---

## 10. Pilotos — OpenF1 `GET /v1/drivers`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `driver_number` | Dorsal del piloto | Entero | 1–99 | Req. (se convierte en `driver_key`) |
| `full_name` | Nombre completo | Texto | Categórico | Degradación a "#{driver_number}" |
| `team_name` | Equipo | Texto | Categórico | Cadena vacía |

> **Proyección de payload:** OpenF1 devuelve 12 campos por piloto; la app retiene **3**.

---

## 11. Stints — OpenF1 `GET /v1/stints`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `stint_number` | Ordinal del stint | Entero | 1–7 | `.get()` → `None` |
| `driver_number` | Dorsal del piloto | Entero | 1–99 | Req. (llave de cruce con vueltas) |
| `compound` | Compuesto usado | Texto | SOFT, MEDIUM, HARD, INTERMEDIATE, WET | **Imputación** a "UNKNOWN" |
| `lap_start` | Primera vuelta del stint | Entero (vueltas) | 1–78 | **Descarte** del stint |
| `lap_end` | Última vuelta del stint | Entero (vueltas) | 1–78 | **Descarte** del stint |
| `tyre_age_at_start` | Edad del neumático al montar | Entero (vueltas) | 0–40 | `.get()` → `None` |

> **Proyección de payload:** OpenF1 devuelve 9 campos por stint; la app retiene **6**.

---

## 12. Vueltas y telemetría — OpenF1 `GET /v1/laps`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `driver_number` | Dorsal del piloto | Entero | 1–99 | Req. (llave) |
| `lap_number` | Número de vuelta | Entero (vueltas) | 1–78 | **Descarte** de la vuelta |
| `lap_duration` | Duración de la vuelta | Decimal (s) | 60–120 | **Descarte** de la vuelta |
| `is_pit_out_lap` | Vuelta de salida de boxes | Booleano | {True, False} | `.get()` → falsy; se **excluye** del ritmo |

> **Proyección de payload:** OpenF1 devuelve **16** campos por vuelta (~564 KB por sesión);
> la app retiene **4** (~101 KB, **−82 %**). Se descartan al recibir: `date_start`,
> `duration_sector_1/2/3`, `i1_speed`, `i2_speed`, `segments_sector_1/2/3`, `st_speed`,
> `meeting_key`, `session_key`.

---

## 13. Respaldo de historial — Jolpica `/laps` y `/pitstops`

Se usan cuando OpenF1 no responde. Los stints se **derivan** partiendo las vueltas en cada parada.

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `number` | Número de vuelta (en `/laps`) | Entero (vueltas) | 1–78 | **Descarte** de la vuelta |
| `Timings[].driverId` | Identificador del piloto | Texto | Categórico | **Descarte** del registro |
| `Timings[].time` | Tiempo de vuelta | Texto (`M:SS.mmm`) | 60–120 s al parsear | **Descarte** si no parsea |
| `Timings[].position` | Posición en esa vuelta | Entero | 1–20 | No se consume |
| `PitStops[].lap` | Vuelta de la parada | Entero (vueltas) | 1–78 | **Descarte** de la parada |
| `PitStops[].stop` | Ordinal de la parada | Entero | 1–4 | No se consume (se usa el `lap`) |
| `PitStops[].duration` | Duración total en la calle de boxes | Decimal (s) | 20–45 | No se consume |
| `PitStops[].time` | Hora local de la parada | Hora (`HH:MM:SS`) | — | No se consume |

**Paginación:** Jolpica limita a 100 registros por respuesta. `/laps` requiere ~12 páginas
por sesión (1129 registros), con un *throttle* de 0.5 s entre páginas y reintentos con
backoff exponencial ante `429`. Los resultados se memorizan con `lru_cache` y caché de
Streamlit de 24 h.

---

## 14. Features y objetivo del modelo — `prediccion.py`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `grid` | Posición de salida | Entero | 0–20 | **Imputación** a 20 |
| `driver_form` | Media histórica de posiciones del piloto (solo carreras previas) | Decimal (posición) | 1.0–20.0 | **Imputación** a la media del set de entrenamiento (o 10.0) |
| `constructor_form` | Media histórica de posiciones del equipo | Decimal (posición) | 1.0–20.0 | Igual |
| `position` | **Variable objetivo**: posición final | Entero | 1–20 | **Descarte**: filas sin posición |
| `season` | Temporada | Entero | 2024, 2025 | Req. |
| `round` | Ronda | Entero | 1–24 | Req. |
| `circuit` | Identificador del circuito | Texto | Categórico (`bahrain`) | Cadena vacía |
| `driver_id` | Identificador del piloto | Texto | Categórico | Cadena vacía; llave |
| `driver_name` | Nombre completo | Texto | Categórico | Degradación a "—" |
| `constructor_id` | Identificador del equipo | Texto | Categórico | Cadena vacía; llave |
| `constructor_name` | Nombre del equipo | Texto | Categórico | Degradación a "—" |

> **Retirada:** `recent_form` se eliminó del conjunto de features. La ablación mostró que era
> redundante con `driver_form` y su retiro **mejora** el acierto de podio (76.4 % → 77.8 %)
> manteniendo el MAE. Features: **3** (`grid`, `driver_form`, `constructor_form`).

---

## 15. Métricas del modelo — derivadas

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `mae` | Error absoluto medio de posición | Decimal (posiciones) | 0–20 | Req. |
| `rmse` | Raíz del error cuadrático medio | Decimal (posiciones) | 0–20 | Req. |
| `baseline_mae` | MAE del baseline (predecir `grid`) | Decimal (posiciones) | 0–20 | Req. |
| `baseline_rmse` | RMSE del baseline | Decimal (posiciones) | 0–20 | Req. |
| `accuracy_pm1` | % de predicciones a ±1 posición | Decimal (%) | 0–100 | Req. |
| `accuracy_pm3` | % de predicciones a ±3 posiciones | Decimal (%) | 0–100 | Req. |
| `podium_hit_rate` | Acierto de podio | Decimal (%) | 0–100 | **Imputación** a 0.0 si no hay casillas |
| `baseline_podium_hit_rate` | Acierto de podio del baseline | Decimal (%) | 0–100 | Igual |
| `rank_correlation` | Correlación de Spearman predicho vs. real | Decimal (adimensional) | −1 a 1 | **Imputación** a 0.0 si la desviación es nula |
| `feature_importance` | Peso relativo de cada variable | Diccionario texto→decimal | 0–1 (suma 1) | Normalización defensiva (divisor mínimo 1.0) |
| `abs_error` | Error absoluto por observación | Decimal (posiciones) | 0–20 | Derivada de `predicted` y `position` |
| `laps_completed` | Vueltas válidas del stint | Entero (vueltas) | 1–78 | Stint descartado si 0 |
| `avg_lap_s` | Tiempo medio de vuelta del stint | Decimal (s) | 65–120 | Requiere ≥1 vuelta válida |
| `best_lap_s` | Mejor vuelta del stint | Decimal (s) | 60–120 | Requiere ≥1 vuelta válida |

---

## 16. Geometría del circuito — `circuits.py`

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `pts` | Puntos del trazado | Lista de (x, y) | ViewBox 720 × 460 | Generado proceduralmente; nunca falta |
| `curvature` | Curvatura discreta por punto | Decimal (rad) | 0.00–0.40 | Derivada de `pts` |
| `corner_idx` | Índices de las curvas detectadas | Lista de enteros | 0–107; típico 7–10 curvas | Lista vacía si no supera el umbral |
| `SECTOR_COLORS` | Color por sector | Texto (hex) | {#E10600, #FFD500, #00B050} | Req. |
| `dim_sectors` | Sectores atenuados por el filtro | Conjunto | Subconjunto de {S1, S2, S3} | **Imputación** a conjunto vacío (= todos visibles) |
| `show_corners` | Mostrar numeración de curvas | Booleano | {True, False} | **Imputación** a `False` |
| `seed` | Semilla de la geometría | Texto | Categórico (clave del circuito) | **Imputación** a `circuit_name` |

---

## 17. Interés de usuarios — estado de sesión

| Variable | Descripción | Tipo / unidad | Rango o categorías | Faltantes |
|---|---|---|---|---|
| `interest_visits` | Contador de vistas por sección | Diccionario texto→entero | Claves: overview, season, prediction, telemetry | **Imputación** a diccionario vacío al iniciar sesión |
| `interest_first_seen` | Marca temporal del primer acceso | Fecha/hora (TZ local) | — | **Imputación** a "ahora" en la primera visita |
| `total_views` | Vistas totales de la sesión | Entero | ≥ 0 | Derivada de `interest_visits` |
| `sections_visited` | Secciones distintas exploradas | Entero | 0–4 | Derivada |
| `top_section` | Sección más visitada | Texto | Raceweek, Temporada, Simulacion, Historial | Degradación a "—" si no hay visitas |
| `session_minutes` | Minutos transcurridos en la sesión | Decimal (min) | ≥ 0.1 | **Imputación** a 0.1 (evita división por cero) |
| `views_per_min` | Ritmo de navegación | Decimal (vistas/min) | ≥ 0 | Derivada |

---

## 18. Notas transversales de calidad de datos

1. **Zona horaria.** Todo cálculo temporal usa `America/Tijuana`. Las fechas ISO se parsean con `strptime("%Y-%m-%d")`; si fallan devuelven `None` y la observación se descarta.
2. **Conversión de horas.** Las horas de Jolpica vienen en UTC; `parse_iso_datetime` asume UTC cuando falta el sufijo `Z`/offset y convierte a TZ local para mostrar.
3. **Cadenas.** Nombres de piloto y equipo se construyen con `strip()`; los campos opcionales usan `.get(clave, default)`, nunca acceso directo.
4. **Numéricos.** La coerción (`_to_int`/`_to_float`) convierte no numéricos a `None`, preservando la diferencia entre "cero" y "desconocido".
5. **Causalidad.** `driver_form` y `constructor_form` se calculan solo con carreras previas, evitando fuga de datos en la evaluación 2025.
6. **Llave de piloto agnóstica.** `driver_key` abstrae el proveedor (dorsal en OpenF1, `driverId` en Jolpica) para que la interfaz no dependa de la fuente.
7. **Respaldo transparente.** El historial indica en pantalla la fuente activa; cuando es Jolpica, el compuesto aparece como `UNKNOWN` y el badge lo advierte.
8. **Caché.** Calendario 30 min · clima 30 min · resultados del modelo y historial de sesiones 24 h. El botón *Actualizar* limpia la caché del calendario.
9. **Límites de API.** Jolpica pagina a 100 registros y aplica `429`; se mitiga con *throttle* (0.5 s), reintentos con backoff (5 intentos) y `lru_cache`. OpenF1 permite 30 req/min en su plan gratuito.
10. **Categóricos sin valor.** Se normalizan a `UNKNOWN` (compuestos) o "—" (textos), nunca a `None` visible en la interfaz.
