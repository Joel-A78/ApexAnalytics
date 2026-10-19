# Diccionario de datos — Apex Analytics · F1

Definición de todas las variables que el proyecto **consume, normaliza o produce**,
organizadas por origen. Cada variable se documenta con: **nombre · significado · tipo / unidad ·
rango o categorías**. El tratamiento de valores faltantes se detalla en el
**Anexo A** al final del documento.

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

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `round` | Número de ronda del campeonato | Entero | 1–24 |
| `raceName` | Nombre oficial del Gran Premio | Texto | Categórico ("Azerbaijan Grand Prix") |
| `date` | Fecha de la carrera | Fecha ISO `YYYY-MM-DD` | Año de la temporada activa |
| `time` | Hora de salida | Hora ISO `HH:MM:SSZ` (UTC) | 00:00:00–23:59:59 |
| `Circuit.circuitName` | Nombre del circuito | Texto | Categórico |
| `Circuit.Location.locality` | Ciudad | Texto | Categórico |
| `Circuit.Location.country` | País | Texto | Categórico |
| `Circuit.Location.lat` | Latitud | Decimal (grados) | −90 a 90 |
| `Circuit.Location.long` | Longitud | Decimal (grados) | −180 a 180 |
| `FirstPractice` | Práctica 1 (`date` + `time`) | Objeto fecha/hora ISO | — |
| `SecondPractice` | Práctica 2 | Objeto fecha/hora ISO | — |
| `ThirdPractice` | Práctica 3 | Objeto fecha/hora ISO | — |
| `SprintQualifying` | Clasificación sprint | Objeto fecha/hora ISO | — |
| `Sprint` | Carrera sprint | Objeto fecha/hora ISO | — |
| `Qualifying` | Clasificación | Objeto fecha/hora ISO | — |
| `url` | Enlace Wikipedia del GP | URL | — |

**Derivadas del calendario**

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `weekend_start` | Primer día del fin de semana | Fecha (TZ local) | Año de temporada |
| `weekend_end` | Último día del fin de semana | Fecha (TZ local) | Año de temporada |
| `days_until` | Días a la próxima carrera | Entero (días) | −400 a 400 (0 = "Hoy") |
| `next_race` | Próxima carrera vigente | Objeto | Fin de semana en curso o futura |
| `is_past` | Carrera ya disputada | Booleano | {True, False} |

---

## 2. Resultados de carrera — Jolpica `GET /f1/{año}/results.json`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `position` | Posición final en carrera | Entero | 1–20 |
| `positionText` | Posición como texto | Texto | 1–20, "R", "D", "E", "W", "F", "N" |
| `points` | Puntos obtenidos | Decimal (puntos) | 0–26 |
| `grid` | Posición de salida | Entero | 0 (pit lane) a 20 |
| `laps` | Vueltas completadas | Entero (vueltas) | 0–78 |
| `status` | Estado final | Texto | "Finished", "+1 Lap", "Accident", "Engine", "Gearbox"… |
| `Driver.driverId` | Identificador del piloto | Texto | Categórico (`max_verstappen`) |
| `Driver.givenName` | Nombre de pila | Texto | Categórico |
| `Driver.familyName` | Apellido | Texto | Categórico |
| `Driver.code` | Sigla de 3 letras | Texto | 3 letras mayúsculas |
| `Driver.nationality` | Nacionalidad | Texto | Categórico |
| `Constructor.constructorId` | Identificador del equipo | Texto | Categórico (`red_bull`) |
| `Constructor.name` | Nombre del equipo | Texto | Categórico |
| `Constructor.nationality` | Nacionalidad del equipo | Texto | Categórico |
| `Time.time` | Tiempo total / diferencia del ganador | Texto (`H:MM:SS.mmm` o `+X.XXX`) | — |
| `FastestLap.AverageSpeed.speed` | Velocidad media de la vuelta rápida | Decimal (km/h) | ~180–260 |
| `cumulative_points` | Puntos acumulados del piloto hasta la ronda | Decimal (puntos) | 0–600 |

---

## 3. Clima actual — Open-Meteo `current=`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `temperature_2m` | Temperatura del aire a 2 m | Decimal (°C) | −20 a 50 |
| `apparent_temperature` | Sensación térmica | Decimal (°C) | −25 a 55 |
| `relative_humidity_2m` | Humedad relativa | Entero (%) | 0–100 |
| `precipitation` | Precipitación instantánea | Decimal (mm) | 0–50 |
| `weather_code` | Código WMO del cielo | Entero (categórico) | 0,1,2,3,45,48,51,53,55,61,63,65,71,73,75,80,81,82,95,96,99 |
| `cloud_cover` | Cobertura nubosa | Entero (%) | 0–100 |
| `pressure_msl` | Presión a nivel del mar | Decimal (hPa) | 950–1050 |
| `wind_speed_10m` | Velocidad del viento a 10 m | Decimal (km/h) | 0–150 |
| `wind_direction_10m` | Dirección del viento | Entero (grados) | 0–359 |
| `wind_gusts_10m` | Rachas de viento | Decimal (km/h) | 0–200 |
| `is_day` | Indicador día/noche | Booleano 0/1 | {0, 1} |

**Derivadas del clima**

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `track_temp` | Temperatura de pista estimada (`apparent_temperature + 9` si es de día) | Decimal (°C) | −25 a 64 |
| `rain_risk` | Máxima probabilidad de lluvia a 3 días | Entero (%) | 0–100 |
| `race_class` | Clase de condición de carrera | Texto (CSS) | `wx-outlook-dry` (<30 %), `wx-outlook-mixed` (≥30 %), `wx-outlook-wet` (≥60 %) |
| `race_note` | Mensaje de condiciones | Texto | 3 mensajes categóricos |

---

## 4. Clima diario (pronóstico) — Open-Meteo `daily=`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `temperature_2m_max` | Temperatura máxima diaria | Decimal (°C) | −20 a 55 |
| `temperature_2m_min` | Temperatura mínima diaria | Decimal (°C) | −30 a 45 |
| `precipitation_probability_max` | Probabilidad máxima de lluvia del día | Entero (%) | 0–100 |
| `weather_code` | Código WMO diario | Entero | Misma escala WMO del grupo 3 |

---

## 5. Catálogo de circuitos — `simulacion.Circuit`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `name` | Nombre del circuito | Texto | 25 categorías (Bahrain…Abu Dhabi, Madrid, Sepang) |
| `base_lap_time` | Vuelta base del circuito | Decimal (s) | 67–106 |
| `pit_loss` | Pérdida de tiempo por paso por boxes | Decimal (s) | 19.0–23.0 |
| `deg_factor` | Multiplicador de degradación del circuito | Decimal (adimensional) | 0.85–1.10 |
| `typical_laps` | Vueltas típicas de carrera | Entero (vueltas) | 44–78 |

> **Retirados:** `overtaking_difficulty`, `safety_car_prob` y `notes` se eliminaron porque
> ningún cálculo ni vista los consumía (3 campos × 25 circuitos).

---

## 6. Catálogo de compuestos — `simulacion.Compound`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `name` | Nombre del compuesto | Texto | Soft, Medium, Hard, Intermediate, Wet |
| `short` | Código del compuesto | Texto | S, M, H, I, W |
| `base_pace` | Delta de ritmo base contra el soft | Decimal (s) | 0.0–4.0 |
| `deg_rate` | Degradación lineal por vuelta | Decimal (s/vuelta) | 0.022–0.045 |
| `cliff_lap` | Vuelta del cambio abrupto de rendimiento | Entero (vueltas) | 14–35 |
| `cliff_drop` | Caída adicional al cruzar el cliff | Decimal (s) | 0.4–0.6 |
| `min_stint` | Stint mínimo viable | Entero (vueltas) | 5–22 |

---

## 7. Simulación de estrategia — derivadas de `simulacion.py`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `stints` | Secuencia de (compuesto, vueltas) | Tupla de pares | Compuestos válidos, vueltas ≥ `min_stint` |
| `stops` | Número de paradas | Entero | 0–2 |
| `total_time` | Tiempo total proyectado | Decimal (s) | ~4200–7800 |
| `pit_laps` | Vueltas de paso por boxes | Lista de enteros | 1–90 |
| `per_lap` | Serie (vuelta, tiempo, compuesto) | Lista de tuplas | — |
| `sample_std` | Desviación estándar Monte Carlo | Decimal (s) | 0–30 |
| `monte_carlo` | Número de simulaciones | Entero | 1–500 |
| `noise_sigma` | Ruido gaussiano por vuelta | Decimal (s) | 0.00–0.50 |
| `gap_to_best` | Margen contra la mejor estrategia | Decimal (s) | 0–200 |
| `starting_compound` | Compuesto de salida | Texto | S, M, H, I, W |
| `rain` | Incluir estrategias de lluvia | Booleano | {True, False} |

---

## 8. Modelo normalizado de historial — `historial.py`

Capa que unifica OpenF1 y Jolpica bajo una misma forma. A continuación, las variables
normalizadas que expone a la interfaz.

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `source` | Proveedor de origen de la sesión | Texto (categórico) | `openf1`, `jolpica` |
| `session_key` | Clave de sesión normalizada | Texto | `openf1`: entero como texto · `jolpica`: `jolpica-{año}-{ronda}` |
| `round` | Ronda de la carrera | Entero | 1–24 |
| `meeting_key` | Clave del Gran Premio | Entero | OpenF1: id real · Jolpica: = `round` |
| `circuit_short_name` | Nombre del circuito | Texto | Categórico |
| `country_name` | País | Texto | Categórico |
| `date_start` | Fecha (y hora) de la sesión | Texto ISO | 2023–2026 |
| `driver_key` | **Llave de piloto agnóstica** | Texto | OpenF1: dorsal · Jolpica: `driverId` |
| `full_name` | Nombre completo del piloto | Texto | Categórico |
| `team_name` | Equipo del piloto | Texto | Categórico |
| `stint_number` | Ordinal del stint | Entero | 1–7 |
| `lap_start` | Primera vuelta del stint | Entero (vueltas) | 1–78 |
| `lap_end` | Última vuelta del stint | Entero (vueltas) | 1–78 |
| `compound` | Compuesto del neumático | Texto | SOFT, MEDIUM, HARD, INTERMEDIATE, WET, **UNKNOWN** |
| `tyre_age_at_start` | Edad del neumático al montar | Entero (vueltas) | 0–40 |
| `lap_number` | Número de vuelta | Entero (vueltas) | 1–78 |
| `lap_duration` | Duración de la vuelta | Decimal (s) | 60–120 |
| `is_pit_out_lap` | Vuelta de salida de boxes | Booleano | {True, False} |

---

## 9. Sesiones — OpenF1 `GET /v1/sessions` y `/v1/meetings`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `session_key` | Identificador único de sesión | Entero | Llave |
| `session_name` | Tipo de sesión | Texto | Race, Sprint, Qualifying, Practice |
| `meeting_key` | Identificador del Gran Premio | Entero | Llave |
| `meeting_name` | Nombre del GP (endpoint `/meetings`) | Texto | Categórico |
| `circuit_short_name` | Nombre corto del circuito | Texto | Categórico |
| `country_name` | País | Texto | Categórico |
| `date_start` | Fecha y hora de inicio | Fecha/hora ISO | 2023–2026 |

> **Proyección de payload:** OpenF1 devuelve 14 campos por sesión; la app retiene **6**.

---

## 10. Pilotos — OpenF1 `GET /v1/drivers`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `driver_number` | Dorsal del piloto | Entero | 1–99 |
| `full_name` | Nombre completo | Texto | Categórico |
| `team_name` | Equipo | Texto | Categórico |

> **Proyección de payload:** OpenF1 devuelve 12 campos por piloto; la app retiene **3**.

---

## 11. Stints — OpenF1 `GET /v1/stints`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `stint_number` | Ordinal del stint | Entero | 1–7 |
| `driver_number` | Dorsal del piloto | Entero | 1–99 |
| `compound` | Compuesto usado | Texto | SOFT, MEDIUM, HARD, INTERMEDIATE, WET |
| `lap_start` | Primera vuelta del stint | Entero (vueltas) | 1–78 |
| `lap_end` | Última vuelta del stint | Entero (vueltas) | 1–78 |
| `tyre_age_at_start` | Edad del neumático al montar | Entero (vueltas) | 0–40 |

> **Proyección de payload:** OpenF1 devuelve 9 campos por stint; la app retiene **6**.

---

## 12. Vueltas y telemetría — OpenF1 `GET /v1/laps`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `driver_number` | Dorsal del piloto | Entero | 1–99 |
| `lap_number` | Número de vuelta | Entero (vueltas) | 1–78 |
| `lap_duration` | Duración de la vuelta | Decimal (s) | 60–120 |
| `is_pit_out_lap` | Vuelta de salida de boxes | Booleano | {True, False} |

> **Proyección de payload:** OpenF1 devuelve **16** campos por vuelta (~564 KB por sesión);
> la app retiene **4** (~101 KB, **−82 %**). Se descartan al recibir: `date_start`,
> `duration_sector_1/2/3`, `i1_speed`, `i2_speed`, `segments_sector_1/2/3`, `st_speed`,
> `meeting_key`, `session_key`.

---

## 13. Respaldo de historial — Jolpica `/laps` y `/pitstops`

Se usan cuando OpenF1 no responde. Los stints se **derivan** partiendo las vueltas en cada parada.

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `number` | Número de vuelta (en `/laps`) | Entero (vueltas) | 1–78 |
| `Timings[].driverId` | Identificador del piloto | Texto | Categórico |
| `Timings[].time` | Tiempo de vuelta | Texto (`M:SS.mmm`) | 60–120 s al parsear |
| `Timings[].position` | Posición en esa vuelta | Entero | 1–20 |
| `PitStops[].lap` | Vuelta de la parada | Entero (vueltas) | 1–78 |
| `PitStops[].stop` | Ordinal de la parada | Entero | 1–4 |
| `PitStops[].duration` | Duración total en la calle de boxes | Decimal (s) | 20–45 |
| `PitStops[].time` | Hora local de la parada | Hora (`HH:MM:SS`) | — |

**Paginación:** Jolpica limita a 100 registros por respuesta. `/laps` requiere ~12 páginas
por sesión (1129 registros), con un *throttle* de 0.5 s entre páginas y reintentos con
backoff exponencial ante `429`. Los resultados se memorizan con `lru_cache` y caché de
Streamlit de 24 h.

---

## 14. Features y objetivo del modelo — `prediccion.py`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `grid` | Posición de salida | Entero | 0–20 |
| `driver_form` | Media histórica de posiciones del piloto (solo carreras previas) | Decimal (posición) | 1.0–20.0 |
| `constructor_form` | Media histórica de posiciones del equipo | Decimal (posición) | 1.0–20.0 |
| `position` | **Variable objetivo**: posición final | Entero | 1–20 |
| `season` | Temporada | Entero | 2024, 2025 |
| `round` | Ronda | Entero | 1–24 |
| `circuit` | Identificador del circuito | Texto | Categórico (`bahrain`) |
| `driver_id` | Identificador del piloto | Texto | Categórico |
| `driver_name` | Nombre completo | Texto | Categórico |
| `constructor_id` | Identificador del equipo | Texto | Categórico |
| `constructor_name` | Nombre del equipo | Texto | Categórico |

> **Retirada:** `recent_form` se eliminó del conjunto de features. La ablación mostró que era
> redundante con `driver_form` y su retiro **mejora** el acierto de podio (76.4 % → 77.8 %)
> manteniendo el MAE. Features: **3** (`grid`, `driver_form`, `constructor_form`).

---

## 15. Métricas del modelo — derivadas

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `mae` | Error absoluto medio de posición | Decimal (posiciones) | 0–20 |
| `rmse` | Raíz del error cuadrático medio | Decimal (posiciones) | 0–20 |
| `baseline_mae` | MAE del baseline (predecir `grid`) | Decimal (posiciones) | 0–20 |
| `baseline_rmse` | RMSE del baseline | Decimal (posiciones) | 0–20 |
| `accuracy_pm1` | % de predicciones a ±1 posición | Decimal (%) | 0–100 |
| `accuracy_pm3` | % de predicciones a ±3 posiciones | Decimal (%) | 0–100 |
| `podium_hit_rate` | Acierto de podio | Decimal (%) | 0–100 |
| `baseline_podium_hit_rate` | Acierto de podio del baseline | Decimal (%) | 0–100 |
| `rank_correlation` | Correlación de Spearman predicho vs. real | Decimal (adimensional) | −1 a 1 |
| `feature_importance` | Peso relativo de cada variable | Diccionario texto→decimal | 0–1 (suma 1) |
| `abs_error` | Error absoluto por observación | Decimal (posiciones) | 0–20 |
| `laps_completed` | Vueltas válidas del stint | Entero (vueltas) | 1–78 |
| `avg_lap_s` | Tiempo medio de vuelta del stint | Decimal (s) | 65–120 |
| `best_lap_s` | Mejor vuelta del stint | Decimal (s) | 60–120 |

---

## 16. Geometría del circuito — `circuits.py`

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `pts` | Puntos del trazado | Lista de (x, y) | ViewBox 720 × 460 |
| `curvature` | Curvatura discreta por punto | Decimal (rad) | 0.00–0.40 |
| `corner_idx` | Índices de las curvas detectadas | Lista de enteros | 0–107; típico 7–10 curvas |
| `SECTOR_COLORS` | Color por sector | Texto (hex) | {#E10600, #FFD500, #00B050} |
| `dim_sectors` | Sectores atenuados por el filtro | Conjunto | Subconjunto de {S1, S2, S3} |
| `show_corners` | Mostrar numeración de curvas | Booleano | {True, False} |
| `seed` | Semilla de la geometría | Texto | Categórico (clave del circuito) |

---

## 17. Interés de usuarios — estado de sesión

| Variable | Significado | Tipo / unidad | Rango o categorías |
|---|---|---|---|
| `interest_visits` | Contador de vistas por sección | Diccionario texto→entero | Claves: overview, season, prediction, telemetry |
| `interest_first_seen` | Marca temporal del primer acceso | Fecha/hora (TZ local) | — |
| `total_views` | Vistas totales de la sesión | Entero | ≥ 0 |
| `sections_visited` | Secciones distintas exploradas | Entero | 0–4 |
| `top_section` | Sección más visitada | Texto | Raceweek, Temporada, Simulacion, Historial |
| `session_minutes` | Minutos transcurridos en la sesión | Decimal (min) | ≥ 0.1 |
| `views_per_min` | Ritmo de navegación | Decimal (vistas/min) | ≥ 0 |

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

---

## Anexo A. Tratamiento de valores faltantes

Regla aplicada a cada variable cuando el valor no está disponible.

| Variable | Tratamiento de faltantes |
|---|---|
| `round` | Descarte del selector; en calendario queda vacío |
| `raceName` | Degradación a "Carrera" |
| `date` | **Descarte**: se excluye de `get_next_race` y del calendario |
| `time` | **Imputación** a 00:00 UTC para ordenar sesiones |
| `Circuit.circuitName` | Degradación a "Circuito" |
| `Circuit.Location.locality` | Degradación a cadena vacía |
| `Circuit.Location.country` | Degradación a "—" |
| `Circuit.Location.lat` | `try/except` → `None` → se omite el clima y se muestra "—" |
| `Circuit.Location.long` | Igual que `lat` |
| `FirstPractice` | Si falta, la sesión no se lista |
| `SecondPractice` | Igual |
| `ThirdPractice` | Igual |
| `SprintQualifying` | Igual |
| `Sprint` | Igual |
| `Qualifying` | Igual |
| `url` | No se consume en KPIs |
| `weekend_start` | `date.min` si no hay sesiones |
| `weekend_end` | `date.max` si no hay sesiones |
| `days_until` | Se omite el KPI si no hay fecha parseable |
| `next_race` | `None` → se oculta la sección de datos geométricos |
| `is_past` | Derivada: `weekend_end < hoy` |
| `position` | **Descarte**: filas sin posición no entran al dataset |
| `positionText` | No se consume; solo trazabilidad |
| `points` | **Imputación** a `0.0` |
| `grid` | **Imputación** a 20 |
| `laps` | Degradación a "—" |
| `status` | Cadena vacía; respaldo de `Time.time` |
| `Driver.driverId` | Cadena vacía; llave de agrupación |
| `Driver.givenName` | Concatenado + `strip()` |
| `Driver.familyName` | Igual |
| `Driver.code` | No se consume |
| `Driver.nationality` | No se consume |
| `Constructor.constructorId` | Cadena vacía; llave de agrupación |
| `Constructor.name` | Degradación a "—" |
| `Constructor.nationality` | No se consume |
| `Time.time` | Respaldo a `status` |
| `FastestLap.AverageSpeed.speed` | Degradación a "—" |
| `cumulative_points` | **Imputación** a 0 por piloto |
| `temperature_2m` | Degradación a "—" |
| `apparent_temperature` | "—"; bloquea el cálculo de `track_temp` |
| `relative_humidity_2m` | "—" |
| `precipitation` | "—" |
| `weather_code` | **Imputación** a 0 ("Despejado") |
| `cloud_cover` | "—" |
| `pressure_msl` | "—" |
| `wind_speed_10m` | "—" |
| `wind_direction_10m` | "—" |
| `wind_gusts_10m` | "—" |
| `is_day` | **Imputación** a 1 (día) |
| `track_temp` | "—" si falta `apparent_temperature` |
| `rain_risk` | **Imputación** a 0 si la lista está vacía |
| `race_class` | Derivada de `rain_risk` |
| `race_note` | Derivada de `rain_risk` |
| `temperature_2m_max` | Si la lista está vacía, no se dibuja el pronóstico |
| `temperature_2m_min` | Igual |
| `precipitation_probability_max` | **Imputación** a 0 |
| `weather_code` | **Imputación** al `weather_code` actual |
| `name` | Req. |
| `base_lap_time` | Req. |
| `pit_loss` | Req. |
| `deg_factor` | Req. |
| `typical_laps` | **Imputación** a 58 |
| `name` | Req. |
| `short` | Req. |
| `base_pace` | Req. |
| `deg_rate` | Req. |
| `cliff_lap` | Req. |
| `cliff_drop` | Req. |
| `min_stint` | Req. |
| `stints` | Req. |
| `stops` | Derivada: `len(stints) − 1` |
| `total_time` | Req. |
| `pit_laps` | Lista vacía si 0 paradas |
| `per_lap` | Req. |
| `sample_std` | **Imputación** a 0.0 si no hay Monte Carlo |
| `monte_carlo` | **Imputación** a 50 |
| `noise_sigma` | **Imputación** a 0.10 |
| `gap_to_best` | 0.0 para la óptima |
| `starting_compound` | **Imputación** a "M" |
| `rain` | **Imputación** a `False` |
| `source` | Req. |
| `session_key` | Req. |
| `round` | Req. |
| `meeting_key` | Req. |
| `circuit_short_name` | Degradación a cadena vacía |
| `country_name` | Cadena vacía |
| `date_start` | Se corta a 10 caracteres; vacío si falta |
| `driver_key` | Req. |
| `full_name` | Degradación a `#{driver_key}` |
| `team_name` | Cadena vacía |
| `stint_number` | `.get()` → `None` |
| `lap_start` | **Descarte** del stint |
| `lap_end` | **Descarte** del stint |
| `compound` | **Imputación** a "UNKNOWN" |
| `tyre_age_at_start` | `None` cuando la fuente no lo publica (siempre en Jolpica) |
| `lap_number` | **Descarte** de la vuelta |
| `lap_duration` | **Descarte** de la vuelta |
| `is_pit_out_lap` | **Derivada** en Jolpica: la vuelta siguiente a cada parada |
| `session_key` | Req. |
| `session_name` | Se filtra por "Race"; descarte si falta |
| `meeting_key` | Req. |
| `meeting_name` | Degradación a `circuit_short_name` |
| `circuit_short_name` | Cadena vacía |
| `country_name` | Cadena vacía |
| `date_start` | Se usa `[:10]` |
| `driver_number` | Req. (se convierte en `driver_key`) |
| `full_name` | Degradación a "#{driver_number}" |
| `team_name` | Cadena vacía |
| `stint_number` | `.get()` → `None` |
| `driver_number` | Req. (llave de cruce con vueltas) |
| `compound` | **Imputación** a "UNKNOWN" |
| `lap_start` | **Descarte** del stint |
| `lap_end` | **Descarte** del stint |
| `tyre_age_at_start` | `.get()` → `None` |
| `driver_number` | Req. (llave) |
| `lap_number` | **Descarte** de la vuelta |
| `lap_duration` | **Descarte** de la vuelta |
| `is_pit_out_lap` | `.get()` → falsy; se **excluye** del ritmo |
| `number` | **Descarte** de la vuelta |
| `Timings[].driverId` | **Descarte** del registro |
| `Timings[].time` | **Descarte** si no parsea |
| `Timings[].position` | No se consume |
| `PitStops[].lap` | **Descarte** de la parada |
| `PitStops[].stop` | No se consume (se usa el `lap`) |
| `PitStops[].duration` | No se consume |
| `PitStops[].time` | No se consume |
| `grid` | **Imputación** a 20 |
| `driver_form` | **Imputación** a la media del set de entrenamiento (o 10.0) |
| `constructor_form` | Igual |
| `position` | **Descarte**: filas sin posición |
| `season` | Req. |
| `round` | Req. |
| `circuit` | Cadena vacía |
| `driver_id` | Cadena vacía; llave |
| `driver_name` | Degradación a "—" |
| `constructor_id` | Cadena vacía; llave |
| `constructor_name` | Degradación a "—" |
| `mae` | Req. |
| `rmse` | Req. |
| `baseline_mae` | Req. |
| `baseline_rmse` | Req. |
| `accuracy_pm1` | Req. |
| `accuracy_pm3` | Req. |
| `podium_hit_rate` | **Imputación** a 0.0 si no hay casillas |
| `baseline_podium_hit_rate` | Igual |
| `rank_correlation` | **Imputación** a 0.0 si la desviación es nula |
| `feature_importance` | Normalización defensiva (divisor mínimo 1.0) |
| `abs_error` | Derivada de `predicted` y `position` |
| `laps_completed` | Stint descartado si 0 |
| `avg_lap_s` | Requiere ≥1 vuelta válida |
| `best_lap_s` | Requiere ≥1 vuelta válida |
| `pts` | Generado proceduralmente; nunca falta |
| `curvature` | Derivada de `pts` |
| `corner_idx` | Lista vacía si no supera el umbral |
| `SECTOR_COLORS` | Req. |
| `dim_sectors` | **Imputación** a conjunto vacío (= todos visibles) |
| `show_corners` | **Imputación** a `False` |
| `seed` | **Imputación** a `circuit_name` |
| `interest_visits` | **Imputación** a diccionario vacío al iniciar sesión |
| `interest_first_seen` | **Imputación** a "ahora" en la primera visita |
| `total_views` | Derivada de `interest_visits` |
| `sections_visited` | Derivada |
| `top_section` | Degradación a "—" si no hay visitas |
| `session_minutes` | **Imputación** a 0.1 (evita división por cero) |
| `views_per_min` | Derivada |
