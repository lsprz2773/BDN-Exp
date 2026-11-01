#!/usr/bin/env bash
# Copia los volúmenes ya cargados de una suite a otras, para que todas tengan
# exactamente los mismos datos sin volver a cargar.
# Uso: scripts/copy_volumes.sh [origen] [destino...]     (por defecto: A -> B C)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-A}"
shift || true
if [ "$#" -eq 0 ]; then DESTS=(B C); else DESTS=("$@"); fi
lower() { echo "$1" | tr 'A-C' 'a-c'; }
s="$(lower "$SRC")"

# Los motores deben estar detenidos para copiar archivos consistentes
"$ROOT/scripts/suite.sh" "$SRC" stop

for D in "${DESTS[@]}"; do
  d="$(lower "$D")"
  [ "$d" = "$s" ] && continue
  "$ROOT/scripts/suite.sh" "$D" down
  for vol in mongo_data pg_data; do
    docker volume rm -f "suite_${d}_${vol}" >/dev/null
    docker volume create --label com.docker.compose.project="suite_$d" \
      --label com.docker.compose.volume="$vol" "suite_${d}_${vol}" >/dev/null
    echo "Copiando suite_${s}_${vol} -> suite_${d}_${vol}"
    docker run --rm -v "suite_${s}_${vol}:/from:ro" -v "suite_${d}_${vol}:/to" \
      alpine sh -c 'cp -a /from/. /to/'
  done
done
