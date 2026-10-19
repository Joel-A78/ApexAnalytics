# Estructura del dashboard — Apex Analytics · F1

Descripción de cómo está organizada la aplicación: contenedores globales, secciones,
jerarquía interna y flujo de navegación.

---

## 1. Estructura global

La aplicación se divide en **tres contenedores permanentes**:

| Contenedor | Ubicación | Contenido |
|---|---|---|
| **Sidebar** | Columna izquierda fija | Logo Apex, rótulo "SECCIONES", cuatro botones de navegación, divisor y datos de sesión (zona horaria y lema) |
| **Área principal** | Centro | Contenido de la sección activa |
| **Footer** | Final del scroll, en todas las secciones | Créditos y fuentes + barra de interés de usuarios |

### Sidebar

1. **Logo** (`assets/media/ApexAnalytics logo letras.png`), embebido en base64.
2. **"SECCIONES"**: rótulo en monoespaciada con línea degradada.
3. **Navegación numerada**:
   - `01 Raceweek` → `overview`
   - `02 Temporada` → `season`
   - `03 Simulacion` → `prediction`
   - `04 Historial` → `telemetry`
4. **Pie**: `Formula 1 · 2026 · HH:MM America/Tijuana` y `Data drives victory.`

Cada botón conserva el mismo tamaño en reposo, hover y activo; el estado activo solo
cambia el color de su acento y el borde izquierdo.

### Footer (transversal)

- **Créditos**: Jolpica/Ergast (calendario y resultados), OpenF1 (telemetría, con
  Jolpica como respaldo), Open-Meteo (clima), referencias FIA y Formula 1.
- **Interés de usuarios**: vistas totales, secciones exploradas, minutos de sesión,
  vistas por minuto y un chip por sección visitada.

---

## 2. Sección Raceweek (`overview`)

Responde: *¿qué se corre esta semana y cuál es el contexto de la próxima carrera?*

```
Encabezado (PIT WALL · Eventos de la semana)
├── Barra superior: Semana en curso | Hoy (Tijuana) | [Actualizar]
├── Fila de 4 KPIs
│   ├── Eventos esta semana
│   ├── Carreras en la temporada
│   ├── Próxima carrera (+ fecha)
│   └── Cuenta regresiva (+ país)
├── Eventos de la semana (tarjetas de sesión o estado vacío)
├── Datos geométricos · [Gran Premio]
│   ├── Columna izquierda: tarjeta de clima
│   │   ├── Clima actual (temperatura, descripción, viento)
│   │   ├── 6 estadísticas (sensación, humedad, rachas, presión, nubosidad, precipitación)
│   │   ├── Condiciones de carrera (riesgo de lluvia y temperatura de pista)
│   │   └── Pronóstico de 3 días
│   └── Columna derecha: mapa del circuito
│       ├── Filtros: sector · mostrar curvas · pantalla completa
│       ├── SVG con sectores coloreados y curvas numeradas
│       └── Caption del modo de color
├── Calendario de la temporada
│   └── Timeline horizontal de tarjetas enlazadas a Temporada
└── Footer
```

**Modo pantalla completa:** al pulsar el botón, el mapa ocupa todo el ancho, la
tarjeta de clima se oculta y aparece el botón **Salir**. El modo se reinicia al
cambiar de sección.

---

## 3. Sección Temporada (`season`)

Responde: *¿qué pasó en una carrera concreta y cómo va el campeonato?*

```
Encabezado
├── Selectores: Temporada (año) | Ronda
├── Banner de la carrera (ronda, GP, circuito, fecha)
├── Tabla de resultados
│   └── Posición, piloto, equipo, salida, puntos, vueltas, estado, vuelta rápida
├── Campeonato acumulado
└── Footer
```

Recibe la ronda desde el calendario de Raceweek mediante parámetros de URL.

---

## 4. Sección Simulacion (`prediction`)

Responde: *¿cuál es la mejor estrategia de paradas para la próxima carrera?*

```
Encabezado
├── Tarjeta de próxima carrera (circuito y fecha, tomados de Raceweek)
├── Controles
│   ├── Circuito (preseleccionado, editable)
│   ├── Vueltas totales (valor típico del circuito)
│   ├── Neumático de salida
│   ├── Simulaciones Monte Carlo
│   ├── Ruido por vuelta
│   └── Estrategias de lluvia
├── Banner de estrategia recomendada
│   └── Tiempo, paradas, ventanas de pit y chips de compuesto
├── 4 KPIs
│   ├── Tiempo estimado de estrategia
│   ├── Número de paradas
│   ├── Margen vs. 2.ª estrategia
│   └── Stints
├── Aviso de margen ajustado (< 1 s)
├── Ranking de estrategias (tabla)
├── Gráfico de tiempo por vuelta (top 3 estrategias, con líneas de pit)
└── Footer
```

---

## 5. Sección Historial (`telemetry`)

Responde: *¿cómo rindió cada piloto por compuesto y qué tan bueno es el modelo?*

```
Encabezado
├── Selector de modo (segmentado)
│   ├── Comparar pilotos (mismo año)
│   └── Train 2024 vs Eval 2025
├── Panel de filtros (contenedor con borde)
│   ├── Modo simple:     Temporada | Carrera | Pilotos
│   └── Modo train/eval: Circuito | Pilotos
├── Bloque por sesión
│   ├── Tarjeta de contexto (GP, circuito, fecha, fuente de datos)
│   ├── Ritmo por stint
│   │   ├── Caption del criterio de color
│   │   ├── Timeline de stints (barras horizontales)
│   │   └── Dispersión avg vs. best (burbujas)
│   └── Detalle de stints (tabla)
├── Predicción de resultados (KPIs del modelo)
│   ├── 4 KPIs: posición predicha, MAE, precisión, correlación
│   ├── Importancia de variables (barras)
│   ├── Distribución del error (histograma)
│   ├── Predicciones de la última carrera evaluada (tabla)
│   └── Texto de interpretación (mejora vs. baseline)
└── Footer con barra de interés
```

En el modo *Train vs. Eval* este bloque se repite dos veces, una por temporada.

---

## 6. Navegación y estado

| Mecanismo | Uso |
|---|---|
| **Botones del sidebar** | Cambian `st.session_state["nav_section"]` sin recargar la página |
| **Parámetros de URL** | El calendario de Raceweek enlaza a `?section=season&season=AÑO&round=N` y preselecciona la carrera |
| **`map_fullscreen`** | Activa el mapa a pantalla completa; se limpia al salir de Raceweek |
| **Caché** | Calendario y clima 30 min · modelo e historial 24 h |

## 7. Principio de organización

La jerarquía sigue el orden **contexto → detalle → decisión**:

1. **Raceweek** entrega el contexto temporal.
2. **Temporada** permite explorar el histórico.
3. **Simulacion** convierte el contexto en una decisión.
4. **Historial** valida el rendimiento con datos y modelo.

Cada sección repite el mismo patrón: **encabezado → filtros/controles → indicadores →
visualizaciones → detalle tabular**. Esa consistencia reduce el costo de aprendizaje y
permite al usuario saber dónde buscar cada tipo de información.
