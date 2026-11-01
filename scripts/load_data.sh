#!/usr/bin/env bash
# Carga el NDJSON en MongoDB y PostgreSQL de una suite y crea los índices de la spec.
# Uso: scripts/load_data.sh [A|B|C] [--force]
#   Por defecto se carga el perfil A (más CPU y memoria = carga más rápida) y luego
#   se copia a las demás suites con scripts/copy_volumes.sh.
#   --force borra la colección y la tabla antes de cargar.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-A}"
FORCE="${2:-}"
p="$(echo "$PROFILE" | tr 'A-C' 'a-c')"
DATA="$ROOT/data/generated/resultados_unidad.ndjson"
MONGO="suite_$p-mongodb-1"
PG="suite_$p-postgres-1"
DB=control_academico

[ -f "$DATA" ] || { echo "Falta $DATA (corre data/synthetic_data_generator.py)" >&2; exit 1; }

"$ROOT/scripts/suite.sh" "$PROFILE" up

mongo_eval() { docker exec "$MONGO" mongosh --quiet "$DB" --eval "$1"; }
psql_c()     { docker exec -i "$PG" psql -v ON_ERROR_STOP=1 -q -U bench -d "$DB" "$@"; }

# --- MongoDB ---------------------------------------------------------------
n_mongo="$(mongo_eval 'db.resultados_unidad.estimatedDocumentCount()')"
if [ "$n_mongo" != "0" ] && [ "$FORCE" != "--force" ]; then
  echo "MongoDB ya tiene $n_mongo documentos; se omite (usa --force para recargar)."
else
  mongo_eval 'db.resultados_unidad.drop()' >/dev/null
  docker exec -i "$MONGO" mongosh --quiet "$DB" < "$ROOT/queries/mongodb/schema.js" >/dev/null
  echo "Cargando MongoDB..."
  time docker exec -i "$MONGO" mongoimport --quiet --db "$DB" --collection resultados_unidad \
    --numInsertionWorkers 4 < "$DATA"
fi

# --- PostgreSQL ------------------------------------------------------------
n_pg="$(psql_c -tAc "SELECT to_regclass('resultados_unidad') IS NOT NULL" )"
if [ "$n_pg" = "t" ]; then n_pg="$(psql_c -tAc 'SELECT count(*) FROM resultados_unidad')"; else n_pg=0; fi
if [ "$n_pg" != "0" ] && [ "$FORCE" != "--force" ]; then
  echo "PostgreSQL ya tiene $n_pg filas; se omite (usa --force para recargar)."
else
  psql_c -c 'DROP TABLE IF EXISTS resultados_unidad'
  psql_c < "$ROOT/queries/postgresql/schema.sql"
  echo "Cargando PostgreSQL..."
  # Cada línea del NDJSON entra como un solo campo: CSV con comilla y delimitador
  # que nunca aparecen en el JSON, para que COPY no interprete nada.
  time {
    psql_c -c 'CREATE UNLOGGED TABLE staging_resultados (doc jsonb)'
    psql_c -c "COPY staging_resultados (doc) FROM STDIN WITH (FORMAT csv, QUOTE e'\x01', DELIMITER e'\x02')" < "$DATA"
    psql_c -c "INSERT INTO resultados_unidad (id, data)
               SELECT (doc->>'resultado_id')::uuid, doc FROM staging_resultados"
    psql_c -c 'DROP TABLE staging_resultados'
    psql_c -c 'VACUUM ANALYZE resultados_unidad'
  }
fi

echo "MongoDB:    $(mongo_eval 'db.resultados_unidad.countDocuments()') documentos"
echo "PostgreSQL: $(psql_c -tAc 'SELECT count(*) FROM resultados_unidad') filas"
