-- Esquema PostgreSQL para la práctica (ver data/ESQUEMA_DATASET.md).
-- Uso: psql -d control_academico -f queries/postgresql/schema.sql
-- Tabla única con el documento completo en JSONB. Índices exigidos por la spec:
-- PK en id y B-Tree sobre la fecha extraída del JSONB. Sin índice en calificacion.final (Q2) ni GIN.

CREATE TABLE IF NOT EXISTS resultados_unidad (
    id   UUID  PRIMARY KEY,   -- mismo valor que data->>'resultado_id'
    data JSONB NOT NULL
);

-- Índice de expresión sobre el texto ISO-8601 (formato fijo UTC 'Z', ordenable como texto).
-- Q2 compara como texto para poder usar este índice (decisión D-15).
CREATE INDEX IF NOT EXISTS idx_resultados_cerrado_en
    ON resultados_unidad ((data->>'cerrado_en'));
