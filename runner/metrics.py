"""Métricas del contenedor y del motor alrededor de la ventana de medición.

- cpu_throttled_seconds: delta de `throttled_usec` en cpu.stat (cgroup v2) del contenedor.
- max_rss_mb: máximo de container_memory_rss (cAdvisor vía Prometheus) en la ventana;
  si Prometheus no responde, se usa memory.peak de la cgroup.
- disk_spill: delta de los contadores de spill del motor (pg_stat_database.temp_bytes
  en PostgreSQL; contadores *spill* de serverStatus en MongoDB).
- oom: delta de oom_kill en memory.events (o el contenedor dejó de correr).
"""
import json
import subprocess
import urllib.parse
import urllib.request

PROMETHEUS = "http://127.0.0.1:9090"


def _run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def container_id(nombre):
    return _run("docker", "inspect", "--format", "{{.Id}}", nombre)


def estado_contenedor(nombre):
    out = _run("docker", "inspect", "--format",
               "{{.State.Running}} {{.State.OOMKilled}} {{.RestartCount}}", nombre)
    running, oom, restarts = out.split()
    return {"running": running == "true", "oom_killed": oom == "true", "restarts": int(restarts)}


def cgroup_file(nombre, archivo):
    return _run("docker", "exec", nombre, "cat", f"/sys/fs/cgroup/{archivo}")


def throttled_seconds(nombre):
    for linea in cgroup_file(nombre, "cpu.stat").splitlines():
        clave, valor = linea.split()
        if clave == "throttled_usec":
            return int(valor) / 1e6
    return 0.0


def oom_kills(nombre):
    """Contador oom_kill de memory.events. Docker deja State.OOMKilled en true para siempre
    tras el primer OOM, así que se usa el delta de este contador por corrida."""
    for linea in cgroup_file(nombre, "memory.events").splitlines():
        clave, valor = linea.split()
        if clave == "oom_kill":
            return int(valor)
    return 0


def memory_peak_mb(nombre):
    try:
        return int(cgroup_file(nombre, "memory.peak")) / 2**20
    except (subprocess.CalledProcessError, ValueError):
        return None


def max_rss_mb_prometheus(cid, segundos, fin_epoch):
    query = f'max_over_time(container_memory_rss{{id="/docker/{cid}"}}[{int(segundos)}s])'
    url = f"{PROMETHEUS}/api/v1/query?" + urllib.parse.urlencode({"query": query, "time": fin_epoch})
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            res = json.load(r)["data"]["result"]
        return float(res[0]["value"][1]) / 2**20 if res else None
    except (OSError, KeyError, ValueError):
        return None


def drop_caches():
    """Vacía la page cache del kernel compartido de WSL2 (afecta a todo el host)."""
    _run("docker", "run", "--rm", "--privileged", "alpine",
         "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches")


# --- Contadores de spill del motor ------------------------------------------

def _sumar_spills(obj):
    total = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and "spill" in k.lower():
                total += v
            else:
                total += _sumar_spills(v)
    return total


def spill_mongo(client):
    status = client.admin.command("serverStatus")
    return _sumar_spills(status.get("metrics", {}))


def spill_pg(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT temp_bytes FROM pg_stat_database WHERE datname = current_database()")
        return cur.fetchone()[0]
