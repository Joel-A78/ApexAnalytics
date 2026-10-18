# Paleta de gráficos — Apex Analytics · F1

Especificación de los colores de las visualizaciones del Historial, con la
justificación de cada decisión y el criterio para elegir la dimensión de color.

---

## 1. El problema

El Timeline de stints y la dispersión *pace por stint* coloreaban por **compuesto
de neumático** con la paleta Pirelli. Cuando la fuente no publica el compuesto
(Jolpica, usada como respaldo), todos los valores llegan como `UNKNOWN` → **todas
las series salían del mismo gris `#6E6E76`**. Los gráficos se volvían ilegibles:
no se distinguían ni los pilotos ni los stints.

Además, la leyenda se construía con `f"{piloto} · {compuesto}"`, generando **una
entrada por stint** y repitiendo el mismo piloto tres veces
("Carlos Sainz · UNKNOWN", "Carlos Sainz · UNKNOWN", "Carlos Sainz · UNKNOWN").

---

## 2. Principio: una dimensión de color, según el dato disponible

| Situación | Dimensión de color | Paleta |
|---|---|---|
| El compuesto **está** disponible (OpenF1) | Compuesto | **Pirelli** (semántica de dominio) |
| El compuesto **no está** (Jolpica) | Timeline → **nº de stint** · Dispersión → **piloto** | Stint (secuencial) · Equipo (F1) |

La regla es explícita en el código (`_compounds_known()`): basta **un** stint con
compuesto real para activar la paleta Pirelli. Solo si **todos** son `UNKNOWN` se
cambia a la dimensión alternativa. La interfaz lo declara con un `st.caption`.

---

## 3. Paleta Pirelli — cuando el compuesto está disponible

| Compuesto | Color | Hex | Significado |
|---|---|---|---|
| Soft | 🔴 Rojo | `#E10600` | Máximo agarre, mínima duración |
| Medium | 🟡 Amarillo | `#FFD500` | Compromiso |
| Hard | ⚪ Blanco | `#FFFFFF` | Máxima duración |
| Intermediate | 🟢 Verde | `#00B050` | Pista húmeda ligera |
| Wet | 🔵 Azul | `#1E90FF` | Lluvia intensa |
| Unknown | ⚫ Gris | `#6E6E76` | Sin dato |

**Por qué:** es la convención real de la F1. El usuario no aprende una leyenda
nueva; reconoce el color porque es el del neumático.

**Contraste del texto interior:** blanco sobre rojo/verde/azul y sobre el gris;
negro sobre amarillo y blanco. Se decide por compuesto, no por algoritmo.

---

## 4. Paleta por número de stint — Timeline sin compuesto

Paleta **secuencial** (índigo → violeta → rosa → teal → naranja) que muestra la
**progresión de la estrategia** aunque falte el compuesto.

| Stint | Color | Hex |
|---|---|---|
| S1 | Índigo | `#4C6EF5` |
| S2 | Violeta | `#9775FA` |
| S3 | Rosa | `#F06595` |
| S4 | Teal | `#20C997` |
| S5 | Naranja | `#FFA94D` |
| S6 | Menta | `#63E6BE` |

La etiqueta interior del bar pasa de la letra del compuesto (`S`, `M`, `H`) a la
del stint (`S1`, `S2`, `S3`), de modo que el color y el texto informen lo mismo.

**Por qué no reutilizar los colores Pirelli:** confundiría la semántica. Si el
bar es rojo, el usuario asumiría "compuesto blando"; con esta paleta queda claro
que el color significa **orden de stint**, no tipo de goma.

---

## 5. Paleta por equipo — Dispersión sin compuesto

Cuando falta el compuesto, la dispersión colorea **por piloto** usando el color
oficial de su equipo. Es la dimensión más útil para comparar (¿quién es más
rápido en media? ¿quién tiene mejor vuelta?).

| Equipo | Hex |
|---|---|
| Red Bull | `#3671C6` |
| Ferrari | `#E8002D` |
| Mercedes | `#27F4D2` |
| McLaren | `#FF8000` |
| Aston Martin | `#229971` |
| Alpine | `#FF87BC` |
| Williams | `#64C4FF` |
| RB / Racing Bulls | `#6692FF` |
| Sauber / Stake / Kick | `#52E252` |
| Haas | `#B6BABD` |
| *Desconocido* | Paleta de respaldo de 12 colores |

La resolución es tolerante: se busca por subcadena del nombre del equipo, así que
"Kick Sauber" y "Sauber" resuelven al mismo color. Si el equipo no se reconoce, se
asigna un color de una lista de respaldo por índice, garantizando que **dos pilotos
nunca compartan color** dentro de la misma vista.

---

## 6. Correcciones de la leyenda

| Antes | Ahora |
|---|---|
| Una entrada por stint → piloto repetido 3 veces | Una entrada por **dimensión** (`legendgroup` + `showlegend` solo en la primera) |
| Título "Carlos Sainz · UNKNOWN" | Título "Carlos Sainz" (sin el sufijo inútil) |
| Sin título de leyenda | Título "Compuesto" o "Piloto" según el modo |
| — | `st.caption` que declara qué representa el color |

---

## 7. Accesibilidad y contraste

| Aspecto | Decisión |
|---|---|
| Fondo de gráfico | `#0A0A0A` (negro) constante en todos los gráficos |
| Texto sobre fondo | `#FFFFFF` (contraste ≈19:1, muy por encima del mínimo AA de 4.5:1) |
| Texto de ejes | `#8A92A6` sobre `#0A0A0A` (≈7:1) |
| Rejilla | `#1F1F1F`, sutil para no competir con los datos |
| Borde de marcador | `#0A0A0A` de 1.5 px: separa marcas solapadas sin usar relleno |
| Codificación redundante | El color **nunca** es el único canal: hay leyenda, etiqueta interior y *tooltip* |
| Tamaño de marcador | 10–38 px en función de las vueltas, legible en cualquier zoom |

La **codificación redundante** es deliberada: quien no distinga dos colores puede
leer la etiqueta del bar o el *tooltip*.

---

## 8. Resumen de constantes

| Constante | Uso | Nº de colores |
|---|---|---|
| `COMPOUND_COLORS_OPENF1` | Color por compuesto (modo primario) | 6 |
| `STINT_COLORS` | Color por número de stint (timeline, respaldo) | 6 |
| `TEAM_COLORS` | Color por equipo (dispersión, respaldo) | 10 |
| `DRIVER_FALLBACK_COLORS` | Respaldo si el equipo no se reconoce | 12 |
