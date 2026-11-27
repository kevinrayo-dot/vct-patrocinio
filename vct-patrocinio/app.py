"""Tablero de BI: ¿a qué equipo de VCT Américas patrocinar en 2027?"""
import os

import matplotlib.pyplot as plt
import pandas as pd
import solara

import graficos
import indicadores as kpi
from datos_proyecto import LIMPIO, bitacora_cuadra, cargar_crudo, equipos, limpiar, temporadas
from prediccion import evaluar, pronostico_siguiente

NOMBRE = os.environ.get("NOMBRE_APP", "Patrocinio VCT Américas 2027")

# --- Datos: se limpian una sola vez al arrancar el servidor ---------------------------------
datos, bitacora = limpiar(cargar_crudo())
evaluacion = evaluar(datos)  # modelo medido en la última temporada, que no vio
pronosticos = pronostico_siguiente(datos)  # tasa esperada de cada equipo para la temporada siguiente
ULTIMA = max(temporadas(datos))

# --- Recomendación: se calcula con los datos, no se escribe a mano --------------------------
ranking = (kpi.consistencia(datos)
           .merge(pronosticos, on="equipo")
           .sort_values(["temporadas_sobre_liga", "pronostico"], ascending=False)
           .reset_index(drop=True))
elegido = ranking.iloc[0]
tasa_eleg, gan_eleg, jug_eleg = kpi.kpi_equipo(datos, elegido["equipo"], ULTIMA)
tasa_liga_ult = kpi.kpi_liga(datos, ULTIMA)[0]
RECOMENDACION = (
    f"**Patrocinar a {elegido['equipo']} para {ULTIMA + 1} con contrato de un año y bono por desempeño.** "
    f"En {ULTIMA} ganó {gan_eleg} de {jug_eleg} series ({tasa_eleg} %, {tasa_eleg - tasa_liga_ult:+.1f} pts sobre la liga) "
    f"y superó a la liga en {elegido['temporadas_sobre_liga']} de {elegido['temporadas']} temporadas, el registro más estable de los 12. "
    f"Pague la parte fija pensando en el pronóstico ({elegido['pronostico']} % para {ULTIMA + 1}), no en repetir {tasa_eleg} %: "
    f"el bono se activa solo si el equipo vuelve a superar {tasa_liga_ult} % (la liga en {ULTIMA})."
)

PREGUNTA = (
    "**Quién decide:** la gerente de mercadeo de una marca colombiana de periféricos gamer.  \n"
    f"**Qué decide:** a cuál de los 12 equipos de la liga VCT Américas patrocinar en {ULTIMA + 1} y cómo atar el pago al rendimiento.  \n"
    "**Qué número necesita ver:** el porcentaje de series ganadas por temporada de cada equipo frente a la liga, "
    f"y cuánto se espera que gane en {ULTIMA + 1}."
)

FICHA = """
- **Fuente:** [vlr.gg](https://www.vlr.gg), historial público de partidas de cada equipo
  (p. ej. [Sentinels](https://www.vlr.gg/team/matches/2/sentinels/?group=completed)), extraído el 26/11/2026.
- **Licencia:** vlr.gg no publica una licencia abierta; los resultados deportivos son hechos públicos y se usan
  con atribución y con fines académicos. Un derivado de estos mismos datos se publica en Kaggle con licencia MIT
  ([Valorant Champion Tour 2021-2026 Data](https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data)).
- **Grano:** una fila = una serie (partida al mejor de 1, 3 o 5 mapas) vista desde uno de los 12 equipos.
  Si dos equipos de la liga se enfrentan, la serie aparece una vez por cada uno.
- **Columnas usadas:** `equipo`, `rival`, `evento`, `fase`, `marcador_equipo`, `marcador_rival` y `fecha` (la columna de fecha).
- **Datos personales:** ninguno. Solo nombres de organizaciones; no hay nombres de jugadores.
"""

equipo = solara.reactive("NRG" if "NRG" in equipos(datos) else equipos(datos)[0])
temporada = solara.reactive(ULTIMA)


def Grafico(fig):
    """Muestra una figura de matplotlib y la cierra para no acumular memoria."""
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def Tarjeta(titulo, valor, detalle):
    with solara.Card(titulo, style={"min-width": "210px", "flex": "1"}):
        solara.Markdown(f"## {valor}\n\n{detalle}")


@solara.component
def Page():
    solara.Title(NOMBRE)
    solara.Markdown(f"# {NOMBRE}")

    # 1. Pregunta de decisión
    solara.Markdown("### 1. La decisión\n" + PREGUNTA)

    # 8. Recomendación (arriba, porque es lo que la decisora vino a buscar)
    with solara.Card("Recomendación", style={"border-left": "6px solid #257de0"}):
        solara.Markdown(RECOMENDACION)

    # 5. Filtros: las opciones salen de los datos limpios
    with solara.Row():
        solara.Select(label="Equipo", value=equipo, values=equipos(datos))
        solara.Select(label="Temporada", value=temporada, values=temporadas(datos))

    # 4. KPI con su línea base y su verificación
    tasa_e, gan_e, jug_e = kpi.kpi_equipo(datos, equipo.value, temporada.value)
    tasa_l, gan_l, jug_l = kpi.kpi_liga(datos, temporada.value)
    solara.Markdown(f"### 2. KPI · {equipo.value} en {temporada.value}")
    if tasa_e is None:
        solara.Warning(f"{equipo.value} no jugó series en {temporada.value}. Elija otra temporada.")
    else:
        with solara.Row(style={"flex-wrap": "wrap"}):
            Tarjeta("Series ganadas", f"{tasa_e} %", f"{gan_e} de {jug_e} series")
            Tarjeta("Línea base: la liga", f"{tasa_l} %", f"{gan_l} de {jug_l} series de los 12 equipos")
            Tarjeta("Diferencia", f"{tasa_e - tasa_l:+.1f} pts", "equipo menos liga")
            Tarjeta("Mapas ganados", f"{kpi.tasa_mapas(datos, equipo.value, temporada.value)} %", "segundo indicador")
        if jug_e < kpi.MIN_SERIES:
            solara.Warning(f"Solo {jug_e} series: con menos de {kpi.MIN_SERIES} la tasa es poco confiable.")
        otra, _, _ = kpi.verificar_por_otro_camino(LIMPIO, equipo.value, temporada.value)
        marca = "✔ coincide" if otra == tasa_e else "✘ NO coincide"
        solara.Markdown(
            f"*Fórmula:* series ganadas ÷ series jugadas × 100 (se suman las series primero y se divide al final). "
            f"*Verificación por un segundo camino* (leyendo el CSV limpio línea por línea, sin pandas): {otra} % → {marca}."
        )

    # 6. Gráficos honestos
    solara.Markdown("### 3. Gráficos")
    Grafico(graficos.barras_por_equipo(kpi.tabla_por_equipo(datos, temporada.value), equipo.value,
                                       temporada.value, tasa_l))
    fila_pron = pronosticos[pronosticos["equipo"] == equipo.value]
    pron = float(fila_pron["pronostico"].iloc[0]) if len(fila_pron) else None
    Grafico(graficos.linea_anual(kpi.serie_anual(datos, equipo.value), kpi.serie_anual(datos), equipo.value, pron))

    # 7. Pronóstico medido contra la línea base
    r = evaluacion
    solara.Markdown(
        f"### 4. Pronóstico (scikit-learn)\n"
        f"Regresión lineal: *tasa de este año = {r['intercepto']} + {r['pendiente']} × tasa del año anterior*. "
        f"Se entrenó con {r['filas_entreno']} equipos-temporada hasta {r['temporada_prueba'] - 1} y se midió en "
        f"**{r['temporada_prueba']}**, que el modelo no vio ({r['filas_prueba']} equipos). "
        f"Línea base: suponer que cada equipo repite su tasa del año anterior."
    )
    Grafico(graficos.errores_pronostico(r["error_modelo"], r["error_base"], r["temporada_prueba"]))
    veredicto = "**le gana**" if r["le_gana"] else "**no le gana**"
    solara.Markdown(
        f"**Veredicto:** el modelo {veredicto} a la línea base ({r['error_modelo']} contra {r['error_base']} puntos de error medio). "
        f"La pendiente de {r['pendiente']} dice que solo un tercio de la ventaja de un año se mantiene al siguiente: "
        f"un gran año no garantiza otro. Aun así, el error de {r['error_modelo']} pts es grande; el pronóstico orienta, no promete."
    )
    detalle = r["detalle"][r["detalle"]["equipo"] == equipo.value]
    if len(detalle):
        d = detalle.iloc[0]
        solara.Markdown(
            f"{equipo.value} en {r['temporada_prueba']}: real **{d['tasa']} %**, modelo {d['pronostico']} %, "
            f"línea base {d['linea_base']} %."
        )

    # Detalle opcional
    solara.Markdown(f"### 5. Últimas series de {equipo.value} en {temporada.value}")
    solara.DataFrame(kpi.ultimas_series(datos, equipo.value, temporada.value), items_per_page=10)

    # 2 y 3. Ficha de datos y limpieza
    solara.Markdown("### 6. Datos y limpieza\n" + FICHA)
    tabla_bitacora = pd.DataFrame(bitacora, columns=["Paso", "Filas"])
    solara.DataFrame(tabla_bitacora, items_per_page=10)
    solara.Markdown(f"¿La bitácora cuadra (leídas − quitadas = limpias)? **{'Sí' if bitacora_cuadra(bitacora) else 'No'}**. "
                    "Reglas completas, una por línea, en `datos_proyecto.py`.")
