"""Gráficos honestos del tablero (matplotlib).

Reglas que cumplen:
- Comparan magnitudes (porcentajes), así que el eje arranca en 0.
- La escala es fija (0 a 100 %) para TODAS las opciones del filtro: cambiar de equipo o
  temporada no estira ni encoge el eje.
- Cada eje dice su unidad y el título dice la conclusión, no solo el tema.
"""
import matplotlib

matplotlib.use("Agg")  # sin ventana: el servidor solo dibuja imágenes
import matplotlib.pyplot as plt  # noqa: E402

AZUL = "#257de0"  # el equipo elegido
GRIS = "#c9c9c9"  # los demás equipos
TEXTO = "#191919"
TEXTO_SUAVE = "#666666"
NARANJA = "#f47230"  # el pronóstico


def _estilo(ax):
    """Ejes discretos: sin marco arriba ni a la derecha, cuadrícula suave."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(TEXTO_SUAVE)
    ax.tick_params(colors=TEXTO_SUAVE, labelsize=9)
    ax.set_axisbelow(True)


def barras_por_equipo(tabla, equipo, temporada, tasa_liga):
    """Barras horizontales: tasa de victorias de cada equipo en la temporada, con la liga como referencia."""
    tabla = tabla.sort_values("tasa")  # el mejor queda arriba
    fig, ax = plt.subplots(figsize=(8, 5.2))
    colores = [AZUL if e == equipo else GRIS for e in tabla["equipo"]]
    ax.barh(tabla["equipo"], tabla["tasa"], color=colores, height=0.7)
    for y, (tasa, jugadas) in enumerate(zip(tabla["tasa"], tabla["jugadas"])):
        ax.text(tasa + 1, y, f"{tasa:.1f} % ({jugadas} series)", va="center", fontsize=8, color=TEXTO)
    ax.axvline(tasa_liga, color=TEXTO_SUAVE, linestyle="--", linewidth=1.2)
    ax.text(tasa_liga + 0.5, len(tabla) - 0.35, f"Liga: {tasa_liga:.1f} %", fontsize=8, color=TEXTO_SUAVE)
    ax.set_xlim(0, 100)  # escala fija y desde cero
    ax.set_xlabel("Series ganadas (% de las jugadas)")
    ax.grid(axis="x", color="#eeeeee")
    fila = tabla[tabla["equipo"] == equipo]
    if fila.empty:
        titulo = f"{equipo} no jugó series en {temporada}"
    else:
        dif = float(fila["tasa"].iloc[0]) - tasa_liga
        puesto = list(tabla["equipo"])[::-1].index(equipo) + 1  # 1 = el de la tasa más alta
        titulo = f"{temporada}: {equipo} queda {puesto}.º de {len(tabla)}, {dif:+.1f} pts frente a la liga"
    ax.set_title(titulo, loc="left", fontsize=11, color=TEXTO)
    _estilo(ax)
    fig.tight_layout()
    return fig


def linea_anual(serie_equipo, serie_liga, equipo, pronostico=None):
    """Tasa por temporada del equipo frente a la liga, con el pronóstico de la temporada siguiente."""
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(serie_liga["temporada"], serie_liga["tasa"], color=GRIS, linewidth=2, marker="o", markersize=5)
    ax.plot(serie_equipo["temporada"], serie_equipo["tasa"], color=AZUL, linewidth=2, marker="o", markersize=6)
    ultimo = serie_equipo.iloc[-1]
    liga_final = serie_liga["tasa"].iloc[-1]
    arriba = ultimo["tasa"] >= liga_final  # la etiqueta del que va arriba sube; la del otro baja
    ax.text(ultimo["temporada"] - 0.1, ultimo["tasa"] + (4 if arriba else -8), equipo, color=TEXTO, fontsize=9, ha="right")
    ax.text(serie_liga["temporada"].iloc[-1] - 0.1, liga_final + (-8 if arriba else 4), "Liga", color=TEXTO_SUAVE,
            fontsize=9, ha="right")
    if pronostico is not None:
        siguiente = int(ultimo["temporada"]) + 1
        ax.plot([ultimo["temporada"], siguiente], [ultimo["tasa"], pronostico], color=NARANJA, linestyle="--", linewidth=2)
        ax.plot([siguiente], [pronostico], marker="o", markersize=8, color=NARANJA)
        ax.text(siguiente + 0.15, pronostico, f"Pronóstico {siguiente}\n{pronostico:.1f} %", color=TEXTO, fontsize=8,
                va="center")
    ax.set_ylim(0, 100)  # escala fija y desde cero
    primera, ultima = int(serie_liga["temporada"].min()), int(serie_liga["temporada"].max())
    ax.set_xlim(primera - 0.3, ultima + 1.9)  # deja espacio a la derecha para la etiqueta del pronóstico
    ax.set_xticks(list(range(primera, ultima + 2)))
    ax.set_ylabel("Series ganadas (%)")
    ax.set_xlabel("Temporada")
    ax.grid(axis="y", color="#eeeeee")
    encima = (serie_equipo.merge(serie_liga, on="temporada", suffixes=("", "_liga"))
              .eval("tasa > tasa_liga").sum())
    ax.set_title(f"{equipo} superó a la liga en {encima} de {len(serie_equipo)} temporadas",
                 loc="left", fontsize=11, color=TEXTO)
    _estilo(ax)
    fig.tight_layout()
    return fig


def errores_pronostico(error_modelo, error_base, temporada):
    """Barras del error medio: modelo contra línea base, en la temporada que el modelo no vio."""
    fig, ax = plt.subplots(figsize=(6, 2.6))
    etiquetas = ["Línea base\n(repetir el año anterior)", "Modelo\n(regresión lineal)"]
    valores = [error_base, error_modelo]
    ax.barh(etiquetas, valores, color=[GRIS, NARANJA], height=0.55)
    for y, v in enumerate(valores):
        ax.text(v + 0.4, y, f"{v:.1f} pts", va="center", fontsize=9, color=TEXTO)
    ax.set_xlim(0, max(30, max(valores) * 1.25))  # desde cero; la escala no depende del filtro
    ax.set_xlabel("Error medio absoluto (puntos porcentuales; menos es mejor)")
    veredicto = "le gana" if error_modelo < error_base else "no le gana"
    ax.set_title(f"En {temporada} el modelo {veredicto} a la línea base", loc="left", fontsize=11, color=TEXTO)
    ax.grid(axis="x", color="#eeeeee")
    _estilo(ax)
    fig.tight_layout()
    return fig
