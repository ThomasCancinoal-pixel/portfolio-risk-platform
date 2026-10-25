"""
Extracción (la "E" de ETL).

Descarga precios históricos diarios desde Yahoo Finance y los guarda SIN
modificar en data/raw/. La limpieza y validación se hacen en otro módulo:
cada archivo tiene una sola responsabilidad.
"""

from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.config import ALL_TICKERS, DATA_RAW_DIR, START_DATE


def download_prices(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """
    Descarga precios diarios ajustados (OHLCV) y los devuelve en formato largo.

    Parámetros
    ----------
    tickers : lista de tickers de Yahoo Finance, por ejemplo ["AAPL", "ENTEL.SN"]
    start   : fecha inicial "AAAA-MM-DD" (incluida)
    end     : fecha final "AAAA-MM-DD" (NO incluida). Si es None, se usa hoy.

    Retorna
    -------
    DataFrame con columnas: date, ticker, open, high, low, close, volume
    (una fila por cada combinación de fecha y ticker).
    """
    # Si no se indica fecha final, usamos HOY. Como yfinance NO incluye la fecha
    # "end", esto deja fuera automáticamente el día en curso, cuyo precio aún
    # no es definitivo (hallazgo de la exploración).
    if end is None:
        end = date.today().isoformat()

    print(f"Descargando {len(tickers)} activos desde {start} hasta {end} (sin incluir)...")

    # auto_adjust=True -> precios ajustados por dividendos y splits
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    # Principio "fallar fuerte": si algo sale mal, detenemos el programa con un
    # mensaje claro, en vez de seguir trabajando con datos vacíos o incompletos.
    if data.empty:
        raise ValueError("La descarga no devolvió datos. Revisa los tickers o tu conexión.")

    # .stack(level="Ticker") convierte el formato ANCHO (una columna por activo)
    # en formato LARGO (una fila por fecha y activo).
    # .reset_index() transforma la fecha y el ticker en columnas normales.
    long_df = data.stack(level="Ticker").reset_index()

    # Nombres de columnas en minúscula: convención estándar en bases de datos
    long_df.columns = [col.lower() for col in long_df.columns]

    # Al mezclar activos de Chile y EE.UU., hay días en que uno cotiza y el otro
    # no (feriados distintos). Esos casos quedan sin precio: los eliminamos aquí,
    # porque una fila sin precio de cierre no aporta información.
    long_df = long_df.dropna(subset=["close"])

    # Verificamos que llegaron TODOS los tickers pedidos (como pasó con ^IPSA,
    # un ticker puede fallar sin detener la descarga de los demás).
    recibidos = set(long_df["ticker"].unique())
    faltantes = set(tickers) - recibidos
    if faltantes:
        raise ValueError(f"No se recibieron datos para: {sorted(faltantes)}")

    # Ordenamos por activo y fecha, y fijamos el orden de las columnas
    long_df = long_df.sort_values(["ticker", "date"]).reset_index(drop=True)
    return long_df[["date", "ticker", "open", "high", "low", "close", "volume"]]


def save_raw(df: pd.DataFrame, filename: str = "prices_raw.parquet") -> Path:
    """Guarda el DataFrame en data/raw/ en formato Parquet y devuelve la ruta."""
    # Crea la carpeta si no existe (exist_ok=True evita error si ya existe)
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    path = DATA_RAW_DIR / filename
    df.to_parquet(path, index=False)

    print(f"Guardado: {path} ({len(df):,} filas)")
    return path


# Este bloque SOLO se ejecuta cuando corres el archivo directamente
# (python -m src.extract), no cuando otro archivo lo importa.
if __name__ == "__main__":
    prices = download_prices(ALL_TICKERS, START_DATE)
    save_raw(prices)

    # Resumen por activo: primera fecha, última fecha y cantidad de días
    resumen = prices.groupby("ticker")["date"].agg(["min", "max", "count"])
    print("\nResumen de la descarga:")
    print(resumen)