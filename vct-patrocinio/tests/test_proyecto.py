"""Pruebas: reglas de limpieza, KPI con su verificación y pronóstico sin fuga."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import indicadores as kpi  # noqa: E402
from datos_proyecto import LIMPIO, bitacora_cuadra, cargar_crudo, limpiar  # noqa: E402
from prediccion import evaluar, pares  # noqa: E402


def caso():
    """Filas inventadas solo para probar las reglas (no son los datos del tablero)."""
    columnas = ["equipo_id", "equipo", "match_id", "rival", "rival_tag", "evento", "fase",
                "marcador_equipo", "marcador_rival", "resultado_vlr", "fecha", "hora"]
    filas = [
        ["1", "A", "10", "X", "X", "Liga", "W1", "2", "0", "win", "2025/03/01", "1:00 pm"],
        ["1", "A", "10", "X", "X", "Liga", "W1", "2", "0", "win", "2025/03/01", "1:00 pm"],  # duplicada
        ["1", "A", "11", "Y", "Y", "Liga", "W2", "", "", "win", "2025/03/02", "1:00 pm"],  # forfeit
        ["1", "A", "12", "Z", "Z", "Showmatch", "", "1", "0", "win", "2025/03/03", "1:00 pm"],  # exhibición
        ["1", "A", "13", "X", "X", "Copa", "GF", "1", "2", "loss", "2020/12/30", "1:00 pm"],  # antes de 2021
        ["1", "A", "14", "Y", "Y", "Liga", "W3", "1", "1", "draw", "2025/03/04", "1:00 pm"],  # empate
        ["1", "A", "15", "Z", "Z", "Liga", "W4", " 1 ", "2", "loss", "2025/03/05", "1:00 pm"],  # espacios
    ]
    return pd.DataFrame(filas, columns=columnas)


def test_reglas_de_limpieza_y_bitacora():
    limpio, bitacora = limpiar(caso())
    assert list(limpio["match_id"]) == ["10", "15"]
    assert list(limpio["gano"]) == [1, 0]
    assert bitacora_cuadra(bitacora)


def test_kpi_suma_primero_y_divide_despues():
    """Un equipo con 1/1 en un mes y 1/3 en otro: 2/4 = 50 %, no el promedio de 100 % y 33 % (66,7 %)."""
    df = pd.DataFrame({"equipo": ["A"] * 4, "temporada": [2025] * 4, "gano": [1, 1, 0, 0]})
    assert kpi.kpi_equipo(df, "A", 2025) == (50.0, 2, 4)


def test_bitacora_real_cuadra():
    _, bitacora = limpiar(cargar_crudo())
    assert bitacora[0] == ("Filas leídas del CSV crudo", 2429)
    assert bitacora[-1] == ("Filas limpias", 2173)
    assert bitacora_cuadra(bitacora)


def test_cifra_de_control_por_otro_camino():
    """Cifra de control: NRG ganó 31 de 48 series en 2026 = 64,6 %, igual por pandas y leyendo el CSV a mano."""
    datos, _ = limpiar(cargar_crudo())
    assert kpi.kpi_equipo(datos, "NRG", 2026) == (64.6, 31, 48)
    assert kpi.verificar_por_otro_camino(LIMPIO, "NRG", 2026) == (64.6, 31, 48)


def test_csv_limpio_guardado_esta_al_dia():
    datos, _ = limpiar(cargar_crudo())
    guardado = pd.read_csv(LIMPIO)
    assert len(guardado) == len(datos)
    assert guardado["gano"].sum() == datos["gano"].sum()


def test_pronostico_sin_fuga():
    """El modelo se mide en la última temporada y entrena solo con temporadas anteriores."""
    datos, _ = limpiar(cargar_crudo())
    r = evaluar(datos)
    assert r["temporada_prueba"] == pares(datos)["temporada"].max()
    assert r["filas_entreno"] == (pares(datos)["temporada"] < r["temporada_prueba"]).sum()
    assert r["le_gana"] == (r["error_modelo"] < r["error_base"])
