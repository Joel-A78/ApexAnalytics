# 🏁 F1 Race Analytics

Dashboard de **visualizacion y prediccion de resultados en Formula 1**.

## Modulos

- `app.py`: aplicacion Streamlit principal. Cuatro secciones:
  - **Vista general**: Grandes Premios y sesiones de la semana en curso (API Jolpica).
  - **Prediccion y estrategia**: simulador de paradas en boxes segun circuito y compuesto.
  - **Telemetria y ritmo**: en construccion.
- `simulacion.py`: motor de simulacion de estrategias. Modela degradacion lineal + cliff por compuesto, evalua 1, 2 y 3 paradas, soporta Monte Carlo.

## Modelo de estrategia

Cada `Circuit` define:

| Parametro | Descripcion |
|---|---|
| `base_lap_time` | Tiempo de vuelta base del circuito (s). |
| `pit_loss` | Segundos perdidos por pasar por boxes. |
| `deg_factor` | Multiplicador de la degradacion por vuelta del compuesto. |
| `overtaking_difficulty` | 0..1 (no se usa todavia en el tiempo total, queda para undercut). |
| `safety_car_prob` | Referencia, no se usa en el simulador todavia. |

Cada `Compound` define:

| Parametro | Descripcion |
|---|---|
| `base_pace` | Delta base contra el soft (s). |
| `deg_rate` | Degradacion lineal por vuelta (s/vuelta). |
| `cliff_lap` | Vuelta a partir de la cual hay caida adicional. |
| `cliff_drop` | Caida adicional en segundos al cruzar el cliff. |
| `min_stint` | Stint minimo recomendado. |

El simulador itera vuelta a vuelta, suma tiempos y aplica `pit_loss` en las vueltas de cambio de stint. Con Monte Carlo agrega ruido gaussiano a cada vuelta.

## Estructura

```
ApexAnalytics/
├── app.py              # Dashboard Streamlit
├── simulacion.py       # Motor de simulacion de estrategias
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── assets/style.css
├── data/raw/           # Datasets locales / cache de la API Jolpica
└── src/                # Modulos auxiliares
```

## Como correr

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

O con Docker:

```bash
docker-compose up --build
```
