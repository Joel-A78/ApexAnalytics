# Plan de proyecto — Design Thinking

Apex Analytics · F1 — Visualización y predicción de resultados en carreras automotrices.

**Metodología:** Design Thinking (Stanford d.school), en 6 fases iterativas:
**Empatizar → Definir → Idear → Prototipar → Evaluar → Presentar**. Cada fase
tiene un producto verificable y criterios de revisión medibles; el ciclo se repite
cuando la evaluación detecta brechas (por ejemplo, la resiliencia de fuentes en la
fase 5 devolvió el proyecto a Prototipar).

**Periodo global:** 22 ago 2026 – 10 oct 2026.

---

## Tabla de fases

| Fase / sprint y periodo | Actividades y herramientas | Producto | Criterio de revisión | Dependencia |
|---|---|---|---|---|
| **1. Empatizar**<br>22 ago – 3 sep 2026 | Inmersión en el dominio F1: revisión del calendario, reglamento de neumáticos y flujo de un fin de semana. Sondeo de APIs públicas (Jolpica/Ergast, OpenF1, Open-Meteo) con `urllib` y muestras JSON. Entrevista con el usuario para acotar el problema. Herramientas: navegación de documentación, scripts de sondeo, notas de campo. | **Informe de fuentes y alcance.** Matriz de fuentes en `docs/`: qué dato entrega cada API, cobertura temporal, límites de uso y campos disponibles. Inventario de APIs descartadas (FastF1). | Las 3 APIs responden `200` y devuelven el esquema esperado en una prueba reproducible. Cada fuente declara cobertura (Jolpica 1950–hoy · OpenF1 2023–hoy · Open-Meteo 3 días) y límite (OpenF1 30 req/min). Se descarta toda fuente sin viabilidad de uso. | Ninguna |
| **2. Definir**<br>4 sep – 10 sep 2026 | Formulación del problema: *"visualizar y predecir resultados de F1"*. Alcance cerrado a **una sola serie** (F1). Identificación de KPIs y del usuario objetivo (analista/aficionado). Definición de la arquitectura modular y del esquema de validación temporal (*train 2024 / eval 2025*). Herramientas: tablero de KPIs, modelos de datos, diagrama de módulos. | **Definición del alcance + catálogo de KPIs + arquitectura.** Documento de KPIs con nombre, definición, objetivo, fórmula, unidad, fuente, periodicidad y responsable. Mapa de módulos (`app` · `simulacion` · `prediccion` · `circuits` · `openf1`/`historial`). | Cada KPI está formulado con nombre, definición, fórmula, unidad, fuente y decisión que apoya. El alcance excluye explícitamente otras series y quedan declarados los límites. La arquitectura separa datos, lógica y presentación (un módulo por responsabilidad). | Fase 1 |
| **3. Idear**<br>11 sep – 17 sep 2026 | Generación de soluciones: simulador de estrategia de paradas, comparador de stints por compuesto y modelo de predicción de posiciones. Elección de técnicas: degradación lineal + *cliff* + Monte Carlo; regresión Ridge con validación temporal. Diseño de la metadata visual (paleta Pirelli, semáforo de sectores, tarjetas de clima). Herramientas: bocetos, prueba de modelos alternativos (Ridge vs. GBR vs. RF) y **ablación de features**. | **Diseño de las 4 secciones + motor de simulación.** Especificación de Raceweek, Simulacion, Historial y Modelo. Prototipo de `simulacion.py` (compuestos, circuitos, Monte Carlo). Resultado de la ablación de features y selección justificada del modelo. | La ablación compara ≥4 combinaciones de features y justifica la elegida por métrica, no por intuición. Se descartan explícitamente las alternativas peores (GBR/RF frente a Ridge; `recent_form` por redundante). Cada visualización propuesta tiene un dato de origen trazable a una fuente de la fase 1. | Fase 2 |
| **4. Prototipar**<br>18 sep – 1 oct 2026 | Construcción del dashboard: Streamlit + Plotly + pandas, CSS propio, integración de las APIs con caché y *timezone* local. Implementación por incrementos: Raceweek → Simulacion → Historial → Modelo. Herramientas: `st.cache_data`, control de versiones (Git), Docker, `streamlit.testing.v1.AppTest` como *smoke test*. | **Aplicación funcional (4 secciones).** `app.py`, `assets/style.css`, `circuits.py`, `simulacion.py`, `prediccion.py`, `openf1.py`, `historial.py`, `Dockerfile`/`docker-compose.yml`, `requirements.txt`. | Las 4 secciones renderizan **sin errores ni excepciones** en `AppTest`. El contenedor arranca *healthy* y sirve en el puerto 8501. Ningún módulo importa datos de otro sin pasar por su función de acceso (sin acoplamiento directo). La app funciona con caché y respeta la zona horaria declarada. | Fase 3 |
| **5. Evaluar**<br>2 oct – 9 oct 2026 | Validación con datos reales y pruebas de calidad. Verificación del modelo sobre 2025 (MAE, RMSE, acierto de podio, Spearman) contra el *baseline*. Reducción de datos (funciones y campos sin uso, recorte de payload, duplicados). Pruebas de resiliencia de fuentes y **Plan B**: respaldo con Jolpica ante la caída de OpenF1 (401). Documentación final. Herramientas: `AppTest`, scripts de ablación, conteo de payload, logs del contenedor. | **Informe de validación + documentación + versión resiliente.** `docs/diccionario-variables.md`, `docs/fichas-kpi.md`, informe de reducción de datos (variables, KB, funciones) y *fallback* `historial.py` operativo. Commit final en Git. | El modelo **supera al baseline** (MAE 3.19 < 3.34; podio 77.8 % > 75.0 %). Las 4 secciones siguen sin errores tras las optimizaciones. El *fallback* reproduce los datos de OpenF1 (63 stints y 1129 vueltas idénticos en Bahrain 2024). Toda reducción conserva la funcionalidad. La documentación cubre el 100 % de las variables y KPIs. | Fase 4 |
| **6. Presentar**<br>10 oct 2026 | Preparación del hito de cierre: recorrido guiado por las 4 secciones con datos en vivo, redacción del guion de demo y del resumen ejecutivo de resultados. Verificación *pre-vuelo* del entorno (contenedor *healthy*, puerto 8501, caché caliente) y ensayo cronometrado. Publicación del repositorio con README, documentación y *commits* limpios. Herramientas: Streamlit en Docker, `AppTest` como puerta previa, guion de demo, `README.md`, `docs/`. | **Presentación del proyecto completo + demo reproducible.** Guion de demo (10 min), resumen ejecutivo (problema → solución → KPIs → resultados), repositorio público con las 4 secciones operativas y las 3 piezas de documentación (`diccionario-variables`, `fichas-kpi`, `plan-design-thinking`). | La demo recorre las **4 secciones sin errores** en ≤10 min, ejecutada desde cero (`docker compose up`) en una máquina limpia. Cada cifra mostrada está respaldada por un artefacto del repo (no hay números sin fuente). El README permite a un tercero reproducir la app con un comando. El repositorio queda sin archivos sin seguimiento (*working tree clean*). | Fase 5 |

---

## Trazabilidad de la iteración

Design Thinking es iterativo: la fase 5 detectó dos brechas que devolvieron el
proyecto a fases anteriores.

| Hallazgo en Evaluar | Fase afectada | Acción |
|---|---|---|
| `recent_form` no aportaba y `Circuit` tenía campos muertos | Idear / Prototipar | Ablación → se retiró la feature y 3 campos; el podio **mejoró** de 76.4 % a 77.8 % |
| OpenF1 devolvió `401` y dejó el Historial sin datos | Empatizar / Prototipar | Nueva fuente de respaldo (Jolpica `/laps` + `/pitstops`) y capa de normalización `historial.py` |

---

## Resumen por fase

| Fase | Foco | Producto clave | Señal de cierre |
|---|---|---|---|
| Empatizar | Entender el dominio y las fuentes | Matriz de fuentes | 3 APIs viables y documentadas |
| Definir | Acotar problema y métricas | Catálogo de KPIs y arquitectura | KPIs completos y trazables |
| Idear | Elegir técnicas y diseño | Motor de simulación y diseño de secciones | Selección de modelo justificada por métrica |
| Prototipar | Construir el producto | App con 4 secciones y 7 módulos | 4/4 secciones sin errores |
| Evaluar | Validar, optimizar y documentar | Informe + docs + versión resiliente | Supera baseline y soporta caída de fuente |

---

## Dependencias

```
Empatizar ──▶ Definir ──▶ Idear ──▶ Prototipar ──▶ Evaluar
                                        ▲              │
                                        └──── iteración ┘
```

- **Empatizar** no depende de nada; habilita todo lo demás.
- **Definir** requiere las fuentes de Empatizar para fijar el alcance con datos reales.
- **Idear** requiere el alcance y los KPIs de Definir.
- **Prototipar** requiere las decisiones técnicas de Idear.
- **Evaluar** requiere el producto de Prototipar; si encuentra brechas, realimenta **Idear y Prototipar**.
- **Presentar** requiere la versión validada y documentada de Evaluar.

---

## Explicación del procedimiento

Paso a paso de cada fase: **qué** se hace, **con qué** datos o recursos, **cómo**
se hace y **qué** se obtiene.

### Fase 1 — Empatizar (entender el dominio y las fuentes)

**Qué haces.** Entender el objeto de estudio (un fin de semana de F1) y averiguar
qué datos existen realmente y de dónde se pueden obtener sin costo ni credenciales.

**Con qué.** Un navegador, la terminal y `urllib` de la biblioteca estándar. Como
insumo, la documentación pública de las APIs candidatas y el calendario oficial
de la temporada.

**Cómo.** Se sondea cada API con una petición mínima y se inspecciona el JSON
devuelto para confirmar que existe el campo que se necesita:

```
GET api.jolpi.ca/ergast/f1/2026.json          → round, raceName, Circuit.Location
GET api.jolpi.ca/ergast/f1/2024/1/laps.json   → 1129 vueltas con Timings[].time
GET api.jolpi.ca/ergast/f1/2024/1/pitstops.json → 43 paradas con lap y duration
GET api.openf1.org/v1/stints?session_key=9472 → compound, lap_start, lap_end
GET api.open-meteo.com/v1/forecast?...        → temperature_2m, weather_code
```

Se descarta toda fuente que no responda o que no encaje con el alcance (por
ejemplo, `fastf1` por dependencia de red no disponible en el entorno).

**Resultado.** Una matriz de fuentes con cobertura, límite y campos de cada API.
Ese inventario es el que después alimenta **todas** las secciones: sin confirmar
que `Timings[].time` existe, no se podría construir el comparador de stints.

### Fase 2 — Definir (acotar el problema y las métricas)

**Qué haces.** Convertir el hallazgo anterior en un problema medible y en una
lista cerrada de indicadores.

**Con qué.** El informe de fuentes de la fase 1 y los campos reales disponibles
(no los deseables).

**Cómo.** Se fija el alcance a **F1 únicamente** y se formula el objetivo
("visualizar y predecir resultados"). Luego se define cada KPI respondiendo siete
preguntas: nombre, definición, objetivo, fórmula, unidad, fuente, periodicidad y
decisión que apoya. La fórmula se escribe contra los campos confirmados en la
fase 1, lo que garantiza que cada indicador sea **calculable**:

| Indicador | Insumo de la fase 1 | Fórmula |
|---|---|---|
| Error de predicción | `grid`, `position` de `/results` | `MAE = (1/n)·Σ\|ŷᵢ − yᵢ\|` |
| Tiempo de estrategia | Catálogo de circuitos y compuestos | `Σ t_vuelta + n_paradas·pit_loss` |
| Acierto de podio | `position` por carrera | `Σ\|top3_pred ∩ top3_real\| / (3·n)` |

Se define también la **validación temporal** (*train 2024 / eval 2025*) y la
arquitectura modular, para que cada responsabilidad viva en un archivo distinto.

**Resultado.** El catálogo de KPIs y el mapa de módulos. Aquí queda claro que la
plataforma no es un fin en sí mismo: es el soporte de los indicadores definidos.

### Fase 3 — Idear (elegir técnicas y diseño)

**Qué haces.** Decidir **cómo** se calculará cada indicador, comparando
alternativas en lugar de asumir la primera idea.

**Con qué.** Los datos limpios de la fase 1 (479 resultados por temporada) y
`scikit-learn` para el modelo; lápiz y papel para el diseño visual.

**Cómo.**
1. Para la **estrategia**: se modela la degradación como
   `t_vuelta = base + pace + deg_rate·deg_factor·(v−1) + cliff`, se agregan las
   paradas y se corre **Monte Carlo** (50 réplicas con ruido gaussiano) para
   obtener no solo un tiempo sino su dispersión.
2. Para la **predicción**: se construyen features **causales** (solo carreras
   previas) y se comparan tres modelos —Ridge, Gradient Boosting y Random
   Forest— con una **ablación** de las 15 combinaciones de features:

   ```
   ['grid']                                    MAE 3.337  podio 75.0 %
   ['grid','driver_form']                      MAE 3.191  podio 72.2 %
   ['grid','driver_form','constructor_form']   MAE 3.193  podio 77.8 %  ← elegida
   ['grid','driver_form','constructor_form','recent_form']  MAE 3.198  podio 76.4 %
   ```
3. Para lo **visual**: se elige la paleta de compuestos Pirelli (rojo/amarillo/
   blanco/verde/azul) y un semáforo de sectores, de modo que el color siga una
   convención real y no una decorativa.

**Resultado.** Las técnicas seleccionadas por **métrica** (no por intuición) y el
diseño de las 4 secciones. Se documenta qué se descartó y por qué (`recent_form`
por redundante; GBR/RF por no superar a Ridge).

### Fase 4 — Prototipar (construir la plataforma)

**Qué haces.** Traducir las decisiones en una aplicación funcionando.

**Con qué.** Streamlit + Plotly + pandas, CSS propio, Docker y Git. Como datos,
las APIs de la fase 1 leídas a través de módulos de acceso con caché.

**Cómo.** Se construye **por incrementos**, un commit por sección:
1. **Raceweek** — integración de Jolpica, clima (Open-Meteo), circuito procedural.
2. **Simulacion** — motor de estrategia y su vista, con la próxima carrera tomada
   de Raceweek.
3. **Historial** — proveedor `openf1.py`, luego la capa `historial.py`.
4. **Modelo** — `prediccion.py` y su bloque de KPIs dentro de Historial.

Cada incremento sigue el mismo patrón: **módulo de datos → función de render →
etiqueta de KPI**. La preparación de datos ocurre en el módulo (`fetch_*` +
`@st.cache_data`), el cálculo en el módulo puro (`calcula`) y solo el resultado
llega a la interfaz.

**Resultado.** La app con 4 secciones y 7 módulos, verificada con `AppTest`
(4/4 secciones sin errores) y con el contenedor en estado *healthy*.

### Fase 5 — Evaluar (validar, optimizar y documentar)

**Qué haces.** Comprobar que los indicadores son correctos, que el modelo sirve y
que la plataforma resiste fallos.

**Con qué.** Los datos de 2025 como conjunto de prueba, los scripts de validación
y los logs del contenedor.

**Cómo.**
1. **Validar el modelo**: se compara contra un *baseline* trivial (predecir la
   posición de salida). El modelo lo supera: MAE 3.19 < 3.34 y podio 77.8 % > 75.0 %.
2. **Optimizar**: se eliminan 6 funciones y 3 campos sin uso, se recorta el
   *payload* de OpenF1 (16 → 4 campos por vuelta, −82 %) y se corrigen duplicados.
   La regla es estricta: **toda reducción debe conservar la funcionalidad**.
3. **Probar resiliencia**: OpenF1 responde `401`; se construye un **Plan B** con
   Jolpica (`/laps` + `/pitstops`) que **deriva** los stints partiendo las vueltas
   en cada parada. Se valida contra la fuente original: 63 stints y 1129 vueltas
   idénticos en Bahrain 2024.
4. **Documentar**: diccionario de variables y fichas de KPI.

**Resultado.** Un informe de validación, la versión resiliente y la documentación.
El hallazgo del `401` no se parchó: se devolvió el proyecto a **Empatizar**
(buscar otra fuente) y a **Prototipar** (construir la capa de respaldo).

### Fase 6 — Presentar (comunicar el proyecto completo)

**Qué haces.** Mostrar el proyecto terminado, demostrando que funciona y que sus
cifras son verificables.

**Con qué.** El repositorio con la versión validada, el contenedor y las tres
piezas de documentación.

**Cómo.** Se prepara un guion que recorre el problema → la solución → los KPIs →
los resultados. Antes de presentar se ejecuta una verificación *pre-vuelo*:

```
docker compose up --build          → contenedor healthy, puerto 8501
python -m pytest  (o AppTest)      → 4/4 secciones sin errores
git status                         → working tree clean
```

El recorrido en vivo sigue el flujo de datos: primero Raceweek (calendario real),
luego Simulacion (la próxima carrera entra sola), después Historial (stints con
la fuente indicada en pantalla) y cierra con los KPIs del modelo.

**Resultado.** La presentación, el resumen ejecutivo y el repositorio reproducible
por un tercero con un solo comando.

---

## Del dato al indicador y a la plataforma

Las fases no son independientes: forman una cadena donde **cada eslabón
condiciona el siguiente**.

| Etapa | Fase | Entrada | Salida | Efecto en las demás |
|---|---|---|---|---|
| **Preparación de datos** | 1 · 2 | APIs crudas | Matriz de fuentes y campos confirmados | Define qué KPIs son **calculables** (no deseables) |
| **Indicadores** | 2 · 3 | Campos confirmados | Fórmulas + features causales | Definen qué funciones necesita la plataforma |
| **Plataforma** | 4 | Fórmulas + features | Módulos y secciones | Materializa los KPIs en pantalla |
| **Validación** | 5 | Producto en marcha | Métricas y *fallback* | Corrige datos (retira features), código y fuentes |
| **Comunicación** | 6 | Versión validada | Presentación y repo | Cierra el ciclo y lo hace reproducible |

**Ejemplo de la cadena completa.** Un campo de la fase 1 (`grid`) se convierte en
una feature del modelo en la fase 3; esa feature produce un indicador (`posicion
predicha`) en la fase 4; su calidad se mide con el MAE en la fase 5; y el MAE se
presenta como evidencia en la fase 6. Si en la fase 1 se hubiera asumido que
`grid` existía sin comprobarlo, el indicador entero habría sido irrealizable.

**Ejemplo del lazo de retorno.** El `401` de OpenF1 (fase 5) obligó a volver a la
fase 1 para encontrar otra fuente (`/laps` + `/pitstops` de Jolpica) y a la fase
4 para construir `historial.py`. Los indicadores (fase 2) no cambiaron: siguen
siendo "tiempo medio por stint" y "mejor vuelta". Solo cambió la procedencia del
dato. Esa es precisamente la ventaja de haber definido los indicadores **antes**
de la plataforma.
