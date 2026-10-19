# 📈 Plataforma de Optimización de Portafolios y Análisis de Riesgo de Mercado

> 🚧 Proyecto en construcción.

Pipeline de datos end-to-end para la gestión cuantitativa de portafolios:

1. **Ingesta (ETL):** descarga automatizada de precios históricos multiactivo con `yfinance`.
2. **Almacenamiento y análisis SQL:** base de datos analítica en `DuckDB` (CTEs, funciones de ventana, retornos).
3. **Optimización:** Teoría Moderna de Portafolios de Markowitz con `SciPy` (Frontera Eficiente, Máximo Sharpe, Mínima Varianza).
4. **Riesgo:** volatilidad, VaR paramétrico e histórico, CVaR y Maximum Drawdown.
5. **Visualización:** dashboard interactivo con `Streamlit` y `Plotly`.

## 🛠️ Stack

Python 3.12 · pandas · NumPy · SciPy · DuckDB · Plotly · Streamlit · pytest · Git