#!/usr/bin/env bash
# Controla la suite de un perfil (proyecto de compose suite_<perfil>).
# Uso: scripts/suite.sh <A|B|C> <up|stop|down|ps|logs> [mongodb|postgres]
#   up    levanta el motor indicado y espera a que esté healthy (sin motor: los dos)
#   stop  detiene el motor indicado (los datos se conservan en el volumen)
#   down  elimina los contenedores de la suite (los volúmenes se conservan)
#   ps    estado de la suite
#   logs  últimas líneas del log del motor
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:?perfil A|B|C}"
ACTION="${2:?acción up|stop|down|ps|logs}"
ENGINE="${3:-}"

case "$PROFILE" in
  A|B|C) ;;
  *) echo "Perfil inválido: $PROFILE" >&2; exit 1 ;;
esac
p="$(echo "$PROFILE" | tr 'A-C' 'a-c')"

compose() {
  docker compose -f "$ROOT/infra/docker-compose.yml" -p "suite_$p" \
    --env-file "$ROOT/infra/profiles/profile_$p.env" "$@"
}

case "$ACTION" in
  up)   compose up -d --wait $ENGINE ;;
  stop) compose stop $ENGINE ;;
  down) compose down ;;
  ps)   compose ps ;;
  logs) compose logs --tail 50 $ENGINE ;;
  *) echo "Acción inválida: $ACTION" >&2; exit 1 ;;
esac
