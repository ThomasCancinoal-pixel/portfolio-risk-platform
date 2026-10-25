"""
Configuración central del proyecto.

Este archivo es la "única fuente de verdad": cualquier parámetro que se use en
más de un lugar (tickers, fechas, rutas) se define AQUÍ y el resto del código
lo importa. Para cambiar el universo de activos, solo se edita este archivo.
"""

from pathlib import Path

# =============================================================================
# RUTAS DEL PROYECTO
# =============================================================================
# Path(__file__) es la ruta de ESTE archivo (src/config.py).
# .resolve() la convierte en ruta absoluta y .parent sube una carpeta.
# Dos .parent: src/config.py -> src/ -> carpeta raíz del proyecto.
# Así las rutas funcionan en cualquier computador, sin escribir "C:\Users\..."
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"              # datos tal como llegan
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"  # datos limpios
DB_PATH = DATA_PROCESSED_DIR / "portfolio.duckdb"         # base de datos (Fase 2)

# =============================================================================
# PARÁMETROS DE DESCARGA
# =============================================================================
# Mismo inicio que el trabajo de Finanzas II, para poder comparar resultados.
START_DATE = "2014-01-01"

# Fecha final del análisis (opción A, decidida el 24-10-2026).
# Yahoo Finance entrega precios CONGELADOS de ENTEL.SN desde el 17-07-2026
# (verificado contra una fuente chilena: el precio real sí cambió y hubo volumen).
# Se corta el análisis de TODOS los activos el día anterior, para que todos
# cubran el mismo periodo con datos confiables.
ANALYSIS_END_DATE = "2026-07-16"
# =============================================================================
# UNIVERSO DE ACTIVOS
# =============================================================================
# Diccionario: la "llave" es el ticker de Yahoo Finance y el "valor" es otro
# diccionario con información descriptiva (útil para el dashboard y el README).
ASSETS = {
    "AAPL":     {"nombre": "Apple",             "clase": "Acción EE.UU.", "sector": "Tecnología",    "moneda": "USD"},
    "JPM":      {"nombre": "JPMorgan Chase",    "clase": "Acción EE.UU.", "sector": "Financiero",    "moneda": "USD"},
    "XOM":      {"nombre": "ExxonMobil",        "clase": "Acción EE.UU.", "sector": "Energía",       "moneda": "USD"},
    "JNJ":      {"nombre": "Johnson & Johnson", "clase": "Acción EE.UU.", "sector": "Salud",         "moneda": "USD"},
    "TLT":      {"nombre": "Bonos Tesoro 20+",  "clase": "Renta fija",    "sector": "Bonos",         "moneda": "USD"},
    "GLD":      {"nombre": "Oro",               "clase": "Materia prima", "sector": "Metales",       "moneda": "USD"},
    "ENTEL.SN": {"nombre": "Entel",             "clase": "Acción Chile",  "sector": "Telecom",       "moneda": "CLP"},
    "ECH":      {"nombre": "iShares MSCI Chile","clase": "ETF Chile",     "sector": "Mercado Chile", "moneda": "USD"},
}

# Lista solo con los tickers invertibles (las llaves del diccionario)
TICKERS = list(ASSETS.keys())

# Benchmark: referencia para comparar el portafolio (NO se invierte en él)
BENCHMARK = "SPY"

# Todos los tickers que el ETL debe descargar
ALL_TICKERS = TICKERS + [BENCHMARK]

# =============================================================================
# CONSTANTES FINANCIERAS
# =============================================================================
# Días de mercado en un año (no 365): se usa para anualizar retornos y volatilidad
TRADING_DAYS_PER_YEAR = 252