"""KPI del tablero: tasa de victorias en series.

Fórmula: series ganadas / series jugadas x 100. Es un cociente, así que primero se SUMA
(ganadas y jugadas) y al final se DIVIDE; nunca se promedian porcentajes de cada mes o equipo.
Línea base: la misma tasa para los 12 equipos juntos en la misma temporada (la "liga").
"""
MIN_SERIES = 10  # con menos series la tasa de un año es puro ruido; se marca como poco confiable


def tasa(ganadas, jugadas):
    """Porcentaje con un decimal. None si no hay series."""
    return round(100 * ganadas / jugadas, 1) if jugadas else None


def kpi_equipo(df, equipo, temporada):
    """Tasa de victorias de un equipo en una temporada: (tasa %, ganadas, jugadas)."""
    datos = df[(df["equipo"] == equipo) & (df["temporada"] == temporada)]
    ganadas, jugadas = int(datos["gano"].sum()), len(datos)  # sumar primero
    return tasa(ganadas, jugadas), ganadas, jugadas  # dividir después


def kpi_liga(df, temporada):
    """Línea base: tasa de los 12 equipos juntos en la temporada (suma de todas sus series)."""
    datos = df[df["temporada"] == temporada]
    ganadas, jugadas = int(datos["gano"].sum()), len(datos)
    return tasa(ganadas, jugadas), ganadas, jugadas


def tasa_mapas(df, equipo, temporada):
    """Segundo indicador: mapas ganados / mapas jugados, también sumando primero."""
    datos = df[(df["equipo"] == equipo) & (df["temporada"] == temporada)]
    return tasa(int(datos["marcador_equipo"].sum()), int(datos["mapas_jugados"].sum()))


def tabla_por_equipo(df, temporada):
    """Tasa de cada equipo en la temporada, ordenada de mayor a menor."""
    datos = df[df["temporada"] == temporada]
    t = datos.groupby("equipo")["gano"].agg(ganadas="sum", jugadas="count").reset_index()
    t["tasa"] = (100 * t["ganadas"] / t["jugadas"]).round(1)
    return t.sort_values("tasa", ascending=False).reset_index(drop=True)


def serie_anual(df, equipo=None):
    """Tasa por temporada, de un equipo o (si equipo es None) de la liga completa."""
    datos = df if equipo is None else df[df["equipo"] == equipo]
    t = datos.groupby("temporada")["gano"].agg(ganadas="sum", jugadas="count").reset_index()
    t["tasa"] = (100 * t["ganadas"] / t["jugadas"]).round(1)
    return t


def consistencia(df):
    """Por equipo: en cuántas temporadas (con al menos MIN_SERIES series) superó la tasa de la liga."""
    liga = serie_anual(df).set_index("temporada")["tasa"]
    t = df.groupby(["equipo", "temporada"])["gano"].agg(ganadas="sum", jugadas="count").reset_index()
    t = t[t["jugadas"] >= MIN_SERIES]
    t["sobre_liga"] = 100 * t["ganadas"] / t["jugadas"] > t["temporada"].map(liga)
    return t.groupby("equipo")["sobre_liga"].agg(temporadas_sobre_liga="sum", temporadas="count").reset_index()


def ultimas_series(df, equipo, temporada, n=10):
    """Tabla de detalle: las n series más recientes del equipo en la temporada."""
    datos = df[(df["equipo"] == equipo) & (df["temporada"] == temporada)].sort_values("fecha", ascending=False)
    tabla = datos.head(n)[["fecha", "rival", "evento", "marcador_equipo", "marcador_rival"]].copy()
    tabla["fecha"] = tabla["fecha"].dt.strftime("%Y-%m-%d")
    tabla["resultado"] = ["Ganó" if g else "Perdió" for g in datos.head(n)["gano"]]
    return tabla.rename(columns={"fecha": "Fecha", "rival": "Rival", "evento": "Torneo",
                                 "marcador_equipo": "Mapas a favor", "marcador_rival": "Mapas en contra",
                                 "resultado": "Resultado"})


def verificar_por_otro_camino(ruta_limpia, equipo, temporada):
    """Segundo camino para el KPI: recorre el CSV limpio línea por línea, sin pandas."""
    import csv

    ganadas = jugadas = 0
    with open(ruta_limpia, encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            if fila["equipo"] == equipo and fila["fecha"].startswith(str(temporada)):
                jugadas += 1
                ganadas += int(fila["marcador_equipo"]) > int(fila["marcador_rival"])
    return tasa(ganadas, jugadas), ganadas, jugadas
