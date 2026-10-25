"""
Validación de calidad de datos.

Revisa los precios crudos y entrega un REPORTE de problemas.
Regla: este módulo NO modifica los datos, solo informa. La corrección se
decide después, de forma explícita y documentada.
"""

import pandas as pd

from src.config import DATA_RAW_DIR

RAW_FILE = DATA_RAW_DIR / "prices_raw.parquet"

# Umbrales de las revisiones (definidos arriba para ajustarlos fácilmente)
STALE_MIN_DAYS = 3       # rachas de precio idéntico de 3+ días se consideran sospechosas
EXTREME_RETURN = 0.25    # variaciones diarias mayores a ±25% se marcan para revisar
MAX_GAP_DAYS = 7         # más de 7 días corridos sin datos se considera un hueco

# Todas las revisiones devuelven una tabla con estas mismas columnas,
# así después se pueden juntar en un solo reporte.
REPORT_COLUMNS = ["check", "ticker", "date", "detail"]


def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Filas con la misma combinación (fecha, ticker)."""
    # keep=False marca TODAS las copias, no solo la segunda
    dup = df[df.duplicated(subset=["date", "ticker"], keep=False)]
    return dup.assign(check="duplicado", detail="fila repetida (fecha, ticker)")[REPORT_COLUMNS]


def check_non_positive(df: pd.DataFrame) -> pd.DataFrame:
    """Precios de cierre iguales a cero o negativos."""
    bad = df[df["close"] <= 0]
    return bad.assign(check="precio_no_positivo", detail="close <= 0")[REPORT_COLUMNS]


def check_stale_prices(df: pd.DataFrame, min_days: int = STALE_MIN_DAYS) -> pd.DataFrame:
    """Rachas en que el precio de cierre se repite idéntico varios días seguidos."""
    issues = []
    # groupby("ticker") separa la tabla en un grupo por activo, y el for los recorre
    for ticker, g in df.groupby("ticker"):
        g = g.sort_values("date")

        # Truco para detectar rachas:
        # 1) .ne(.shift()) marca True cuando el precio CAMBIA respecto al día anterior
        # 2) .cumsum() suma esos True: cada racha de precios iguales recibe un número
        #    Ejemplo: precios 10, 10, 10, 12, 12 -> cambios T,F,F,T,F -> rachas 1,1,1,2,2
        changed = g["close"].ne(g["close"].shift())
        run_id = changed.cumsum()

        # Resumimos cada racha: fecha de inicio, de término, duración y precio
        runs = g.groupby(run_id).agg(
            start=("date", "first"),
            end=("date", "last"),
            days=("close", "size"),
            price=("close", "first"),
        )

        for _, r in runs[runs["days"] >= min_days].iterrows():
            issues.append({
                "check": "precio_repetido",
                "ticker": ticker,
                "date": r["start"],
                "detail": f"{r['price']:.2f} repetido {r['days']} días (hasta {r['end'].date()})",
            })
    return pd.DataFrame(issues, columns=REPORT_COLUMNS)


def check_extreme_returns(df: pd.DataFrame, threshold: float = EXTREME_RETURN) -> pd.DataFrame:
    """Variaciones diarias del precio mayores al umbral (en valor absoluto)."""
    df = df.sort_values(["ticker", "date"])
    # 1) Calculamos el retorno como columna de la tabla COMPLETA...
    df = df.assign(ret=df.groupby("ticker")["close"].pct_change())
    # 2) ...y recién después filtramos. Si no hay casos, 'bad' queda vacío sin problemas.
    bad = df[df["ret"].abs() > threshold]
    bad = bad.assign(check="retorno_extremo", detail=bad["ret"].map(lambda r: f"retorno diario {r:+.1%}"))
    return bad[REPORT_COLUMNS]


def check_date_gaps(df: pd.DataFrame, max_gap: int = MAX_GAP_DAYS) -> pd.DataFrame:
    """Saltos de más de max_gap días corridos entre dos fechas con datos."""
    df = df.sort_values(["ticker", "date"])
    # Mismo patrón: primero la columna en la tabla completa, después el filtro
    df = df.assign(gap=df.groupby("ticker")["date"].diff().dt.days)
    bad = df[df["gap"] > max_gap]
    bad = bad.assign(check="hueco_fechas", detail=bad["gap"].map(lambda d: f"{int(d)} días sin datos antes de esta fecha"))
    return bad[REPORT_COLUMNS]

def run_all_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta todas las revisiones y las junta en un único reporte."""
    report = pd.concat(
        [
            check_duplicates(df),
            check_non_positive(df),
            check_stale_prices(df),
            check_extreme_returns(df),
            check_date_gaps(df),
        ],
        ignore_index=True,
    )
    return report.sort_values(["check", "ticker", "date"]).reset_index(drop=True)


if __name__ == "__main__":
    prices = pd.read_parquet(RAW_FILE)
    print(f"Validando {len(prices):,} filas de {prices['ticker'].nunique()} activos...\n")

    report = run_all_checks(prices)

    if report.empty:
        print("✅ Sin problemas detectados.")
    else:
        # Conteo de problemas por tipo de revisión y activo
        print("Resumen de problemas:")
        print(report.groupby(["check", "ticker"]).size().to_string())
        print("\nDetalle:")
        print(report.to_string(index=False))