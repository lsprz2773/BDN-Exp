"""Escritura del CSV de mediciones con el esquema fijo del playbook (§8.2)."""
import csv
import fcntl
from pathlib import Path

COLUMNAS = [
    "timestamp_epoch", "engine", "profile", "query_id", "concurrency", "run_number",
    "throughput_qps", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms",
    "cpu_throttled_seconds", "max_rss_mb", "disk_spill", "status",
]


def agregar_fila(ruta, fila):
    """Añade una fila; crea el archivo con encabezado si no existe. Seguro entre procesos."""
    faltan = set(COLUMNAS) - set(fila)
    sobran = set(fila) - set(COLUMNAS)
    if faltan or sobran:
        raise ValueError(f"columnas inválidas: faltan {faltan}, sobran {sobran}")
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        if f.tell() == 0:
            csv.writer(f).writerow(COLUMNAS)
        csv.DictWriter(f, fieldnames=COLUMNAS).writerow(fila)
        fcntl.flock(f, fcntl.LOCK_UN)
