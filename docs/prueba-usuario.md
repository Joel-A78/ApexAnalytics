# Prueba de usuario — Apex Analytics · F1

Simulación de uso real: se plantean consultas concretas, se ejecutan contra la
aplicación, se registra lo observado, el comentario del usuario, el ajuste
aplicado y la comprobación posterior.

> **Alcance.** La simulación la ejecuta el equipo de desarrollo asumiendo el rol
> de usuario. Las pruebas que requieren percepción visual humana o varias
> personas reales se declaran **pendientes** al final.

**Entorno:** contenedor `apexanalytics-app` · `http://localhost:8501` ·
fecha de prueba 17 oct 2026 · zona `America/Tijuana`.

---

## Tabla de prueba

| Tarea de prueba | Observación / comentario | Ajuste y nueva prueba |
|---|---|---|
| **T1.** «¿Qué carrera hay esta semana y cuándo es la próxima?» | El KPI *Eventos esta semana* muestra **0** y *Próxima carrera* **United States Grand Prix** con cuenta regresiva de **8 días** (COTA, 2026-10-25). *Comentario:* "Entiendo que esta semana no hay carrera y que la siguiente es en 8 días; el dato es claro." | **Sin ajuste.** La vista ya distingue "eventos de esta semana" de "próxima carrera". **Nueva prueba:** se verificó que con la semana vacía aparece el mensaje *"No hay Grandes Premios esta semana"* y se mantienen los KPIs. ✔ |
| **T2.** «¿Cuál es la mejor estrategia para la próxima carrera?» | Para COTA: **1 parada S-M**, tiempo **1:29:53**, pit en la vuelta **25**, desviación Monte Carlo **0.70–0.81 s** y margen frente a la 2.ª estrategia de **0.48–0.87 s**. *Comentario:* "El margen es menor a 1 segundo; no sé si la decisión es robusta o si da igual cualquiera de las dos." | **Ajuste aplicado:** se añadió un aviso automático cuando el margen es **< 1 s**: *"Margen ajustado (<1 s): la eleccion es sensible a la variabilidad. Revisa la desviacion Monte Carlo antes de fijar el plan."* **Nueva prueba:** el aviso aparece con margen 0.87 s y desaparece con márgenes amplios. ✔ |
| **T3.** «¿Cómo fue el ritmo de Verstappen por stint en Bahréin 2024?» | **Dos defectos reales.** (1) La carrera aparecía como **"R9472"** porque se usaba el `meeting_key` de OpenF1 como número de ronda. (2) El piloto aparecía como **"Max VERSTAPPEN"** (OpenF1) frente a "Max Verstappen" (Jolpica). *Comentario:* "La ronda no tiene sentido y el nombre cambia de formato según la sección." | **Ajustes aplicados:** (1) la ronda se deriva del **orden cronológico** (1–24); (2) se normaliza el nombre con `_normalize_name()` conservando las palabras ya capitalizadas. **Nueva prueba:** la carrera muestra **"R1 · Australian Grand Prix · 2025-03-16"** y el piloto **"Max Verstappen"**. Datos: S1 1–17 (17 vueltas, media 97.19 s), S2 18–37 (19, 95.77), S3 38–57 (19, 94.69). ✔ |
| **T4.** «¿Quién es el favorito al podio según el modelo?» | MAE **3.193** vs baseline **3.344**; acierto de podio **77.8 %** vs 75.0 %. En la última ronda evaluada el top-3 predicho fue Norris (P3.5), Verstappen (P3.7) y Piastri (P4.0). *Comentario:* "Veo que el modelo supera al baseline, pero quiero saber cuánto mejora." | **Sin ajuste:** la vista ya muestra el MAE junto al baseline y la diferencia se explica en el texto inferior. **Nueva prueba:** se confirma que el KPI de error incluye el valor del baseline como delta. ✔ |
| **T5.** «¿Cuáles fueron los resultados de la ronda 5 de 2026?» | Seleccionando la ronda 5 aparecen **22 resultados** con podio **Antonelli (Mercedes), Hamilton (Ferrari), Verstappen (Red Bull)**. *Comentario:* "Funciona, pero no sabía que podía llegar a este detalle desde el calendario de Raceweek." | **Ajuste aplicado:** el calendario ahora tiene tarjetas-enlace con la CTA *"Ver resultados"* al pasar el cursor y un texto de ayuda encima de la rejilla. **Nueva prueba:** al pulsar una tarjeta se abre Temporada con la temporada y ronda preseleccionadas y los resultados cargados. ✔ |
| **T6.** «Quiero ver los resultados de una carrera desde el calendario.» | El enlace generado es `?section=season&season=2026&round=5`; al abrirlo, los selectores quedan en **Temporada 2026** y **Ronda 5** y se muestran los resultados y el campeonato acumulado. *Comentario:* "La navegación es directa y no tengo que buscar la carrera otra vez." | **Sin ajuste adicional.** Se verificó que los parámetros de URL se limpian después de aplicarse (no se re-aplican al navegar con el sidebar). **Nueva prueba:** tras cambiar de sección con el sidebar, la app no vuelve a forzar la ronda. ✔ |

---

## Cambios derivados de la prueba

| Archivo | Cambio | Motivo |
|---|---|---|
| `historial.py` | Ronda cronológica (1–24) en lugar de `meeting_key` | T3 |
| `historial.py` | `_normalize_name()` para unificar mayúsculas | T3 |
| `app.py` | Aviso de margen ajustado (< 1 s) | T2 |
| `app.py` | CTA y texto de ayuda en el calendario | T5 |

**Verificación final:** las 4 secciones (Raceweek, Temporada, Simulacion,
Historial) renderizan **sin errores ni excepciones**.

---

## Pruebas pendientes (declaradas)

| Prueba | Por qué está pendiente | Cómo se cerrará |
|---|---|---|
| **Legibilidad visual de los gráficos** | Requiere inspección humana a tamaño real (contraste, solapamiento, tipografías) | Revisión con la lista de verificación de `plan-verificacion-calidad.md` §2.4 sobre capturas en escritorio y móvil |
| **Diseño responsive / móvil** | No se puede validar sin dispositivo o emulación real | Prueba en viewport ≤ 700 px y tableta |
| **Accesibilidad con lector de pantalla** | Requiere tecnología de asistencia | Recorrido con NVDA/VoiceOver sobre el sidebar y los filtros |
| **Concurrencia multiusuario** | La simulación es de una sola sesión | Prueba con ≥ 3 sesiones simultáneas y verificación de caché |
| **Recuperación ante caída de OpenF1 en producción** | El `401` fue transitorio durante el desarrollo | Simular el fallo y medir el tiempo de conmutación a Jolpica y el aviso en pantalla |
| **Validación con usuarios reales** | Esta prueba fue una simulación de rol | Sesión con 3–5 usuarios externos y registro de comentarios |

---

## Evidencia de ejecución

```
T1  hoy 2026-10-17 · próxima United States GP · 2026-10-25 · 8 días
T2  COTA · 1-stop S-M · 1:29:53 · pit [25] · std MC 0.70 s · margen 0.87 s
T3  ronda 1 · Max Verstappen · S1 97.19 · S2 95.77 · S3 94.69
T4  MAE 3.193 (baseline 3.344) · podio 77.8 % (baseline 75.0 %)
T5  ronda 5 2026 · 22 resultados · P1 Antonelli · P2 Hamilton · P3 Verstappen
T6  ?section=season&season=2026&round=5 → Temporada 2026 / Ronda 5
AppTest: 4/4 secciones sin errores ni excepciones
```
