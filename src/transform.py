"""
Transformación (la "T" de ETL).

Toma los precios crudos (data/raw/), aplica la ventana de análisis, conserva
solo las columnas necesarias y, ANTES de guardar, exige que los datos pasen un
control de calidad (quality gate). El archivo crudo nunca se modifica.
"""

import pandas as pd

from src.config import ANALYSIS_END_DATE, DATA_PROCESSED_DIR, DATA_RAW_DIR, START_DATE
from src.validate import check_duplicates, check_non_positive, check_stale_prices

RAW_FILE = DATA_RAW_DIR / "prices_raw.parquet"
CLEAN_FILE = DATA_PROCESSED_DIR / "prices_clean.parquet"

# Máximo de días seguidos con precio idéntico que aceptamos como "posible dato real".
# Rachas más largas se consideran datos congelados y bloquean el proceso.
MAX_STALE_DAYS_ALLOWED = 5


def clean_prices(raw: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Aplica la ventana de análisis y deja solo las columnas necesarias."""
    # pd.Timestamp convierte el texto "AAAA-MM-DD" en una fecha comparable
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)

    # Filtro con dos condiciones: & significa "Y" (ambas deben cumplirse).
    # Cada condición va entre paréntesis por cómo Python ordena las operaciones.
    df = raw[(raw["date"] >= start_ts) & (raw["date"] <= end_ts)]

    # Solo lo que usaremos: el cierre (ya ajustado) y el volumen
    df = df[["date", "ticker", "close", "volume"]]

    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def quality_gate(df: pd.DataFrame) -> None:
    """
    Control de calidad: si encuentra un problema grave, DETIENE el proceso.
    No devuelve nada (None): o pasa, o lanza un error.
    """
    # Reutilizamos las funciones de validate.py en vez de reescribirlas
    # (principio DRY: "Don't Repeat Yourself", no te repitas).
    problemas = pd.concat(
        [
            check_duplicates(df),
            check_non_positive(df),
            check_stale_prices(df, min_days=MAX_STALE_DAYS_ALLOWED + 1),
        ],
        ignore_index=True,
    )

    if not problemas.empty:
        print(problemas.to_string(index=False))
        raise ValueError(f"Quality gate NO superado: {len(problemas)} problema(s) grave(s).")

    print("✅ Quality gate superado: sin duplicados, sin precios <= 0 "
          f"y sin rachas de más de {MAX_STALE_DAYS_ALLOWED} días.")


def save_clean(df: pd.DataFrame) -> None:
    """Guarda los datos limpios en data/processed/ en formato Parquet."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_FILE, index=False)
    print(f"Guardado: {CLEAN_FILE} ({len(df):,} filas)")


if __name__ == "__main__":
    raw = pd.read_parquet(RAW_FILE)
    print(f"Datos crudos: {len(raw):,} filas")

    clean = clean_prices(raw, START_DATE, ANALYSIS_END_DATE)
    print(f"Ventana {START_DATE} a {ANALYSIS_END_DATE}: {len(clean):,} filas "
          f"({len(raw) - len(clean):,} filas fuera de la ventana)\n")

    quality_gate(clean)   # si falla, el programa se detiene aquí y NO guarda nada
    save_clean(clean)

    resumen = clean.groupby("ticker")["date"].agg(["min", "max", "count"])
    print("\nResumen de los datos limpios:")
    print(resumen)