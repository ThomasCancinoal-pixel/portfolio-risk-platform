"""
Carga (la "L" de ETL).

Crea la base de datos DuckDB a partir del esquema en sql/01_schema.sql y carga:
  - assets: información descriptiva de cada activo (desde config.py)
  - prices: precios limpios (desde data/processed/prices_clean.parquet)
"""

import duckdb
import pandas as pd

from src.config import ASSETS, BENCHMARK, DATA_PROCESSED_DIR, DB_PATH, PROJECT_ROOT

CLEAN_FILE = DATA_PROCESSED_DIR / "prices_clean.parquet"
SCHEMA_FILE = PROJECT_ROOT / "sql" / "01_schema.sql"


def build_assets_table() -> pd.DataFrame:
    """Arma la tabla de activos a partir del diccionario ASSETS de config.py."""
    # "List comprehension": construye una lista en una sola línea.
    # {"ticker": t, **info} crea un diccionario nuevo con el ticker más
    # todos los datos de 'info' (el ** "desempaca" el diccionario).
    rows = [{"ticker": t, **info, "es_benchmark": False} for t, info in ASSETS.items()]

    # El benchmark no está en ASSETS (no se invierte en él), así que lo agregamos aparte
    rows.append({
        "ticker": BENCHMARK, "nombre": "SPDR S&P 500 ETF", "clase": "Benchmark",
        "sector": "Mercado EE.UU.", "moneda": "USD", "es_benchmark": True,
    })
    return pd.DataFrame(rows)


def load_to_duckdb() -> None:
    """Crea las tablas y carga los datos en la base DuckDB."""
    # connect() abre la base; si el archivo no existe, lo crea
    con = duckdb.connect(str(DB_PATH))
    try:
        # 1) Ejecutamos el archivo SQL del esquema (crea o recrea las tablas)
        con.execute(SCHEMA_FILE.read_text(encoding="utf-8"))

        # 2) Cargamos la tabla de activos.
        #    register() le "presta" el DataFrame de pandas a DuckDB con un nombre,
        #    para que podamos usarlo dentro de una consulta SQL como si fuera una tabla.
        con.register("assets_df", build_assets_table())
        con.execute("""
            INSERT INTO assets
            SELECT ticker, nombre, clase, sector, moneda, es_benchmark
            FROM assets_df
        """)

        # 3) Cargamos los precios. DuckDB lee el Parquet DIRECTAMENTE con read_parquet(),
        #    sin pasar por pandas. CAST convierte cada columna al tipo de la tabla.
        #    .as_posix() escribe la ruta con "/" (formato que SQL entiende en Windows).
        con.execute(f"""
            INSERT INTO prices
            SELECT CAST(date AS DATE), ticker, close, CAST(volume AS BIGINT)
            FROM read_parquet('{CLEAN_FILE.as_posix()}')
        """)

        print(f"Base de datos creada en: {DB_PATH}\n")

        # 4) Consulta de verificación: un JOIN une prices con assets por el ticker
        resumen = con.sql("""
            SELECT a.ticker, a.clase, a.moneda,
                   COUNT(*)    AS dias,
                   MIN(p.date) AS desde,
                   MAX(p.date) AS hasta
            FROM prices AS p
            JOIN assets AS a USING (ticker)
            GROUP BY ALL
            ORDER BY a.ticker
        """).df()   # .df() convierte el resultado en un DataFrame de pandas
        print(resumen.to_string(index=False))
    finally:
        # 'finally' se ejecuta SIEMPRE, haya error o no: la base queda cerrada.
        # Una base DuckDB abierta queda "bloqueada" para otros programas.
        con.close()


if __name__ == "__main__":
    load_to_duckdb()