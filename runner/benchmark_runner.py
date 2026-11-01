"""Ejecuta UNA corrida (motor × perfil × query_id × concurrencia × repetición).

Fases: warmup -> medición -> cooldown. N clientes en bucle cerrado, cada uno en su
propio hilo y con su propia conexión (D-11). Ninguna consulta pasa del final de su
ventana: se le da como timeout el tiempo restante (maxTimeMS / statement_timeout), y
las que se cortan no cuentan para latencias ni throughput.

El flush de caché y el encendido del motor los hace el orquestador (run_matrix.py).
"""
import gzip
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import psycopg
import pymongo
from pymongo.errors import ExecutionTimeout, OperationFailure, PyMongoError

import metrics

ROOT = Path(__file__).resolve().parent.parent
QUERIES = ROOT / "queries"
DB = "control_academico"
COLL = "resultados_unidad"

PERFILES = {"A": "PROFILE_A_BASELINE", "B": "PROFILE_B_MEDIUM", "C": "PROFILE_C_SEVERE"}

# query_id -> (archivo, opciones). Mongo: kwargs de aggregate. PG: work_mem de la sesión.
VARIANTES = {
    "mongodb": {
        "Q1": ("q1", {}),
        "Q2_DISK0": ("q2", {"allowDiskUse": False}),
        "Q2_DISK1": ("q2", {"allowDiskUse": True}),
    },
    "postgresql": {
        "Q1": ("q1", None),
        "Q2_WM4": ("q2", "4MB"),
        "Q2_WM64": ("q2", "64MB"),
    },
}

MONGO_MEMORIA = {292}            # QueryExceededMemoryLimitNoDiskUseAllowed
MONGO_TIMEOUT = {50}             # MaxTimeMSExpired


def perfil_env(perfil):
    env = {}
    for linea in (ROOT / "infra" / "profiles" / f"profile_{perfil.lower()}.env").read_text().splitlines():
        if "=" in linea and not linea.startswith("#"):
            k, v = linea.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def contenedor(perfil, motor):
    return f"suite_{perfil.lower()}-{'mongodb' if motor == 'mongodb' else 'postgres'}-1"


# --- Clientes ------------------------------------------------------------------

class ClienteMongo:
    def __init__(self, env, qid):
        base, self.opciones = VARIANTES["mongodb"][qid]
        self.pipeline = json.loads((QUERIES / "mongodb" / f"{base}.json").read_text(encoding="utf-8"))
        self.client = pymongo.MongoClient(
            f"mongodb://127.0.0.1:{env['MONGO_PORT']}", maxPoolSize=1,
            serverSelectionTimeoutMS=15000, socketTimeoutMS=0)
        self.coll = self.client[DB][COLL]

    def ejecutar(self, restante_s):
        ms = max(1, int(restante_s * 1000))
        list(self.coll.aggregate(self.pipeline, maxTimeMS=ms, **self.opciones))

    def clasificar(self, exc):
        if isinstance(exc, ExecutionTimeout) or getattr(exc, "code", None) in MONGO_TIMEOUT:
            return "corte"
        if isinstance(exc, OperationFailure) and exc.code in MONGO_MEMORIA:
            return "memoria"
        return "error"

    def cerrar(self):
        self.client.close()


class ClientePG:
    def __init__(self, env, qid):
        base, self.work_mem = VARIANTES["postgresql"][qid]
        self.sql = (QUERIES / "postgresql" / f"{base}.sql").read_text(encoding="utf-8")
        self.env = env
        self._conectar()

    def _conectar(self):
        self.conn = psycopg.connect(
            host="127.0.0.1", port=int(self.env["PG_PORT"]), dbname=DB, user="bench",
            password=self.env["PG_PASSWORD"], autocommit=True, connect_timeout=15)
        if self.work_mem:
            self.conn.execute(f"SET work_mem = '{self.work_mem}'")

    def ejecutar(self, restante_s):
        # Tras un OOM de un backend, PostgreSQL reinicia y cierra todas las sesiones:
        # el cliente se reconecta, como haría una aplicación real.
        if self.conn.closed or self.conn.broken:
            self._conectar()
        ms = max(1, int(restante_s * 1000))
        with self.conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {ms}")
            cur.execute(self.sql)
            cur.fetchall()

    def clasificar(self, exc):
        if isinstance(exc, psycopg.errors.QueryCanceled):
            return "corte"
        if isinstance(exc, (psycopg.errors.OutOfMemory, psycopg.errors.DiskFull)):
            return "memoria"
        return "error"

    def cerrar(self):
        self.conn.close()


# --- Ejecución por fases -------------------------------------------------------

@dataclass
class Fase:
    inicio: float
    fin: float
    muestras: list = field(default_factory=list)   # (t_inicio, latencia_ms)
    fallos: dict = field(default_factory=dict)     # tipo -> cuántos
    ultimo_error: str = ""


def correr_fase(clientes, segundos):
    fase = Fase(inicio=time.time(), fin=time.time() + segundos)
    lock = threading.Lock()

    def bucle(cliente):
        while True:
            t0 = time.time()
            restante = fase.fin - t0
            if restante <= 0.05:
                return
            try:
                cliente.ejecutar(restante)
            except (PyMongoError, psycopg.Error, OSError) as exc:
                tipo = cliente.clasificar(exc)
                with lock:
                    fase.fallos[tipo] = fase.fallos.get(tipo, 0) + 1
                    if tipo != "corte":
                        fase.ultimo_error = f"{type(exc).__name__}: {str(exc)[:200]}"
                if tipo == "error":
                    time.sleep(0.5)   # no saturar si el motor cayó
                continue
            t1 = time.time()
            if t1 <= fase.fin:
                with lock:
                    fase.muestras.append((t0, (t1 - t0) * 1000))

    hilos = [threading.Thread(target=bucle, args=(c,), daemon=True) for c in clientes]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return fase


def percentil(valores, p):
    if not valores:
        return None
    v = sorted(valores)
    k = (len(v) - 1) * p / 100
    i = int(k)
    return v[i] if i + 1 >= len(v) else v[i] + (v[i + 1] - v[i]) * (k - i)


def _lector_spill(motor, env):
    """Conexión de monitoreo aparte de los clientes medidos; tolera reinicios del motor."""
    estado = {"cliente": None}

    def leer():
        try:
            if motor == "mongodb":
                if estado["cliente"] is None:
                    estado["cliente"] = pymongo.MongoClient(
                        f"mongodb://127.0.0.1:{env['MONGO_PORT']}", serverSelectionTimeoutMS=10000)
                return metrics.spill_mongo(estado["cliente"])
            c = estado["cliente"]
            if c is None or c.closed or c.broken:
                c = estado["cliente"] = psycopg.connect(
                    host="127.0.0.1", port=int(env["PG_PORT"]), dbname=DB, user="bench",
                    password=env["PG_PASSWORD"], autocommit=True, connect_timeout=10)
            return metrics.spill_pg(c)
        except (PyMongoError, psycopg.Error):
            return None

    def cerrar():
        if estado["cliente"] is not None:
            estado["cliente"].close()

    return leer, cerrar


def _guardar_cpu(ruta, fila, cpu_s):
    """CPU-s de la ventana leídos de la cgroup; scripts/export_series.py los usa cuando
    Prometheus no tiene la serie del contenedor (E-010). Varias suites escriben a la vez."""
    import fcntl
    ruta.parent.mkdir(parents=True, exist_ok=True)
    claves = ("timestamp_epoch", "engine", "profile", "query_id", "concurrency", "run_number")
    with open(ruta, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0, 2)
        if f.tell() == 0:
            f.write(",".join(claves) + ",cpu_seconds_medicion\n")
        f.write(",".join(str(fila[k]) for k in claves) + f",{'' if cpu_s is None else round(cpu_s, 3)}\n")
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)


def _guardar_serie(ruta, muestras):
    """Serie del muestreo propio, mismo formato que scripts/export_series.py."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(ruta, "wt", encoding="utf-8") as f:
        f.write("t_epoch,fase,rss_mb,cpu_nucleos\n")
        previo = None
        for t, rss, cpu in muestras:
            nucleos = "" if previo is None else round((cpu - previo[1]) / (t - previo[0]), 4)
            f.write(f"{int(t)},medicion,{round(rss, 1)},{nucleos}\n")
            previo = (t, cpu)


def ejecutar_corrida(perfil, motor, qid, concurrencia, rep, warmup, duracion, cooldown, ruta_raw,
                     ruta_serie=None):
    """Devuelve (fila_csv, notas, falla_real). falla_real = hubo algo que corregir o analizar
    (OOM o fallos distintos de cortes por fin de ventana). Con ruta_serie, guarda también los
    CPU-s de la ventana y, si hubo muestreo propio, la serie de RSS y CPU."""
    env = perfil_env(perfil)
    nombre = contenedor(perfil, motor)
    cid = metrics.container_id(nombre)
    Cliente = ClienteMongo if motor == "mongodb" else ClientePG
    notas = []
    leer_spill, cerrar_spill = _lector_spill(motor, env)
    oom0 = metrics.oom_kills(nombre)

    clientes = [Cliente(env, qid) for _ in range(concurrencia)]
    try:
        fallos_warmup = {}
        if warmup > 0:
            fallos_warmup = correr_fase(clientes, warmup).fallos
            if fallos_warmup:
                notas.append(f"warmup: {fallos_warmup}")

        muestreo = None
        if metrics.max_rss_mb_prometheus(cid, max(warmup, 10), time.time()) is None:
            muestreo = metrics.MuestreoRSS(nombre).iniciar()
        thr0, spill0 = metrics.throttled_seconds(nombre), leer_spill()
        cpu0 = metrics.cpu_usage_seconds(nombre)
        m = correr_fase(clientes, duracion)
        rss_muestreo = muestreo.detener() if muestreo else None
        estado = metrics.estado_contenedor(nombre)
        cpu_s = None
        if estado["running"]:
            cpu1 = metrics.cpu_usage_seconds(nombre)
            cpu_s = None if cpu0 is None or cpu1 is None or cpu1 < cpu0 else cpu1 - cpu0
            thr = metrics.throttled_seconds(nombre) - thr0
            spill1 = leer_spill()
            spill = None if spill0 is None or spill1 is None else spill1 > spill0
            if spill:
                unidad = "temp_bytes" if motor == "postgresql" else "contadores spill de serverStatus"
                notas.append(f"spill: +{spill1 - spill0} ({unidad})")
            n_oom = metrics.oom_kills(nombre) - oom0
        else:
            thr, spill, n_oom = None, None, 1
    finally:
        cerrar_spill()
        for c in clientes:
            try:
                c.cerrar()
            except Exception:   # el motor pudo haber caído
                pass

    time.sleep(2)   # deja que Prometheus raspe el final de la ventana
    rss = metrics.max_rss_mb_prometheus(cid, duracion, m.fin)
    if rss is None and rss_muestreo is not None:
        rss = rss_muestreo
        notas.append("max_rss_mb por muestreo de memory.stat anon cada 1 s (cAdvisor sin la serie)")
    elif rss is None:
        rss = metrics.memory_peak_mb(nombre) if estado["running"] else None
        notas.append("max_rss_mb desde memory.peak (Prometheus sin dato)")

    lat = [x[1] for x in m.muestras]
    oom = n_oom > 0
    if oom:
        notas.append(f"oom_kill en el contenedor: {n_oom}" if estado["running"] else "el contenedor dejó de correr")
    errores = sum(v for k, v in m.fallos.items() if k != "corte")
    falla_real = oom or errores > 0 or any(k != "corte" for k in fallos_warmup)
    if oom:
        status = "oom"
    elif not lat or errores:
        status = "error"
    elif spill:
        status = "spill"
    else:
        status = "ok"
    if m.fallos:
        notas.append(f"fallos en medición: {m.fallos}")
    if m.ultimo_error:
        notas.append(m.ultimo_error)
    if not lat:
        notas.append("ninguna consulta terminó dentro de la ventana")

    if ruta_raw:
        ruta_raw.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(ruta_raw, "wt", encoding="utf-8") as f:
            f.write("t_inicio_epoch,latencia_ms\n")
            for t0, ms in m.muestras:
                f.write(f"{t0:.3f},{ms:.3f}\n")

    r = lambda x, d: "" if x is None else round(x, d)
    fila = {
        "timestamp_epoch": int(m.inicio),
        "engine": motor,
        "profile": PERFILES[perfil],
        "query_id": qid,
        "concurrency": concurrencia,
        "run_number": rep,
        "throughput_qps": round(len(lat) / duracion, 4),
        "latency_p50_ms": r(percentil(lat, 50), 2),
        "latency_p95_ms": r(percentil(lat, 95), 2),
        "latency_p99_ms": r(percentil(lat, 99), 2),
        "cpu_throttled_seconds": r(thr, 3),
        "max_rss_mb": r(rss, 1),
        "disk_spill": "" if spill is None else str(bool(spill)).lower(),
        "status": status,
    }

    if ruta_serie:
        _guardar_cpu(ruta_serie.parent / "cpu_cgroup.csv", fila, cpu_s)
        if muestreo and muestreo.muestras:
            _guardar_serie(ruta_serie, muestreo.muestras)

    if cooldown > 0:
        time.sleep(cooldown)
    return fila, notas, falla_real
