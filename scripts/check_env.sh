#!/usr/bin/env bash
# Verifica los límites REALES de los contenedores en ejecución (actividad F1.5).
# Lee docker inspect y los archivos de la cgroup v2 dentro de cada contenedor.
# Uso: scripts/check_env.sh            (todos los contenedores con label bench.profile)
# La salida (tabla Markdown) se usa en la sección 1 del reporte.
set -euo pipefail

ids="$(docker ps -q --filter label=bench.profile)"
if [ -z "$ids" ]; then
  echo "No hay contenedores de benchmark en ejecución." >&2
  exit 1
fi

printf '| Perfil | Motor | Imagen | NanoCpus | Memory | MemorySwap | cpu.max | memory.max | memory.swap.max |\n'
printf '|---|---|---|---|---|---|---|---|---|\n'
for id in $ids; do
  info="$(docker inspect "$id" --format '{{index .Config.Labels "bench.profile"}}|{{index .Config.Labels "bench.engine"}}|{{.Config.Image}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.Memory}}|{{.HostConfig.MemorySwap}}')"
  cg="$(docker exec "$id" sh -c 'echo "$(cat /sys/fs/cgroup/cpu.max)|$(cat /sys/fs/cgroup/memory.max)|$(cat /sys/fs/cgroup/memory.swap.max)"')"
  printf '| %s | %s |\n' "$(echo "$info" | sed 's/|/ | /g')" "$(echo "$cg" | sed 's/|/ | /g')"
done | sort
