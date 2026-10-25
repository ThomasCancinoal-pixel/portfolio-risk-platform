-- =============================================================================
-- 01_schema.sql — Esquema (estructura) de la base de datos analítica
-- =============================================================================
-- CREATE OR REPLACE: si la tabla existe, la borra y la crea de nuevo.
-- Esto hace que la carga sea IDEMPOTENTE (correrla 1 o 10 veces da lo mismo).

-- Tabla de DIMENSIÓN: un registro por activo (información descriptiva)
CREATE OR REPLACE TABLE assets (
    ticker        VARCHAR PRIMARY KEY,   -- VARCHAR = texto; PRIMARY KEY = único e irrepetible
    nombre        VARCHAR NOT NULL,      -- NOT NULL = obligatorio, no puede quedar vacío
    clase         VARCHAR NOT NULL,
    sector        VARCHAR,
    moneda        VARCHAR NOT NULL,
    es_benchmark  BOOLEAN NOT NULL       -- BOOLEAN = verdadero/falso
);

-- Tabla de HECHOS: un registro por día y activo
CREATE OR REPLACE TABLE prices (
    date    DATE    NOT NULL,            -- DATE = fecha sin hora
    ticker  VARCHAR NOT NULL,
    close   DOUBLE  NOT NULL,            -- DOUBLE = número con decimales
    volume  BIGINT,                      -- BIGINT = número entero grande
    PRIMARY KEY (date, ticker)           -- llave compuesta: un solo precio por activo y día
);