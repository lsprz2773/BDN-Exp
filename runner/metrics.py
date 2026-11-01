"""Métricas del contenedor y del motor alrededor de la ventana de medición.

- cpu_throttled_seconds: delta de `throttled_usec` en cpu.stat (cgroup v2) del contenedor.
- max_rss_mb: máximo de container_memory_rss (cAdvisor vía Prometheus) en la ventana;
  si cAdvisor no tiene la serie del contenedor, se muestrea `anon` de memory.stat cada
  segundo (mismo valor que container_memory_rss); en último caso, memory.peak.
- disk_spill: delta de los contadores de spill del motor (pg_stat_database.temp_bytes
  en PostgreSQL; contadores *spill* de serverStatus en MongoDB).
- oom: delta de oom_kill en memory.events (o el contenedor dejó de correr).
"""
import json
import subprocess
import threading
import time
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


def _claves(texto):
    return {c: int(v) for c, v in (linea.split() for linea in texto.splitlines()) if v.isdigit()}


def throttled_seconds(nombre):
    return _claves(cgroup_file(nombre, "cpu.stat")).get("throttled_usec", 0) / 1e6


def cpu_usage_seconds(nombre):
    """CPU usada por el contenedor (usage_usec de cpu.stat); base de M3."""
    try:
        return _claves(cgroup_file(nombre, "cpu.stat")).get("usage_usec", 0) / 1e6
    except subprocess.CalledProcessError:
        return None


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


def rss_mb(nombre):
    """`anon` de memory.stat: el mismo valor que cAdvisor publica como container_memory_rss
    en cgroup v2."""
    try:
        for linea in cgroup_file(nombre, "memory.stat").splitlines():
            clave, valor = linea.split()
            if clave == "anon":
                return int(valor) / 2**20
    except (subprocess.CalledProcessError, ValueError):
        pass
    return None


class MuestreoRSS:
    """Muestrea cada segundo, en un hilo, el RSS (`anon` de memory.stat) y la CPU usada
    (`usage_usec` de cpu.stat) con un solo docker exec. Respaldo para cuando cAdvisor no ve
    la cgroup del contenedor (Docker Desktop 29.9 la anida fuera de /docker/, E-010).
    `muestras` = [(t_epoch, rss_mb, cpu_s)] alimenta la curva RSS de la corrida."""

    def __init__(self, nombre, intervalo=1.0):
        self.nombre, self.intervalo, self.maximo = nombre, intervalo, None
        self.muestras = []
        self._parar = threading.Event()
        self._hilo = threading.Thread(target=self._bucle, daemon=True)

    def _bucle(self):
        while not self._parar.is_set():
            t = time.time()
            try:
                c = _claves(_run("docker", "exec", self.nombre, "cat",
                                 "/sys/fs/cgroup/memory.stat", "/sys/fs/cgroup/cpu.stat"))
                v = c["anon"] / 2**20
                self.muestras.append((t, v, c["usage_usec"] / 1e6))
                if self.maximo is None or v > self.maximo:
                    self.maximo = v
            except (subprocess.CalledProcessError, KeyError):
                pass
            # docker exec tarda ~0,5-1 s con el host cargado: se descuenta para no espaciar más.
            self._parar.wait(max(0.0, self.intervalo - (time.time() - t)))

    def iniciar(self):
        self._hilo.start()
        return self

    def detener(self):
        self._parar.set()
        self._hilo.join(timeout=15)
        return self.maximo


def max_rss_mb_prometheus(cid, segundos, fin_epoch):
    # Por id y no por ruta completa: según la versión de Docker Desktop la cgroup del
    # contenedor cuelga de /docker/ o de otro prefijo.
    query = f'max(max_over_time(container_memory_rss{{id=~".*{cid}.*"}}[{int(segundos)}s]))'
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
