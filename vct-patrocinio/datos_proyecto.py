"""Carga y limpieza de los datos del proyecto.

Fuente: historial de series de los 12 equipos de la liga VCT Américas 2026, tomado de vlr.gg
(una página por equipo: https://www.vlr.gg/team/matches/<id>/<equipo>/?group=completed).
Grano: una fila = una serie (partida al mejor de 1, 3 o 5 mapas) vista desde uno de los 12 equipos.

Correr `python datos_proyecto.py` imprime la bitácora y guarda datos/series_limpias.csv.
"""
from pathlib import Path

import pandas as pd

CARPETA = Path(__file__).parent / "datos"
CRUDO = CARPETA / "series_vct_americas_crudo.csv"
LIMPIO = CARPETA / "series_limpias.csv"

INICIO_VCT = "2021-01-01"  # el circuito oficial VCT empezó en 2021; antes eran torneos sueltos


def cargar_crudo(ruta=CRUDO):
    """Lee el CSV tal como salió de vlr.gg, todo como texto (para no perder nada al leer)."""
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8")


def limpiar(crudo):
    """Aplica las reglas de limpieza, una por línea. Devuelve (datos_limpios, bitacora)."""
    df = crudo.copy()
    bitacora = [("Filas leídas del CSV crudo", len(df))]

    def regla(texto, mascara_a_quitar):
        """Quita las filas marcadas y anota cuántas salieron."""
        nonlocal df
        bitacora.append((texto, -int(mascara_a_quitar.sum())))
        df = df[~mascara_a_quitar]

    df = df.apply(lambda col: col.str.strip())  # quita espacios sobrantes en todos los textos
    regla("Duplicadas (mismo equipo y misma serie)", df.duplicated(["equipo_id", "match_id"]))  # una serie cuenta una vez por equipo
    regla("Sin marcador (forfeit o serie no jugada)", ~df["marcador_equipo"].str.fullmatch(r"\d+") | ~df["marcador_rival"].str.fullmatch(r"\d+"))  # centinela: marcador vacío
    regla("Showmatch (exhibición, no es competencia)", df["evento"].str.contains("showmatch", case=False) | df["fase"].str.contains("showmatch", case=False))  # no cuenta para ganar
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y/%m/%d", errors="coerce")  # texto 2026/08/22 -> fecha
    regla("Fecha que no se pudo leer", df["fecha"].isna())  # fecha inválida
    regla("Antes de 2021 (anterior al circuito VCT)", df["fecha"] < INICIO_VCT)  # fuera del periodo de análisis
    df["marcador_equipo"] = df["marcador_equipo"].astype(int)  # texto -> número de mapas ganados
    df["marcador_rival"] = df["marcador_rival"].astype(int)  # texto -> número de mapas perdidos
    regla("Empate en el marcador (serie sin ganador)", df["marcador_equipo"] == df["marcador_rival"])  # 0-0 o 1-1: no hay ganador

    df["gano"] = (df["marcador_equipo"] > df["marcador_rival"]).astype(int)  # 1 si ganó la serie, 0 si la perdió
    df["mapas_jugados"] = df["marcador_equipo"] + df["marcador_rival"]  # mapas de la serie
    df["temporada"] = df["fecha"].dt.year  # la temporada VCT va de enero a diciembre
    df = df.drop(columns=["hora", "resultado_vlr"])  # la hora no se usa; el resultado se recalcula del marcador

    bitacora.append(("Filas limpias", len(df)))
    return df.sort_values(["equipo", "fecha"]).reset_index(drop=True), bitacora


def cargar(ruta=CRUDO):
    """Datos limpios listos para la app."""
    return limpiar(cargar_crudo(ruta))[0]


def bitacora_cuadra(bitacora):
    """La bitácora cuadra si filas leídas menos quitadas da exactamente las filas limpias."""
    leidas, *quitadas, (_, limpias) = bitacora
    return leidas[1] + sum(n for _, n in quitadas) == limpias


def equipos(df):
    """Opciones del filtro de equipo, tomadas de los datos limpios."""
    return sorted(df["equipo"].unique())


def temporadas(df):
    """Opciones del filtro de temporada, tomadas de los datos limpios."""
    return sorted(int(t) for t in df["temporada"].unique())


if __name__ == "__main__":
    datos, registro = limpiar(cargar_crudo())
    for paso, filas in registro:
        print(f"{paso:<48}{filas:>7}")
    print("¿Cuadra la bitácora?", bitacora_cuadra(registro))
    datos.to_csv(LIMPIO, index=False, date_format="%Y-%m-%d")
    print("Guardado:", LIMPIO)
