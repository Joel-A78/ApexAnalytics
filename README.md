# � Supplier Plant Performance Intelligence

Proyecto de análisis de datos para una planta proveedora automotriz ubicada en Tijuana, Baja California, que exporta componentes a Estados Unidos. El objetivo es transformar datos operativos en información útil para mejorar la eficiencia, la calidad, la confiabilidad del proceso y la entrega a clientes.

## 🎯 Contexto del caso de negocio

En una planta automotriz de manufactura avanzada, la competitividad depende de tres factores clave:

- producir volumen con consistencia,
- cumplir especificaciones de calidad,
- entregar a tiempo a clientes internacionales.

Cualquier pérdida de eficiencia, retrabajo, paro de línea, falta de material o demora en entrega puede afectar directamente la rentabilidad y la relación con el cliente. Por eso, este proyecto simula un ambiente de manufactura que requiere análisis ejecutivo para detectar riesgos antes de que se vuelvan críticos.

## 🧩 Problema que resuelve

Una planta proveedora automotriz necesita monitorear el desempeño global de sus operaciones para responder preguntas críticas como:

- ¿Qué líneas están perdiendo capacidad?
- ¿Qué causas están generando scrap y retrabajo?
- ¿Cuál es el nivel real de OEE por turno o por estación?
- ¿Qué máquinas presentan más paros o tiempos muertos?
- ¿Existe riesgo de faltante de inventario o exceso de stock?
- ¿Qué clientes y proveedores están afectando la entrega final?

El proyecto responde a este problema mediante un dashboard que consolida indicadores clave de producción, calidad, inventario, mantenimiento y logística para apoyar la toma de decisiones operativas.

## 📊 Objetivos del proyecto

1. Identificar pérdidas de eficiencia operativa.
2. Detectar defectos y oportunidades de mejora en calidad.
3. Medir el impacto de paros y tiempos muertos.
4. Monitorear inventario y riesgo de abastecimiento.
5. Evaluar cumplimiento de entrega (OTIF) y retrasos logísticos.
6. Generar una vista ejecutiva para líderes de producción, calidad y supply chain.

## ❓ Preguntas de negocio

- ¿Qué líneas tienen menor rendimiento y mayor pérdida de disponibilidad?
- ¿Cuál es la causa principal de scrap y retrabajo?
- ¿Qué máquinas tienen más paros y cuánta capacidad se pierde por día?
- ¿Qué proveedores presentan mayor riesgo de faltante o demora?
- ¿Cuánto inventario está por debajo del nivel mínimo de seguridad?
- ¿Qué clientes presentan mayor riesgo de atraso de entrega?
- ¿Dónde deberíamos actuar primero para mejorar OEE y calidad?

## 📈 KPIs principales

### Operación y productividad
- OEE (Overall Equipment Effectiveness)
- Disponibilidad
- Rendimiento
- Cumplimiento de plan vs producción real
- Tiempo muerto por máquina o línea
- Costo por unidad

### Calidad
- Scrap %
- Retrabajo %
- Defectos por tipo
- DPMO / PPM
- Unidades buenas vs no conformes

### Mantenimiento
- MTBF
- MTTR
- Paros por máquina
- Minutos perdidos por causa
- Disponibilidad por turno

### Inventario y supply chain
- Stock promedio por material
- Inventario crítico
- Stock de seguridad
- OTIF (On Time In Full)
- Días de cobertura
- Riesgo de faltante

## 🗂️ Estructura sugerida de datos

El proyecto simula un entorno industrial real con datos transaccionales de producción, mantenimiento, calidad e inventario.

### Tabla de producción
- date
- line
- shift
- machine
- product
- plan
- produced
- good_units
- scrap_units
- downtime_min
- oee

### Tabla de calidad
- date
- line
- station
- defect_type
- defect_count
- scrap_units
- root_cause
- supplier

### Tabla de mantenimiento
- date
- machine
- downtime_min
- failure_type
- maintenance_type
- mtbf
- mttr

### Tabla de inventario
- date
- material
- supplier
- stock
- safety_stock
- days_coverage
- lead_time
- risk_level

### Tabla de entregas / logística
- date
- customer
- order_id
- delivery_due_date
- actual_delivery_date
- otif
- delay_days
- ship_mode

## 📊 Dashboards recomendados

### 1. Executive Overview
- OEE global
- cumplimiento de plan
- scrap total
- OTIF por cliente
- inventario crítico
- tendencia operacional mensual

### 2. Productivity by Line
- producción real vs. plan por línea
- paros por estación
- disponibilidad por turno
- capacidad perdida por motivo

### 3. Quality Dashboard
- defectos por tipo
- scrap por línea
- Pareto de causas raíz
- defectos por proveedor o proceso

### 4. Maintenance & Downtime
- minutos perdidos por máquina
- tiempo medio de falla
- fallas recurrentes
- MTTR/MTBF

### 5. Inventory & Supply Chain Risk
- stock vs seguridad
- riesgo de faltante
- OTIF por proveedor
- lead time y cobertura

## 🔬 Análisis con SQL / Python

### Ejemplos de análisis SQL

```sql
SELECT
  line,
  AVG(oee) AS oee_promedio,
  SUM(scrap_units) AS scrap_total,
  SUM(produced) AS unidades_producidas
FROM production_data
GROUP BY line
ORDER BY oee_promedio ASC;
```

```sql
SELECT
  defect_type,
  SUM(scrap_units) AS unidades_rechazadas
FROM quality_data
GROUP BY defect_type
ORDER BY unidades_rechazadas DESC;
```

```sql
SELECT
  supplier,
  AVG(otif) * 100 AS otif_pct,
  AVG(days_coverage) AS cobertura_dias
FROM inventory_data
GROUP BY supplier;
```

### Ejemplos de análisis en Python

```python
# Cálculo de OEE
authorized_time = df["available_time"]
actual_rate = df["produced"] / df["run_time"]
quality_rate = df["good_units"] / df["produced"]

oee = (availability * performance * quality_rate)
```

```python
# Pareto de defectos
defect_summary = (
    df.groupby("defect_type")["scrap_units"].sum()
      .sort_values(ascending=False)
)
```

```python
# Riesgo de inventario
df["risk_level"] = np.where(
    df["stock"] < df["safety_stock"],
    "alto",
    "normal",
)
```

## 📊 Visualizaciones recomendadas en Power BI

- KPI cards para OEE, scrap, OTIF e inventario crítico
- gráficos de línea para producción vs plan
- barras por línea para scrap y disponibilidad
- Pareto para defectos principales
- mapa de calor por turno y máquina
- gráficos de cascada para pérdidas por causa
- tablas dinámicas por cliente, proveedor y línea

## ✅ Recomendaciones accionables para una planta

1. Priorizar líneas con menor OEE y mayor tiempo muerto.
2. Ejecutar análisis Pareto de defectos por estación y tipo de falla.
3. Reducir MTTR con mantenimiento preventivo en máquinas críticas.
4. Ajustar stock mínimo y seguridad para materiales de alto riesgo.
5. Establecer alertas de OTIF para clientes críticos.
6. Crear reuniones semanales de operación con producción, calidad y compras.
7. Traducir hallazgos a proyectos de mejora continua (Kaizen, 5S, RCA).

## 🚀 Cómo correr este proyecto

```bash
# 1. Clonar el repositorio
git clone <tu-repo-url>
cd Car project

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la app
streamlit run app.py
```

## 🏗️ Estructura del proyecto

```text
Car project/
├── app.py
├── README.md
├── requirements.txt
├── assets/
│   └── style.css
├── data/
│   └── raw/
├── src/
│   ├── __init__.py
│   ├── categories.py
│   ├── data_loader.py
│   ├── cleaning.py
│   ├── degradation.py
│   ├── strategy_sim.py
│   ├── regulations.py
│   └── endurance/
├── notebooks/
└── .venv/
```

## 🏁 ¿Por qué este proyecto funciona para portafolio?

Porque combina tres elementos clave que demandan empleadores en manufactura y BI:

- contexto industrial realista,
- uso de análisis de datos para decisiones operativas,
- vinculación directa con eficiencia, calidad, logística y mejora continua.

Este tipo de proyecto es especialmente valioso para perfiles en:

- manufactura
- calidad
- supply chain
- logística
- mantenimiento
- BI / analítica operativa
- mejora continua

## 📝 Cómo narrarlo en entrevistas

> Este proyecto simula una planta proveedora automotriz exportando a Estados Unidos, con foco en eficiencia operativa, calidad, inventario y cumplimiento de entrega. A través del análisis de datos de producción, defectos, mantenimiento y logística, busco detectar pérdidas de capacidad, riesgos de abastecimiento y oportunidades de mejora continua que impacten directamente la operación y la rentabilidad.

## 💡 Impacto esperado

El dashboard permite que una planta pueda responder rápidamente a preguntas estratégicas como:

- ¿qué está frenando la producción?
- ¿dónde se genera más scrap?
- ¿qué máquina requiere atención inmediata?
- ¿qué material pone en riesgo la entrega?

Todo esto convierte el proyecto en una demostración sólida de análisis de negocios aplicado a la industria automotriz de Baja California.
