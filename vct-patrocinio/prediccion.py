"""Pronóstico sencillo con scikit-learn: la tasa de victorias de un equipo en la próxima temporada.

Modelo: regresión lineal  tasa_de_este_año = a + b * tasa_del_año_anterior,
entrenada con todos los equipos juntos (cada fila es un equipo en una temporada).

Medición honesta (sin fuga): el modelo se entrena SOLO con temporadas anteriores a la última
y se mide en la última temporada, que nunca vio. Se compara con la línea base ingenua
"este año el equipo gana lo mismo que el año pasado". Error = MAE en puntos porcentuales.
"""
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from indicadores import MIN_SERIES


def tabla_anual(df):
    """Una fila por equipo y temporada con su tasa; quita temporadas con menos de MIN_SERIES series."""
    t = df.groupby(["equipo", "temporada"])["gano"].agg(ganadas="sum", jugadas="count").reset_index()
    t["tasa"] = 100 * t["ganadas"] / t["jugadas"]  # sumar primero, dividir después
    return t[t["jugadas"] >= MIN_SERIES].reset_index(drop=True)


def pares(df):
    """Agrega la tasa del año anterior del mismo equipo (solo si ese año existe y es el inmediatamente anterior)."""
    t = tabla_anual(df).sort_values(["equipo", "temporada"])
    t["tasa_anterior"] = t.groupby("equipo")["tasa"].shift(1)
    t["temporada_anterior"] = t.groupby("equipo")["temporada"].shift(1)
    consecutivo = t["temporada_anterior"] == t["temporada"] - 1
    return t[consecutivo].drop(columns="temporada_anterior").reset_index(drop=True)


def evaluar(df):
    """Entrena con las temporadas viejas y mide en la última. Devuelve un diccionario con el resultado."""
    p = pares(df)
    prueba_temporada = int(p["temporada"].max())  # el último periodo: el modelo no lo ve al entrenar
    entreno = p[p["temporada"] < prueba_temporada]
    prueba = p[p["temporada"] == prueba_temporada].copy()

    modelo = LinearRegression().fit(entreno[["tasa_anterior"]], entreno["tasa"])
    prueba["pronostico"] = modelo.predict(prueba[["tasa_anterior"]])
    prueba["linea_base"] = prueba["tasa_anterior"]  # ingenua: repetir el año anterior

    error_modelo = mean_absolute_error(prueba["tasa"], prueba["pronostico"])
    error_base = mean_absolute_error(prueba["tasa"], prueba["linea_base"])
    return {
        "temporada_prueba": prueba_temporada,
        "filas_entreno": len(entreno),
        "filas_prueba": len(prueba),
        "error_modelo": round(error_modelo, 1),
        "error_base": round(error_base, 1),
        "le_gana": error_modelo < error_base,
        "pendiente": round(float(modelo.coef_[0]), 2),
        "intercepto": round(float(modelo.intercept_), 1),
        "detalle": prueba[["equipo", "tasa_anterior", "tasa", "pronostico", "linea_base"]].round(1),
    }


def pronostico_siguiente(df):
    """Pronóstico para la temporada siguiente a la última, entrenando ahora con TODAS las temporadas."""
    p = pares(df)
    modelo = LinearRegression().fit(p[["tasa_anterior"]], p["tasa"])
    ultima = tabla_anual(df)
    ultima = ultima[ultima["temporada"] == ultima["temporada"].max()].copy()
    ultima["pronostico"] = modelo.predict(ultima[["tasa"]].rename(columns={"tasa": "tasa_anterior"})).round(1)
    ultima["temporada_pronosticada"] = ultima["temporada"] + 1
    return ultima[["equipo", "tasa", "pronostico", "temporada_pronosticada"]].round(1).sort_values(
        "pronostico", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    from datos_proyecto import cargar

    datos = cargar()
    r = evaluar(datos)
    print(f"Prueba en {r['temporada_prueba']} ({r['filas_prueba']} equipos), entrenado con {r['filas_entreno']} filas")
    print(f"MAE modelo {r['error_modelo']} pts | MAE línea base {r['error_base']} pts | ¿le gana? {r['le_gana']}")
    print(r["detalle"].to_string(index=False))
    print(pronostico_siguiente(datos).to_string(index=False))
