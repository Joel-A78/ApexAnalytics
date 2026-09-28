# Fichas técnicas de KPIs — Apex Analytics · F1

Documentación de los indicadores implementados en el proyecto de visualización y
predicción de resultados para carreras de Fórmula 1.

**Convenciones**
- `n` = número de observaciones válidas de la muestra.
- `Σ` = sumatoria sobre el conjunto indicado.
- `|X|` = cardinalidad (conteo de elementos) del conjunto `X`.
- Todos los tiempos están en segundos salvo indicación contraria.

---

## Índice

| # | KPI | Sección | Tipo |
|---|-----|---------|------|
| 1 | Eventos esta semana | Raceweek | Contexto |
| 2 | Carreras en la temporada | Raceweek | Contexto |
| 3 | Cuenta regresiva a la próxima carrera | Raceweek | Contexto |
| 4 | Riesgo de lluvia | Raceweek | Condiciones |
| 5 | Temperatura de pista estimada | Raceweek | Condiciones |
| 6 | Número de curvas | Raceweek | Geometría |
| 7 | Vueltas típicas del circuito | Raceweek | Geometría |
| 8 | Tiempo estimado de estrategia | Simulación | Estrategia |
| 9 | Número de paradas | Simulación | Estrategia |
| 10 | Margen vs. 2ª mejor estrategia | Simulación | Estrategia |
| 11 | Desviación estándar Monte Carlo | Simulación | Incertidumbre |
| 12 | Posición predicha | Historial | Modelo |
| 13 | Error de predicción (MAE) | Historial | Modelo |
| 14 | RMSE de posiciones | Historial | Modelo |
| 15 | Precisión del modelo (acierto de podio) | Historial | Modelo |
| 16 | Correlación de ranking (Spearman) | Historial | Modelo |
| 17 | Tiempo medio de vuelta por stint | Historial | Rendimiento |
| 18 | Mejor vuelta del stint | Historial | Rendimiento |
| 19 | Vueltas por stint | Historial | Rendimiento |
| 20 | Interés de usuarios | Footer | Producto |

---

## 1. Eventos esta semana

| Campo | Descripción |
|---|---|
| **Nombre** | Eventos esta semana |
| **Definición** | Número de Grandes Premios cuyo fin de semana (de la primera a la última sesión) se solapa con la semana calendario en curso. |
| **Objetivo** | Detectar si hay actividad de F1 en los próximos siete días para priorizar el monitoreo de sesiones. |
| **Fórmula** | `N = |{ r ∈ Calendario : inicio(r) ≤ D ∧ fin(r) ≥ L }|` donde `L` = lunes y `D` = domingo de la semana actual. |
| **Unidad** | Eventos (entero ≥ 0). |
| **Fuente** | Jolpica/Ergast API — `GET /f1/{año}.json` (fechas de FP1, FP2, FP3, Sprint, Qualifying y Race). |
| **Periodicidad** | Semanal; recalculado en cada carga de página (caché 30 min). |
| **Responsable** | Analista de datos. |
| **Decisión** | Define si la vista Raceweek muestra tarjetas de sesión o el estado vacío, y concentra la atención operativa de la semana. |

---

## 2. Carreras en la temporada

| Campo | Descripción |
|---|---|
| **Nombre** | Carreras en la temporada |
| **Definición** | Total de rondas del campeonato publicadas en el calendario de la temporada activa. |
| **Objetivo** | Dar contexto de escala: cuántas pruebas componen el campeonato y qué fracción representa la ronda en curso. |
| **Fórmula** | `N = |Calendario(año)|` |
| **Unidad** | Carreras (entero). |
| **Fuente** | Jolpica/Ergast API — `GET /f1/{año}.json`. |
| **Periodicidad** | Anual; recalculado en cada carga (caché 30 min). |
| **Responsable** | Analista de datos. |
| **Decisión** | Sirve de denominador para porcentajes de avance de temporada y para validar que el calendario se descargó completo. |

---

## 3. Cuenta regresiva a la próxima carrera

| Campo | Descripción |
|---|---|
| **Nombre** | Cuenta regresiva (días a la próxima carrera) |
| **Definición** | Días naturales que faltan desde la fecha local actual hasta la fecha de la próxima carrera, entendiendo como "próxima" aquella cuyo fin de semana está en curso o cuya fecha aún no ha pasado. |
| **Objetivo** | Cuantificar la urgencia temporal y disparar los preparativos de análisis previo al Gran Premio. |
| **Fórmula** | `días = fecha_carrera − hoy_local` (entero; `0` se muestra como "Hoy"). |
| **Unidad** | Días (entero). |
| **Fuente** | Jolpica/Ergast API (fecha de carrera) + reloj local `America/Tijuana`. |
| **Periodicidad** | Diaria. |
| **Responsable** | Analista de datos. |
| **Decisión** | Prioriza qué circuito simular: a menor cantidad de días, mayor prioridad para preparar la estrategia y revisar el clima. |

---

## 4. Riesgo de lluvia

| Campo | Descripción |
|---|---|
| **Nombre** | Riesgo de lluvia (condiciones de carrera) |
| **Definición** | Máxima probabilidad de precipitación pronosticada para los próximos tres días en la ubicación del circuito; resume la probabilidad de una carrera en mojado. |
| **Objetivo** | Anticipar el cambio de compuestos y ajustar la estrategia por condiciones de pista mojada. |
| **Fórmula** | `riesgo = max( P_lluvia[d] : d ∈ {hoy, mañana, pasado} )` |
| **Clasificación** | `≥ 60 %` → probable (azul) · `≥ 30 %` → posible (amarillo) · `< 30 %` → seco (verde). |
| **Unidad** | Porcentaje (%). |
| **Fuente** | Open-Meteo API — variable diaria `precipitation_probability_max`. |
| **Periodicidad** | Cada 30 min (TTL de caché de clima). |
| **Responsable** | Analista de condiciones / meteorología. |
| **Decisión** | Recomienda el tipo de neumático (seco vs. intermedio/lluvia) e informa si conviene habilitar estrategias de lluvia en el simulador. |

---

## 5. Temperatura de pista estimada

| Campo | Descripción |
|---|---|
| **Nombre** | Temperatura de pista estimada |
| **Definición** | Aproximación de la temperatura del asfalto a partir de la sensación térmica y la insolación diurna. |
| **Objetivo** | Estimar el factor térmico que acelera la degradación del neumático cuando no se dispone de sensores de pista. |
| **Fórmula** | `T_pista = T_sensación + 9 °C` si es de día; `T_pista = T_sensación` si es de noche. |
| **Unidad** | Grados Celsius (°C). |
| **Fuente** | Open-Meteo API — `apparent_temperature` e `is_day`. |
| **Periodicidad** | Cada 30 min. |
| **Responsable** | Analista de condiciones. |
| **Decisión** | Ajusta la expectativa de degradación y el número de paradas previstas en circuitos de alta abrasión. |

---

## 6. Número de curvas

| Campo | Descripción |
|---|---|
| **Nombre** | Número de curvas |
| **Definición** | Cantidad de curvas detectadas sobre el trazado procedural del circuito, identificadas como máximos locales de curvatura separados por una distancia mínima. |
| **Objetivo** | Cuantificar la complejidad del trazado y servir de simbología en el mapa. |
| **Fórmula** | Curvatura discreta `κᵢ = |Δθᵢ|` con `θᵢ = atan2(pᵢ₊₁ − pᵢ)`; se seleccionan los máximos locales con `κᵢ ≥ 0.05` y separación `≥ 4` muestras (máx. 16). |
| **Unidad** | Curvas (entero). |
| **Fuente** | Geometría generada en `circuits.py` (sin API externa). |
| **Periodicidad** | Estática por circuito (determinista por nombre). |
| **Responsable** | Desarrollador front-end / visualización. |
| **Decisión** | Indica la complejidad del trazado y alimenta la leyenda del mapa; sirve para comparar circuitos urbanos vs. permanentes. |

---

## 7. Vueltas típicas del circuito

| Campo | Descripción |
|---|---|
| **Nombre** | Vueltas típicas del circuito |
| **Definición** | Número de vueltas habitual de una carrera en ese circuito, usado como valor por defecto para la simulación. |
| **Objetivo** | Precargar la simulación con la distancia real de carrera y evitar configuraciones irreales. |
| **Fórmula** | Valor constante de catálogo: `typical_laps(circuito)`. |
| **Unidad** | Vueltas (entero). |
| **Fuente** | Catálogo interno `simulacion.CIRCUITS`. |
| **Periodicidad** | Anual (se actualiza con el calendario). |
| **Responsable** | Analista de estrategia. |
| **Decisión** | Define el horizonte temporal de la simulación; determina si una estrategia de 1 o 2 paradas es viable según la distancia. |

---

## 8. Tiempo estimado de estrategia

| Campo | Descripción |
|---|---|
| **Nombre** | Tiempo estimado de estrategia |
| **Definición** | Tiempo total de carrera proyectado para la estrategia de paradas óptima, sumando los tiempos de vuelta simulados y las pérdidas por paso por boxes. |
| **Objetivo** | Comparar estrategias de 1, 2 y 3 paradas y seleccionar la de menor tiempo total. |
| **Fórmula** | `T_total = Σ t_vuelta(v) + n_paradas × pit_loss`<br>con `t_vuelta = t_base + pace_compuesto + deg_rate × deg_factor × max(v−1, 0) + cliff` |
| **Unidad** | Tiempo en formato `h:mm:ss.cc` (segundos internamente). |
| **Fuente** | Cálculo interno (`simulacion.py`) sobre el catálogo de circuitos y compuestos. |
| **Periodicidad** | Por cada cambio de parámetro en la pestaña Simulación. |
| **Responsable** | Estratega de carrera. |
| **Decisión** | Elige el plan de paradas, define las ventanas de pit y evalúa el impacto de cambiar compuestos. |

---

## 9. Número de paradas

| Campo | Descripción |
|---|---|
| **Nombre** | Número de paradas |
| **Definición** | Cantidad de cambios de neumático previstos por la estrategia recomendada. |
| **Objetivo** | Caracterizar la estrategia y contrastarla con la práctica habitual del circuito. |
| **Fórmula** | `n_paradas = n_stints − 1` |
| **Unidad** | Paradas (entero ≥ 0). |
| **Fuente** | Cálculo interno (`simulacion.Strategy.stops`). |
| **Periodicidad** | Por cada cambio de parámetro en la pestaña Simulación. |
| **Responsable** | Estratega de carrera. |
| **Decisión** | Determina el número de ventanas de pit a planificar y el riesgo asociado a perder posición en pista. |

---

## 10. Margen vs. 2ª mejor estrategia

| Campo | Descripción |
|---|---|
| **Nombre** | Margen vs. 2ª mejor estrategia |
| **Definición** | Diferencia de tiempo total entre la estrategia recomendada y la segunda clasificada. |
| **Objetivo** | Medir cuán robusta es la recomendación: un margen amplio indica una decisión clara; uno estrecho, una decisión sensible. |
| **Fórmula** | `margen = T_total(2ª) − T_total(1ª)` |
| **Unidad** | Segundos (s), con signo `+`. |
| **Fuente** | Ranking interno de estrategias (`simulacion.recommend`). |
| **Periodicidad** | Por cada cambio de parámetro en la pestaña Simulación. |
| **Responsable** | Estratega de carrera. |
| **Decisión** | Si el margen es pequeño, se recomienda considerar flexibilidad y factores externos (safety car, tráfico) antes de fijar el plan. |

---

## 11. Desviación estándar Monte Carlo

| Campo | Descripción |
|---|---|
| **Nombre** | Desviación estándar Monte Carlo (Std MC) |
| **Definición** | Dispersión del tiempo total de carrera entre las `N` repeticiones de la simulación con ruido gaussiano por vuelta. |
| **Objetivo** | Cuantificar la incertidumbre de cada estrategia y distinguir planes robustos de planes frágiles. |
| **Fórmula** | `σ = √( (1/N) · Σ (Tⱼ − T̄)² )` con `Tⱼ` el tiempo total de la j-ésima corrida y `T̄` su media. |
| **Unidad** | Segundos (s). |
| **Fuente** | Motor Monte Carlo (`simulacion.recommend`, por defecto 50 corridas, `σ_ruido = 0.10 s/vuelta`). |
| **Periodicidad** | Por cada cambio de parámetros (vueltas, ruido, nº de simulaciones). |
| **Responsable** | Analista cuantitativo. |
| **Decisión** | Prioriza estrategias estables ante variabilidad (tráfico, clima, errores) y descarta las de alto riesgo aunque su media sea buena. |

---

## 12. Posición predicha

| Campo | Descripción |
|---|---|
| **Nombre** | Posición predicha |
| **Definición** | Posición de llegada estimada por el modelo de regresión para cada piloto. |
| **Objetivo** | Estimar el resultado de carrera a partir de la posición de salida y la forma reciente. |
| **Fórmula** | `ŷ = β₀ + β₁·grid + β₂·forma_piloto + β₃·forma_equipo + β₄·forma_reciente` (regresión Ridge, `α = 1.0`). |
| **Unidad** | Posición (escala continua; se reporta con un decimal). |
| **Fuente** | Jolpica/Ergast API — resultados de 2024 (entrenamiento) y 2025 (evaluación). |
| **Periodicidad** | Por temporada / evaluación (caché 24 h). |
| **Responsable** | Científico de datos. |
| **Decisión** | Ordena a los pilotos por probabilidad de buen resultado y permite detectar candidatos a podio o a remontada respecto de su posición de salida. |

---

## 13. Error de predicción (MAE)

| Campo | Descripción |
|---|---|
| **Nombre** | Error de predicción (MAE) |
| **Definición** | Error absoluto medio entre la posición predicha y la posición real en la temporada de evaluación. |
| **Objetivo** | Medir el desempeño del modelo en posiciones, de forma interpretable y robusta a valores atípicos. |
| **Fórmula** | `MAE = (1/n) · Σ |ŷᵢ − yᵢ|` |
| **Unidad** | Posiciones (menor es mejor). |
| **Fuente** | Evaluación sobre 2025 (479 resultados) con modelo entrenado en 2024. |
| **Periodicidad** | Por temporada evaluada. |
| **Responsable** | Científico de datos. |
| **Decisión** | Aceptar o descartar el modelo comparándolo contra el baseline (predecir la posición de salida); diferencia actual: −0.15 posiciones. |

---

## 14. RMSE de posiciones

| Campo | Descripción |
|---|---|
| **Nombre** | RMSE de posiciones |
| **Definición** | Raíz del error cuadrático medio de la posición predicha respecto de la real. |
| **Objetivo** | Penalizar con mayor severidad los errores grandes, complementando al MAE. |
| **Fórmula** | `RMSE = √( (1/n) · Σ (ŷᵢ − yᵢ)² )` |
| **Unidad** | Posiciones (menor es mejor). |
| **Fuente** | Evaluación sobre 2025. |
| **Periodicidad** | Por temporada evaluada. |
| **Responsable** | Científico de datos. |
| **Decisión** | Detecta si el modelo comete errores catastróficos aislados (p. ej. abandonos no anticipados) aunque su MAE sea aceptable. |

---

## 15. Precisión del modelo (acierto de podio)

| Campo | Descripción |
|---|---|
| **Nombre** | Precisión del modelo (acierto de podio) |
| **Definición** | Porcentaje de podios reales que el modelo logró incluir en su top-3 predicho, agregado sobre todas las carreras evaluadas. |
| **Objetivo** | Medir la capacidad del modelo para identificar el resultado más relevante (el podio), no solo el orden general. |
| **Fórmula** | `Precisión = ( Σ_carreras |top3_pred ∩ top3_real| / (3 · n_carreras) ) × 100` |
| **Unidad** | Porcentaje (%). |
| **Fuente** | Evaluación sobre 2025 (24 carreras × 3 puestos = 72 casillas). |
| **Periodicidad** | Por temporada evaluada. |
| **Responsable** | Científico de datos. |
| **Decisión** | Comunica la utilidad práctica del modelo al público no técnico; con 76 % de acierto, respalda usarlo como referencia de favoritos al podio. |

---

## 16. Correlación de ranking (Spearman)

| Campo | Descripción |
|---|---|
| **Nombre** | Correlación de ranking (Spearman) |
| **Definición** | Correlación entre el orden de llegada predicho y el real, evaluada sobre los rangos y no sobre los valores. |
| **Objetivo** | Medir la capacidad de ordenamiento global del modelo, independiente de la escala de posiciones. |
| **Fórmula** | `ρ = corr( rank(ŷ), rank(y) )` |
| **Unidad** | Adimensional, rango [−1, 1] (más cercano a 1 es mejor). |
| **Fuente** | Evaluación sobre 2025. |
| **Periodicidad** | Por temporada evaluada. |
| **Responsable** | Científico de datos. |
| **Decisión** | Valida que el modelo ordena correctamente a la parrilla; un ρ bajo obligaría a revisar las variables explicativas. |

---

## 17. Tiempo medio de vuelta por stint

| Campo | Descripción |
|---|---|
| **Nombre** | Tiempo medio de vuelta por stint |
| **Definición** | Tiempo promedio de las vueltas válidas de un stint, excluyendo vueltas de salida de boxes. |
| **Objetivo** | Comparar el ritmo de cada piloto por compuesto y por tramo de carrera. |
| **Fórmula** | `t̄ = (1/m) · Σ t_vuelta(i)` sobre las `m` vueltas válidas del stint. |
| **Unidad** | Segundos (s). |
| **Fuente** | OpenF1 API — `GET /v1/laps` y `GET /v1/stints`. |
| **Periodicidad** | Por sesión/carrera analizada (caché 24 h). |
| **Responsable** | Analista de rendimiento. |
| **Decisión** | Identifica qué piloto gestiona mejor cada compuesto y en qué ventana conviene atacar o defenderse. |

---

## 18. Mejor vuelta del stint

| Campo | Descripción |
|---|---|
| **Nombre** | Mejor vuelta del stint |
| **Definición** | Vuelta más rápida registrada dentro del stint (excluyendo vueltas de salida de boxes). |
| **Objetivo** | Medir el potencial máximo de cada compuesto y detectar el momento óptimo de rendimiento. |
| **Fórmula** | `t_min = min( t_vuelta(i) )` sobre las vueltas válidas del stint. |
| **Unidad** | Segundos (s). |
| **Fuente** | OpenF1 API — `GET /v1/laps`. |
| **Periodicidad** | Por sesión/carrera analizada. |
| **Responsable** | Analista de rendimiento. |
| **Decisión** | Apoya la decisión de undercut: si el rival ya marcó su mejor vuelta, el compuesto está entrando en su fase de caída. |

---

## 19. Vueltas por stint

| Campo | Descripción |
|---|---|
| **Nombre** | Vueltas por stint (longitud efectiva) |
| **Definición** | Cantidad de vueltas válidas completadas dentro de un stint. |
| **Objetivo** | Cuantificar la durabilidad real de cada compuesto en condiciones de carrera. |
| **Fórmula** | `m = |{ vueltas i : vueltas_validas(i) }|`, con `vueltas_validas` = dentro del rango del stint, sin `is_pit_out_lap` y con duración registrada. |
| **Unidad** | Vueltas (entero). |
| **Fuente** | OpenF1 API — `GET /v1/laps` y `GET /v1/stints`. |
| **Periodicidad** | Por sesión/carrera analizada. |
| **Responsable** | Analista de rendimiento. |
| **Decisión** | Valida el `min_stint` del simulador y sugiere cuántas vueltas se puede estirar cada compuesto. |

---

## 20. Interés de usuarios

| Campo | Descripción |
|---|---|
| **Nombre** | Interés de usuarios |
| **Definición** | Conjunto de métricas de uso de la sesión actual: vistas totales, secciones exploradas, sección más vista, minutos en sesión y vistas por minuto. |
| **Objetivo** | Estimar la demanda potencial del producto y detectar qué secciones generan más interés. |
| **Fórmula** | `vistas = Σ visitas(sección)`<br>`secciones = |{ secciones con ≥ 1 visita }|`<br>`minutos = (ahora − primer_acceso) / 60`<br>`vistas/min = vistas / max(minutos, 0.1)` |
| **Unidad** | Vistas (entero), secciones (entero), minutos (decimal), vistas/min (decimal). |
| **Fuente** | Estado de sesión de la aplicación (`st.session_state`). |
| **Periodicidad** | En tiempo real, en cada interacción con el sidebar. |
| **Responsable** | Product Owner. |
| **Decisión** | Orienta prioridades de desarrollo: una sección poco visitada puede requerir rediseño; un ratio vistas/min alto indica navegación exploratoria. |

---

## Resumen de fuentes

| Fuente | KPIs que alimenta | URL |
|---|---|---|
| Jolpica / Ergast API | 1, 2, 3, 7, 12–16 | https://jolpi.ca/ergast/f1/ |
| OpenF1 API | 17, 18, 19 | https://openf1.org/ |
| Open-Meteo API | 4, 5 | https://open-meteo.com/ |
| Catálogo interno `simulacion.py` | 7–11 | — |
| Geometría procedural `circuits.py` | 6 | — |
| Estado de sesión Streamlit | 20 | — |
| Referencias institucionales | Contexto y validación reglamentaria | https://www.fia.com/ · https://www.formula1.com/ |

---

## Notas de gobierno de datos

1. **Trazabilidad.** Cada KPI declara su fuente y su fórmula. Los KPIs 8–11 y 12–16 son *derivados*: dependen de parámetros de modelo que pueden recalibrarse.
2. **Linaje temporal.** El modelo usa validación temporal estricta (entrenamiento 2024, evaluación 2025) para evitar fuga de información futura; las variables de forma son *causales* (solo usan carreras previas).
3. **Caché.** Calendario 30 min; resultados de modelo y telemetría de sesiones 24 h; clima 30 min. El botón *Actualizar* invalida el calendario.
4. **Limitaciones.** La posición predicha es continua y sensible a abandonos no modelados; el MAE se reporta junto al baseline porque la posición de salida es un predictor muy fuerte en F1.
5. **Propiedad.** Datos y marcas pertenecen a sus titulares (FIA, Formula 1 y proveedores de API). Este proyecto es independiente y de carácter analítico.
