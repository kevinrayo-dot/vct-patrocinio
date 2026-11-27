# Patrocinio VCT Américas 2027: tablero de BI en Solara

- **URL pública:** https://vct-patrocinio.onrender.com  *(cámbiela por la suya cuando Render la cree)*
- **Repositorio:** https://github.com/Rayo2995/vct-patrocinio

## 1. Pregunta de decisión

- **Quién decide:** la gerente de mercadeo de una marca colombiana de periféricos gamer.
- **Qué decide:** a cuál de los 12 equipos de la liga VCT Américas 2026 patrocinar en 2027 y cómo atar el pago al rendimiento.
- **Qué número necesita ver:** el % de series ganadas por temporada de cada equipo frente a la liga, y cuánto se espera que gane en 2027.

## 2. Datos

### Ficha

| Campo | Valor |
|---|---|
| Fuente | [vlr.gg](https://www.vlr.gg), historial público de partidas de cada equipo, p. ej. [Sentinels](https://www.vlr.gg/team/matches/2/sentinels/?group=completed). Extraído el 26/11/2026 con `scripts/extraer_vlr.js`. |
| Licencia | vlr.gg no publica una licencia abierta. Los resultados deportivos son hechos públicos; se usan con atribución y con fines académicos. Un derivado de estos datos se publica en Kaggle con licencia MIT: [Valorant Champion Tour 2021-2026 Data](https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data). |
| Archivo crudo | `datos/series_vct_americas_crudo.csv` (2 429 filas, CSV UTF-8) |
| Archivo limpio | `datos/series_limpias.csv` (2 173 filas), generado con `python datos_proyecto.py` |
| Grano | Una fila = una serie (partida al mejor de 1, 3 o 5 mapas) vista desde uno de los 12 equipos. Si dos equipos de la liga se enfrentan, la serie aparece una vez por cada uno. |
| Columnas usadas | `equipo`, `rival`, `evento`, `fase`, `marcador_equipo`, `marcador_rival`, `fecha` (columna de fecha) |
| Periodo | 2021 a noviembre de 2026 |
| Datos personales | Ninguno: solo organizaciones (equipos). No hay nombres de jugadores. |

### Limpieza (reglas en `datos_proyecto.py`, una por línea)

| Paso | Filas |
|---|---:|
| Filas leídas del CSV crudo | 2 429 |
| Duplicadas (mismo equipo y misma serie) | 0 |
| Sin marcador (forfeit o serie no jugada) | −6 |
| Showmatch (exhibición, no es competencia) | −12 |
| Fecha que no se pudo leer | 0 |
| Antes de 2021 (anterior al circuito VCT) | −236 |
| Empate en el marcador (serie sin ganador) | −2 |
| **Filas limpias** | **2 173** |

2 429 − 6 − 12 − 236 − 2 = 2 173: la bitácora cuadra (lo comprueba `tests/test_proyecto.py`).
Una de las dos filas con empate venía marcada como victoria con un marcador 1-1: por eso el resultado se recalcula desde el marcador y no se usa la columna `resultado_vlr`.

## 3. KPI

- **Fórmula:** tasa de victorias = series ganadas ÷ series jugadas × 100. Es un cociente: se **suman** las series primero y se **divide** al final (nunca se promedian porcentajes).
- **Unidad:** % de series ganadas en la temporada.
- **Línea base:** la misma tasa para los 12 equipos juntos en la misma temporada (la "liga"). Ejemplo 2026: 204 de 369 = 55,3 %.
- **Verificación por un segundo camino:** el tablero recalcula el KPI leyendo `datos/series_limpias.csv` línea por línea con el módulo `csv`, sin pandas, y muestra si coincide.
  Cifra de control: **NRG 2026 = 31 de 48 = 64,6 %** por los dos caminos.
- Segundo indicador: mapas ganados ÷ mapas jugados (también sumando primero).

## 4. Pronóstico

`prediccion.py`: regresión lineal de scikit-learn, *tasa de este año = a + b × tasa del año anterior*, con todos los equipos juntos
(solo temporadas con 10 series o más). Se entrena con 2022–2025 (38 filas) y se mide en **2026**, que el modelo no vio (12 equipos).

| | Error medio absoluto en 2026 |
|---|---:|
| Línea base: repetir la tasa del año anterior | 18,6 pts |
| Modelo | **12,6 pts** → le gana |

La pendiente (0,32) dice que solo un tercio de la ventaja de un año se mantiene al siguiente. El error sigue siendo grande: el pronóstico orienta, no promete.

## 5. Recomendación

**Patrocinar a NRG para 2027 con contrato de un año y bono por desempeño.** En 2026 ganó 31 de 48 series (64,6 %, +9,3 pts sobre la liga) y superó a la liga en las 6 temporadas, el registro más estable de los 12. La parte fija se paga pensando en el pronóstico (54,7 % para 2027), no en repetir 64,6 %; el bono se activa solo si vuelve a superar 55,3 % (la liga en 2026).

## 6. Cómo correrlo

Con Docker (lo que usa Render):

```bash
docker build -t vct-patrocinio .
docker run --rm -p 8765:8765 vct-patrocinio
```

Sin Docker (entorno `cloud2026`):

```bash
pip install -r requirements-dev.txt
python datos_proyecto.py      # imprime la bitácora y regenera datos/series_limpias.csv
python prediccion.py          # imprime el error del modelo y de la línea base
pytest -q                     # 6 pruebas
solara run app.py             # abre http://localhost:8765
```

Variable opcional: `NOMBRE_APP` (título del tablero). No hay secretos.

## 7. Proceso y uso de IA

- **Herramienta:** Claude (Anthropic), en la app de escritorio.
- **Para qué la usé:** buscar una fuente con fecha (el primer CSV que elegí, `Players.csv` de Kaggle, no tenía fecha y traía nombres de jugadores); escribir el script que extrae el historial de vlr.gg; proponer las reglas de limpieza, el KPI, el modelo y los gráficos; y redactar este README.
- **Qué cambié o decidí yo:** *(complete con lo que usted revisó, cambió y decidió. Debe poder explicar cada línea de `app.py` y de los módulos).*
- **Cómo lo verifiqué:** `pytest -q` (6 pruebas, entre ellas la bitácora y la cifra de control por un segundo camino) y revisé el tablero abierto con distintos equipos y temporadas.
