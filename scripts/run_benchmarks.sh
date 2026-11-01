#!/usr/bin/env bash
# Automatización de la matriz de mediciones (playbook §8.1).
# Ejecuta todas las corridas de un perfil con runner/run_matrix.py.
#
#   Ronda 1 (dos terminales a la vez, misma --session):
#     scripts/run_benchmarks.sh --profile B --round 1 --parties B,C --session r1
#     scripts/run_benchmarks.sh --profile C --round 1 --parties B,C --session r1
#   Ronda 2:
#     scripts/run_benchmarks.sh --profile A --round 2
#   Suite de prueba (F5.5): igual que la ronda 1 pero con --test en lugar de --round
#   Al reanudar una ronda interrumpida, usar una --session nueva (p. ej. r1b).
#
# Requisitos: stack de monitoreo arriba y el entorno virtual con runner/requirements.txt
# (por defecto ~/.venvs/bdn; se puede cambiar con la variable VENV).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${VENV:-$HOME/.venvs/bdn}"

if ! curl -sf http://127.0.0.1:9090/-/ready >/dev/null; then
  echo "Levantando el stack de monitoreo..."
  docker compose -f "$ROOT/infra/monitoring/docker-compose.monitoring.yml" -p monitor up -d
fi

mkdir -p "$ROOT/results/logs"
exec "$VENV/bin/python" -u "$ROOT/runner/run_matrix.py" "$@"
