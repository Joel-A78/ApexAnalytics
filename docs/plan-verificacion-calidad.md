# Plan de verificación y calidad — Apex Analytics · F1

Procedimientos para comprobar **exactitud de fórmulas y totales**, **funcionamiento
de filtros**, **actualización de datos**, **legibilidad de gráficos** y **utilidad
para las decisiones del usuario**, con roles, consultas, registro de incidencias y
flujo de corrección.

> **Supuesto de equipo.** El proyecto lo trabaja un equipo de **n personas** con
> roles diferenciados, no una sola. Una persona puede cubrir varios roles, pero
> rige una regla fija: **quien verifica un artefacto no es quien lo produjo**
> (segregación de funciones).

---

## 1. Roles y responsabilidades

| Rol | Responsabilidad principal | Verifica | No decide sobre |
|---|---|---|---|
| **Analista de dominio (F1)** | Define el comportamiento esperado (reglas de compuestos, paradas, calendario) | Que el resultado “tenga sentido de F1” | Implementación técnica |
| **Analista de datos** | Valida fórmulas, totales y procedencia del dato | Exactitud e integridad | Diseño visual |
| **Científico de datos** | Entrena y evalúa el modelo | Métricas del modelo y no-fuga de datos | Fuentes ni UI |
| **Ingeniero de integración** | APIs, caché, *fallback*, *timezone* | Actualización y resiliencia | Fórmulas de negocio |
| **Desarrollador de dashboard** | Construye secciones y visualizaciones | Legibilidad y filtros | Criterios de negocio |
| **QA / Revisor independiente** | Verificación transversal | Todo lo verificable | Prioridad del producto |
| **Product Owner** | Valida utilidad y cierra el ciclo | Que el KPI cambie una decisión | Detalle técnico |

**Matriz RACI (R = ejecuta · A = aprueba · C = consultado · I = informado)**

| Actividad | Dom. | Datos | Cient. | Integr. | Dev | QA | PO |
|---|---|---|---|---|---|---|---|
| Validar fórmula de un KPI | C | **R/A** | C | I | I | C | I |
| Validar métricas del modelo | C | C | **R/A** | I | I | C | I |
| Probar *fallback* de fuente | I | C | I | **R/A** | C | **R** | I |
| Verificar filtros | C | C | I | I | **R** | **R/A** | I |
| Revisar legibilidad | C | I | I | I | **R** | **R/A** | C |
| Aceptar utilidad | **R/A** | C | C | I | I | C | **R/A** |

En equipos pequeños los roles se agrupan, pero **QA nunca coincide con el autor**
del artefacto que revisa.

---

## 2. Verificaciones por dimensión

### 2.1 Exactitud de fórmulas y totales

| Aspecto | Detalle |
|---|---|
| **Qué se verifica** | Que cada KPI se calcule como está documentado en `docs/fichas-kpi.md` y que los totales cuadren con sus partes. |
| **Quién revisa** | Analista de datos (**A**), QA independiente (**R**). |
| **Consultas / pruebas** | 1. **Recálculo manual**: se toma un caso y se calcula a mano. Ej. Bahrain 2024, Verstappen stint 1 (vueltas 1–17): `avg = mean(t₁…t₁₇)`, `best = min(t₁…t₁₇)`; debe coincidir con la tabla con 3 decimales.<br>2. **Invariantes**: `Σ laps_completed` de los stints de un piloto = vueltas válidas del piloto; `n_paradas = n_stints − 1`; `nº pit_laps` = nº de paradas reales.<br>3. **Pruebas unitarias** en `tests/`: `test_simulacion.py` (el tiempo de vuelta crece con `deg_rate`; el *cliff* solo actúa desde `cliff_lap`), `test_prediccion.py` (el MAE calculado a mano coincide), `test_historial.py` (los stints derivados igualan el conteo de la fuente).<br>4. **Contraste entre fuentes**: los stints de Jolpica deben igualar los de OpenF1 (63 vs. 63 en Bahrain 2024).<br>5. **Sanidad del modelo**: si `MAE > baseline_MAE`, se marca la corrida como sospechosa. |
| **Criterio** | Recálculo manual idéntico al mostrado · todas las invariantes verdaderas · 100 % de las pruebas unitarias en verde · diferencia entre fuentes = 0 registros · modelo supera al baseline. |
| **Evidencia** | Salida de `pytest`, tabla de contraste de fuentes, captura del recálculo manual. |

### 2.2 Funcionamiento de filtros

| Aspecto | Detalle |
|---|---|
| **Qué se verifica** | Que cada control cambie **exactamente** lo que debe cambiar y nada más. |
| **Quién revisa** | Desarrollador (**R**), QA (**A**). |
| **Consultas / pruebas** | 1. **Filtro de sectores**: al elegir “Solo S1”, S2 y S3 quedan atenuados; el conjunto atenuado debe ser el complementario exacto (`{S2,S3}`).<br>2. **Multiselección de pilotos**: en la tabla y los gráficos deben aparecer **solo** las claves seleccionadas.<br>3. **Selectores de temporada y carrera**: cambiar la ronda debe cambiar resultados, pilotos y stints.<br>4. **Prueba automatizada**: `AppTest` fija el valor del *widget* y luego se afirma sobre el resultado:<br>`at.selectbox[0].set_value("Solo S1").run()` → `assert set(atenuados) == {"S2","S3"}`<br>`at.multiselect[0].set_value([k1,k2]).run()` → `assert set(df.Piloto) ⊆ {k1,k2}` |
| **Criterio** | Para cada filtro, el conjunto resultante es **exactamente** el esperado (ni de más ni de menos); ningún *widget* deja la vista sin datos de forma inesperada. |
| **Evidencia** | Casos de prueba en `AppTest` + captura del estado con y sin filtro. |

### 2.3 Actualización de datos

| Aspecto | Detalle |
|---|---|
| **Qué se verifica** | Que los datos se refresquen cuando corresponde y que el sistema no muestre información vencida. |
| **Quién revisa** | Ingeniero de integración (**R/A**), QA (**R**). |
| **Consultas / pruebas** | 1. **Políticas de caché**: calendario y clima 30 min; modelo y sesiones 24 h; el botón *Actualizar* limpia la caché del calendario.<br>2. **Cambio de carrera**: se inyecta una fecha posterior al día de carrera y se comprueba que `get_next_race()` devuelve la siguiente, no la pasada.<br>3. **Carrera en curso**: con la fecha dentro del fin de semana, debe devolver **esa** carrera.<br>4. **Cambio de temporada**: el `season` va como argumento de la función de caché, de modo que el 1 de enero la clave cambia y no se sirve el año anterior.<br>5. **Resiliencia**: se simula un `401` de OpenF1 y se comprueba que la app conmuta a Jolpica y muestra el origen en pantalla. |
| **Criterio** | Ninguna vista muestra datos fuera de su ventana de vigencia · el cambio de ronda/año produce datos nuevos · ante caída de la fuente primaria, la app sigue operativa con la de respaldo y lo indica. |
| **Evidencia** | Log del contenedor, salida de las pruebas con fecha inyectada, captura del badge de fuente. |

### 2.4 Legibilidad de gráficos

| Aspecto | Detalle |
|---|---|
| **Qué se verifica** | Que cualquier usuario pueda leer un gráfico sin explicación previa. |
| **Quién revisa** | Desarrollador (**R**), QA (**A**), Analista de dominio (**C**). |
| **Consultas / pruebas** | *Checklist* por gráfico:<br>☐ Título descriptivo · ☐ Ejes rotulados **con unidad** (“Tiempo de vuelta (s)”, “Vuelta”) · ☐ Leyenda presente cuando hay ≥2 series · ☐ Colores con contraste suficiente sobre fondo oscuro (blanco sobre `#0A0A0A` ≈ 19:1) · ☐ Etiquetas sin truncar (`…`) · ☐ *Tooltip* con valores exactos · ☐ Sin solapamiento de marcas · ☐ Paleta de compuestos consistente con su convención (rojo=soft, amarillo=medium, blanco=hard, verde=intermedio, azul=mojado).<br>Además, prueba de contraste y de tamaño mínimo de fuente (≥10 px efectivos). |
| **Criterio** | Ningún “☐” en falso · todo eje con unidad explícita · ningún texto cortado · la paleta coincide con la convención de dominio. |
| **Evidencia** | Lista de verificación firmada + capturas en resolución objetivo (escritorio y móvil). |

### 2.5 Utilidad para las decisiones del usuario

| Aspecto | Detalle |
|---|---|
| **Qué se verifica** | Que cada KPI **cambie una decisión** concreta y no sea un número decorativo. |
| **Quién revisa** | Product Owner (**A**), Analista de dominio (**R**). |
| **Consultas / pruebas** | 1. **Trazabilidad KPI→decisión**: cada indicador de `docs/fichas-kpi.md` declara su decisión; se confirma una a una.<br>2. **Prueba de sensibilidad**: si se cambia el ruido de Monte Carlo, ¿cambia la estrategia recomendada? Si **no cambia nunca**, el KPI no discrimina.<br>3. **Prueba de margen**: si la diferencia entre la 1.ª y 2.ª estrategia es < 1 s, la interfaz debe advertir que la decisión es ajustada.<br>4. **Recorrido heurístico**: un usuario nuevo, sin ayuda, debe llegar a interpretar la recomendación; se mide si lo logra y en cuánto tiempo.<br>5. **Caso de uso real**: se verifica que el sistema proponga una estrategia distinta entre un circuito de alta y otra de baja degradación. |
| **Criterio** | El 100 % de los KPIs tiene una decisión asociada y no redundante · al menos un escenario cambia la recomendación · el usuario interpreta la recomendación sin asistencia. |
| **Evidencia** | Ficha KPI + registro del recorrido heurístico + comparativa de dos circuitos. |

---

## 3. Registro de incidencias

Toda desviación detectada (en cualquier fase) se registra con una **plantilla
única** antes de corregirse. El tablero es la fuente de verdad: si no está
registrado, no existe.

| Campo | Contenido |
|---|---|
| **ID** | `INC-###` correlativo |
| **Fecha** | Alta de la incidencia |
| **Fase** | Empatizar · Definir · Idear · Prototipar · Evaluar · Presentar |
| **Dimensión** | Fórmulas · Filtros · Actualización · Legibilidad · Utilidad |
| **Severidad** | S1 bloqueante · S2 mayor · S3 menor · S4 cosmético |
| **Descripción** | Qué se esperaba y qué ocurrió |
| **Evidencia** | Log, captura, traza o consulta que lo reproduce |
| **Reporta / Asignado** | Quién la detecta (≠ quién corrige) |
| **Estado** | Abierta · En corrección · En verificación · Cerrada · Descartada |
| **Corrección** | Commit o cambio aplicado |
| **Verificación** | Quién la re-valida y con qué prueba |

**Severidades**

| Nivel | Significado | Plazo objetivo |
|---|---|---|
| **S1 Bloqueante** | Impide usar una sección o da un dato incorrecto | Corregir antes de cualquier entrega |
| **S2 Mayor** | Funciona con un resultado equivocado o engañoso | Siguiente incremento |
| **S3 Menor** | Afecta la experiencia sin alterar el dato | Se planifica |
| **S4 Cosmético** | Solo presentación | Se agrupa por *release* |

**Incidencias reales del proyecto (ejemplos del registro)**

| ID | Fase | Dimensión | Sev. | Descripción | Corrección |
|---|---|---|---|---|---|
| INC-001 | Prototipar | Actualización | S1 | `KeyError: 'meeting_name'` al cargar sesiones (el campo no existe en `/sessions`). | Se usa `/meetings` y degradación al nombre del circuito. |
| INC-002 | Prototipar | Fórmulas | S1 | `AttributeError: 'Circuit' object has no attribute 'typical_laps'` en runtime. | Se completó el dataclass y se recargó el contenedor. |
| INC-003 | Evaluar | Actualización | S2 | El mapa de Raceweek no rotaba de carrera al pasar el día de GP. | `get_next_race()` considera el fin de semana en curso; caché con clave por año. |
| INC-004 | Evaluar | Fórmulas | S2 | `"Madrid"` duplicado 3 veces en el catálogo de circuitos. | Se eliminaron los duplicados. |
| INC-005 | Evaluar | Actualización | S1 | OpenF1 devolvió `401` y dejó Historial sin datos. | Plan B: respaldo Jolpica + capa `historial.py`. |
| INC-006 | Evaluar | Legibilidad | S3 | El video de fondo capturaba el *scroll*. | `pointer-events: none` en el elemento de video. |
| INC-007 | Idear | Fórmulas | S3 | `circuit_avg` / `recent_form` no aportaban al modelo. | Ablación → retiro de la feature (el podio mejoró de 76.4 % a 77.8 %). |

---

## 4. Flujo de corrección

```
1. DETECTAR   Cualquier rol reproduce el problema y captura evidencia
      │
2. REGISTRAR  Se abre INC-### con la plantilla (severidad + responsable)
      │
3. TRIAGE     Datos/QA asignan severidad y prioridad; PO si afecta al alcance
      │
4. CORREGIR   El asignado arregla en una rama; un commit por incidencia
      │
5. RE-VERIFICAR  OTRA persona reproduce la prueba del "Criterio" y confirma
      │
6. CERRAR     Se adjunta evidencia de la verificación; estado = Cerrada
      │
7. PREVENIR   Si es sistémico, se añade prueba unitaria o se reabre la
              fase correspondiente de Design Thinking
```

**Reglas del flujo**

1. **Nadie cierra su propia incidencia.** La re-verificación (paso 5) la firma
   alguien distinto del autor.
2. **Toda incidencia S1 o S2 deja una prueba automatizada** que la habría
   detectado (regresión). Ej.: INC-005 dejó la comparación de conteos entre
   fuentes; INC-003 dejó el caso con fecha inyectada.
3. **Lo sistémico no se parcha.** Si la causa es una brecha de proceso, se
   devuelve el proyecto a la fase de Design Thinking que corresponda (el `401`
   devolvió a Empatizar y Prototipar, no solo a corregir código).
4. **Trazabilidad.** La corrección se enlaza al commit y la incidencia queda
   cerrada con su evidencia.

---

## 5. Cadencia de revisión

| Ritual | Frecuencia | Quién | Qué se revisa |
|---|---|---|---|
| **Auto-revisión** | Antes de cada commit | Autor | Los 5 *checklists* de la sección 2 |
| **Puerta de integración** | Por incremento | Autor + QA | `AppTest`: 4/4 secciones sin errores; contenedor *healthy* |
| **Revisión de datos** | Semanal | Analista de datos + dominio | Fórmulas, totales e invariantes |
| **Revisión de modelo** | Por evaluación | Científico de datos + QA | MAE vs. baseline, no-fuga, ablación |
| **Aceptación de producto** | Fin de fase | Product Owner | Utilidad para la decisión |
| **Cierre de fase** | Por hito | QA independiente | Criterios de la fase en `plan-design-thinking.md` |

---

## 6. Evidencia y trazabilidad

1. **Un criterio sin prueba no es un criterio.** Todo lo verificable de la
   sección 2 tiene una consulta, un caso de prueba o una lista de verificación
   firmada.
2. **Reproducibilidad.** Las pruebas se ejecutan desde cero (`docker compose up`,
   `pytest`) para que cualquier miembro las repita sin contexto previo.
3. **Doble firma.** Los artefactos críticos (fórmulas y modelo) llevan la firma
   del autor y del revisor independiente.
4. **Historial.** El tablero de incidencias y los *commits* forman el registro
   auditable del proyecto.
