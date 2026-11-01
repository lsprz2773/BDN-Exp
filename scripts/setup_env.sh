#!/usr/bin/env bash
# Prepara una PC recién clonada para correr una suite. Es idempotente: se puede repetir.
#   1. Verifica Docker (cgroup v2), Docker Compose, Python 3 con venv, curl y la RAM disponible
#   2. Crea el entorno virtual del runner e instala runner/requirements.txt
#   3. Genera el dataset (semilla 42) y comprueba que es idéntico al de las demás PCs (sha256)
#   4. Descarga las imágenes, carga el dataset en la suite y lo valida
#   5. Levanta el stack de monitoreo
#
# Uso: scripts/setup_env.sh [A|B|C]        (por defecto A)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-A}"
VENV="${VENV:-$HOME/.venvs/bdn}"
DATA="$ROOT/data/generated/resultados_unidad.ndjson"
SHA_ESPERADO="10a04043c06971463cff30c2ec09936efc85ee2b671fc7430b23caa2d9bfc429"

paso() { printf '\n== %s\n' "$*"; }
falla() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

paso "1/5 Requisitos"
command -v docker >/dev/null || falla "no se encuentra docker (en WSL: activar Docker Desktop > Settings > Resources > WSL integration)"
docker info >/dev/null 2>&1 || falla "el daemon de Docker no responde (¿Docker Desktop abierto?)"
[ "$(docker info --format '{{.CgroupVersion}}')" = "2" ] || falla "Docker no usa cgroup v2"
docker compose version >/dev/null 2>&1 || falla "falta Docker Compose v2"
command -v curl >/dev/null || falla "falta curl"
command -v python3 >/dev/null || falla "falta python3"
python3 -c 'import sys; assert sys.version_info >= (3, 10)' || falla "se requiere Python >= 3.10"
mem_mb=$(( $(docker info --format '{{.MemTotal}}') / 1024 / 1024 ))
echo "Docker $(docker version --format '{{.Server.Version}}'), cgroup v2, $(docker info --format '{{.NCPU}}') CPUs, ${mem_mb} MB"
# Memoria mínima para Docker/WSL: límite del motor + monitoreo + runner + sistema
case "$PROFILE" in A) min_mb=6000 ;; B) min_mb=4500 ;; *) min_mb=3500 ;; esac
if [ "$mem_mb" -lt "$min_mb" ]; then
  falla "el perfil $PROFILE necesita ~${min_mb} MB para Docker y hay ${mem_mb} MB. En WSL sube 'memory=' en %USERPROFILE%\\.wslconfig (ver README)"
fi

paso "2/5 Entorno virtual ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV" || falla "no se pudo crear el venv (en Ubuntu: sudo apt install python3-venv)"
fi
"$VENV/bin/pip" install -q -r "$ROOT/runner/requirements.txt"
"$VENV/bin/python" -c 'import pymongo, psycopg; print("pymongo", pymongo.version, "| psycopg", psycopg.__version__)'

paso "3/5 Dataset"
if [ ! -f "$DATA" ]; then
  (cd "$ROOT" && python3 -I data/synthetic_data_generator.py --n 500000 --seed 42)
fi
sha=$(sha256sum "$DATA" | cut -d' ' -f1)
if [ "$sha" = "$SHA_ESPERADO" ]; then
  echo "sha256 OK: idéntico al dataset de las demás rondas"
else
  echo "AVISO: sha256 distinto ($sha). El dataset no es byte a byte el mismo; revisar la versión de Python." >&2
fi

paso "4/5 Imágenes, carga y validación (perfil $PROFILE)"
p="$(echo "$PROFILE" | tr 'A-C' 'a-c')"
docker compose -f "$ROOT/infra/docker-compose.yml" -p "suite_$p" \
  --env-file "$ROOT/infra/profiles/profile_$p.env" pull -q
docker pull -q alpine >/dev/null
"$ROOT/scripts/load_data.sh" "$PROFILE"
python3 -I "$ROOT/scripts/validate_data.py" "$PROFILE"

paso "5/5 Monitoreo"
docker compose -f "$ROOT/infra/monitoring/docker-compose.monitoring.yml" -p monitor up -d --quiet-pull
for _ in $(seq 1 30); do
  curl -sf http://127.0.0.1:9090/-/ready >/dev/null && break
  sleep 1
done
curl -sf http://127.0.0.1:9090/-/ready >/dev/null || falla "Prometheus no responde en :9090"
echo "Prometheus listo"

printf '\nListo. Para correr la suite:\n  scripts/run_benchmarks.sh --profile %s --round <N>\n' "$PROFILE"
