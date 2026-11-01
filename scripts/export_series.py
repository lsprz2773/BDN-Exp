#!/usr/bin/env python3
"""Exporta de Prometheus las series por corrida que el CSV no guarda (actividad F8).

Por cada fila de results/csv/mediciones_ronda{N}.csv:
- results/series/ronda{N}/<corrida>.csv.gz: cada 1 s desde el inicio del warmup hasta el fin
  de la medición, con la fase, el RSS (container_memory_rss, MB) y la CPU usada (núcleos,
  rate de container_cpu_usage_seconds_total). Sirve para la curva RSS.
- results/series/ronda{N}/resumen.csv: CPU-s usados y RSS máximo en la ventana de medición,
  base de M3 (CPU-s y MB por 1 000 documentos, D-09).

Correr en la misma PC que hizo la ronda, con el stack de monitoreo arriba y los contenedores
de las suites sin recrear (el id del contenedor se toma de docker inspect). Si Prometheus no
tiene la serie de un contenedor (E-010), se usa lo que guardó el runner desde la cgroup: la
serie de su muestreo propio (solo la ventana de medición) y cpu_cgroup.csv. La columna
`fuente` dice de dónde salió cada fila.

Uso: python3 -I scripts/export_series.py [ronda ...]   (por defecto, todas las del CSV)
"""
import csv
import gzip
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runner"))
from benchmark_runner import PERFILES, contenedor  # noqa: E402
from tracking import id_corrida  # noqa: E402

PROMETHEUS = "http://127.0.0.1:9090"
WARMUP, DURACION = 60, 300
PERFIL_CORTO = {v: k for k, v in PERFILES.items()}


def prom(ruta, **params):
    url = f"{PROMETHEUS}/api/v1/{ruta}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)["data"]["result"]


def rango(query, inicio, fin):
    res = prom("query_range", query=query, start=inicio, end=fin, step="1s")
    return {int(float(t)): float(v) for t, v in res[0]["values"]} if res else {}


def instante(query, t):
    res = prom("query", query=query, time=t)
    return float(res[0]["value"][1]) if res else None


def container_id(nombre):
    try:
        return subprocess.run(["docker", "inspect", "--format", "{{.Id}}", nombre],
                              check=True, capture_output=True, text=True).stdout.strip()
    except subprocess.CalledProcessError:
        return None


CLAVES = ("timestamp_epoch", "engine", "profile", "query_id", "concurrency", "run_number")


def cpu_cgroup(destino):
    ruta = destino / "cpu_cgroup.csv"
    if not ruta.exists():
        return {}
    with open(ruta, newline="", encoding="utf-8") as f:
        return {tuple(r[k] for k in CLAVES): r["cpu_seconds_medicion"] for r in csv.DictReader(f)}


def serie_runner(ruta):
    """RSS de la serie que dejó el muestreo propio del runner, si existe."""
    if not ruta.exists():
        return []
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        return [float(r["rss_mb"]) for r in csv.DictReader(f) if r["rss_mb"]]


def exportar(ronda):
    csv_path = ROOT / "results" / "csv" / f"mediciones_ronda{ronda}.csv"
    destino = ROOT / "results" / "series" / f"ronda{ronda}"
    destino.mkdir(parents=True, exist_ok=True)
    with open(csv_path, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    cpu_runner = cpu_cgroup(destino)

    ids, resumen, sin_serie = {}, [], 0
    for fila in filas:
        perfil = PERFIL_CORTO[fila["profile"]]
        motor, t0 = fila["engine"], int(fila["timestamp_epoch"])
        rid = id_corrida(perfil, motor, fila["query_id"], fila["concurrency"], fila["run_number"])
        nombre = contenedor(perfil, motor)
        if nombre not in ids:
            ids[nombre] = container_id(nombre)
        cid = ids[nombre]
        sel = f'{{id=~".*{cid}.*"}}'
        fin = t0 + DURACION

        rss = rango(f"max(container_memory_rss{sel}) / 1048576", t0 - WARMUP, fin) if cid else {}
        cpu = rango(f"sum(rate(container_cpu_usage_seconds_total{sel}[5s]))",
                    t0 - WARMUP, fin) if cid else {}
        cpu_s = instante(f"sum(increase(container_cpu_usage_seconds_total{sel}[{DURACION}s]))",
                         fin) if cid else None
        medidos = [v for t, v in rss.items() if t >= t0]
        ruta = destino / f"{rid.replace(':', '_')}.csv.gz"
        fuente = "prometheus"
        if not rss:
            # No se sobrescribe la serie que haya dejado el runner.
            medidos = serie_runner(ruta)
            cpu_s = cpu_runner.get(tuple(fila[k] for k in CLAVES)) or None
            fuente = "cgroup (runner)" if medidos or cpu_s else ""
            sin_serie += not medidos
        else:
            with gzip.open(ruta, "wt", encoding="utf-8") as f:
                f.write("t_epoch,fase,rss_mb,cpu_nucleos\n")
                for t in sorted(set(rss) | set(cpu)):
                    fase = "warmup" if t < t0 else "medicion"
                    r, c = rss.get(t), cpu.get(t)
                    f.write(f"{t},{fase},{'' if r is None else round(r, 1)},"
                            f"{'' if c is None else round(c, 4)}\n")

        resumen.append({
            "corrida": rid, "engine": motor, "profile": fila["profile"],
            "query_id": fila["query_id"], "concurrency": fila["concurrency"],
            "run_number": fila["run_number"], "status": fila["status"],
            "throughput_qps": fila["throughput_qps"],
            "consultas_medidas": round(float(fila["throughput_qps"] or 0) * DURACION),
            "cpu_seconds_medicion": "" if cpu_s is None else round(float(cpu_s), 3),
            "rss_max_mb_serie": round(max(medidos), 1) if medidos else "",
            "muestras": len(medidos),
            "fuente": fuente,
        })

    with open(destino / "resumen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(resumen[0]))
        w.writeheader()
        w.writerows(resumen)
    print(f"ronda {ronda}: {len(filas)} corridas, {len(filas) - sin_serie} con serie de RSS, "
          f"{sin_serie} sin serie -> {destino.relative_to(ROOT)}")


def main():
    rondas = sys.argv[1:] or sorted(p.stem.removeprefix("mediciones_ronda")
                                    for p in (ROOT / "results" / "csv").glob("mediciones_ronda*.csv"))
    for ronda in rondas:
        exportar(ronda)


if __name__ == "__main__":
    main()
