#!/usr/bin/env python3
"""Consolida las mediciones y genera las tablas y figuras del reporte (actividad F8).

Entradas: results/csv/mediciones_ronda*.csv, results/series/ronda*/ (resumen.csv y series
por corrida) y results/evidencia_spill_oom/ronda*/ (bytes de spill de PostgreSQL).
Salidas:
- report/datos/consolidado.csv: una fila por celda (perfil × motor × query_id × concurrencia)
  con la mediana y el rango de las 3 repeticiones (D-08) y M3 (D-09).
- report/tablas/*.tex: tablas LaTeX que \\input{} el reporte.
- report/figures/*.pdf: P99 vs concurrencia, throttling vs QPS y curvas RSS.

Funciona con los perfiles que haya: al llegar la ronda 2 basta con volver a correrlo.

Uso: ~/.venvs/bdn/bin/python -I scripts/analyze_results.py
"""
import csv
import gzip
import os
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report"
PERFIL_CORTO = {"PROFILE_A_BASELINE": "A", "PROFILE_B_MEDIUM": "B", "PROFILE_C_SEVERE": "C"}
CPUS = {"A": 4, "B": 2, "C": 1}
MEM = {"A": 4096, "B": 2048, "C": 1024}
MOTORES = ("mongodb", "postgresql")
NOMBRE_MOTOR = {"mongodb": "MongoDB", "postgresql": "PostgreSQL"}
QUERIES = {"mongodb": ("Q1", "Q2_DISK0", "Q2_DISK1"), "postgresql": ("Q1", "Q2_WM4", "Q2_WM64")}
# Las variantes de Q2 se emparejan por papel: memoria restringida / memoria amplia.
PAPEL = {"Q1": "Q1", "Q2_DISK0": "Q2r", "Q2_WM4": "Q2r", "Q2_DISK1": "Q2a", "Q2_WM64": "Q2a"}
TITULO_PAPEL = {"Q1": "Q1\nunwind + group",
                "Q2r": "Q2 restringida\nDISK0 / WM4",
                "Q2a": "Q2 amplia\nDISK1 / WM64"}
CONC = (1, 10, 50)
VENTANA = 300
DOCS = 500_000   # documentos de la colección que evalúa cada consulta (D-09)

# Paleta de referencia (dataviz): slot 1 azul, slot 2 naranja. El perfil va en el marcador
# y el trazo, así la identidad nunca depende solo del color (impresión en gris incluida).
COLOR = {"mongodb": "#2a78d6", "postgresql": "#eb6834"}
MARCA = {"A": "o", "B": "s", "C": "^"}
TRAZO = {"A": "-", "B": "--", "C": ":"}
TINTA, TINTA2, REJILLA = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "axes.edgecolor": TINTA2, "axes.labelcolor": TINTA, "xtick.color": TINTA2,
    "ytick.color": TINTA2, "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "lines.linewidth": 1.6, "lines.markersize": 5, "savefig.bbox": "tight",
})


def num(x):
    return None if x in ("", None) else float(x)


def mediana(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def cargar():
    filas = []
    for p in sorted((ROOT / "results" / "csv").glob("mediciones_ronda*.csv")):
        ronda = p.stem.removeprefix("mediciones_ronda")
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r["perfil"], r["ronda"] = PERFIL_CORTO[r["profile"]], ronda
                filas.append(r)
    cpu = {}
    for p in (ROOT / "results" / "series").glob("ronda*/resumen.csv"):
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cpu[r["corrida"]] = (num(r["cpu_seconds_medicion"]), r["fuente"])
    spill = {}
    for p in (ROOT / "results" / "evidencia_spill_oom").glob("ronda*/*.log"):
        texto = p.read_text(encoding="utf-8", errors="replace")[:4000]
        m = re.search(r"corrida: (\S+)", texto)
        b = re.search(r"spill: \+(\d+) \(temp_bytes\)", texto)
        k = re.search(r"oom_kill en el contenedor: (\d+)", texto)
        if m:
            spill[m.group(1)] = (int(b.group(1)) if b else None, int(k.group(1)) if k else 0)
    return filas, cpu, spill


def rid(r):
    corto = "MONGO" if r["engine"] == "mongodb" else "PG"
    return f"{r['perfil']}:{corto}:{r['query_id']}:c{r['concurrency']}:r{r['run_number']}"


def consolidar(filas, cpu, spill):
    grupos = defaultdict(list)
    for r in filas:
        grupos[(r["perfil"], r["engine"], r["query_id"], int(r["concurrency"]))].append(r)
    celdas = {}
    for k, reps in grupos.items():
        perfil, motor, qid, conc = k
        c = {"perfil": perfil, "engine": motor, "query_id": qid, "concurrency": conc,
             "reps": len(reps), "estados": [r["status"] for r in reps]}
        for col in ("throughput_qps", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms",
                    "cpu_throttled_seconds", "max_rss_mb"):
            v = [num(r[col]) for r in reps]
            c[col] = mediana(v)
            vv = [x for x in v if x is not None]
            c[col + "_min"], c[col + "_max"] = (min(vv), max(vv)) if vv else (None, None)
        # CPU-s de la ventana; si falta (B:MONGO:Q1, E-010) se estima: B no puede pasar de
        # su cuota y, si la misma celda en A usó menos, la demanda es la misma (D-09).
        cpus, estimado = [], False
        for r in reps:
            v = cpu.get(rid(r), (None, ""))[0]
            if v is None:
                ref = [cpu.get(rid({**x, "perfil": "A"}), (None,))[0] for x in reps]
                ref = mediana(ref)
                v = CPUS[perfil] * VENTANA if ref is None else min(CPUS[perfil] * VENTANA, ref)
                estimado = True
            cpus.append(v)
        c["cpu_seconds"], c["cpu_estimado"] = mediana(cpus), estimado
        consultas = [round(num(r["throughput_qps"]) * VENTANA) for r in reps]
        porq = [cs / q for cs, q in zip(cpus, consultas) if q]
        c["consultas"] = mediana(consultas)
        c["cpu_s_por_1000_docs"] = mediana([x / DOCS * 1000 for x in porq]) if porq else None
        c["mb_por_1000_docs"] = None if c["max_rss_mb"] is None else c["max_rss_mb"] / DOCS * 1000
        sp = [spill.get(rid(r), (None, 0)) for r in reps]
        c["spill_gb"] = mediana([b / 1e9 for b, _ in sp if b])
        c["oom_kills"] = sum(n for _, n in sp)
        celdas[k] = c
    return celdas


# --- Salidas -----------------------------------------------------------------

def fmt(x, d=1, escala=1.0):
    if x is None:
        return "--"
    x = x / escala
    return f"{x:,.{d}f}".replace(",", "\\,")


def estado_corto(estados):
    cuenta = defaultdict(int)
    for e in estados:
        cuenta[e] += 1
    orden = ("ok", "spill", "error", "oom")
    return ", ".join(f"{cuenta[e]}\\,{e}" for e in orden if cuenta[e])


def escribir_csv(celdas):
    (OUT / "datos").mkdir(parents=True, exist_ok=True)
    cols = ["perfil", "engine", "query_id", "concurrency", "reps", "estados", "throughput_qps",
            "throughput_qps_min", "throughput_qps_max", "latency_p50_ms", "latency_p95_ms",
            "latency_p99_ms", "latency_p99_ms_min", "latency_p99_ms_max", "cpu_throttled_seconds",
            "max_rss_mb", "spill_gb", "oom_kills", "consultas", "cpu_seconds", "cpu_estimado",
            "cpu_s_por_1000_docs", "mb_por_1000_docs"]
    with open(OUT / "datos" / "consolidado.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for k in sorted(celdas):
            w.writerow({**celdas[k], "estados": "/".join(celdas[k]["estados"])})


def tabla_resultados(celdas, perfil):
    lineas = [
        "\\begin{tabular}{llrlrrrrrr}", "\\toprule",
        "Motor & Query & Conc. & Estado & QPS & P50 (s) & P95 (s) & P99 (s) & Throttled (s) & RSS (MB) \\\\",
        "\\midrule"]
    for motor in MOTORES:
        for qid in QUERIES[motor]:
            for conc in CONC:
                c = celdas.get((perfil, motor, qid, conc))
                if not c:
                    continue
                q = qid.replace("_", "\\_")
                lineas.append(
                    f"{NOMBRE_MOTOR[motor]} & {q} & {conc} & {estado_corto(c['estados'])} & "
                    f"{fmt(c['throughput_qps'], 2)} & {fmt(c['latency_p50_ms'], 2, 1000)} & "
                    f"{fmt(c['latency_p95_ms'], 2, 1000)} & {fmt(c['latency_p99_ms'], 2, 1000)} & "
                    f"{fmt(c['cpu_throttled_seconds'], 0)} & {fmt(c['max_rss_mb'], 0)} \\\\")
            lineas.append("\\addlinespace[2pt]")
        if motor == "mongodb":
            lineas.append("\\midrule")
    lineas += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lineas) + "\n"


def tabla_spill(celdas):
    lineas = ["\\begin{tabular}{llrlrr}", "\\toprule",
              "Perfil & Motor / query & Conc. & Estado (3 rep.) & Spill (GB/ventana) & oom\\_kill \\\\",
              "\\midrule"]
    for k in sorted(celdas):
        c = celdas[k]
        if all(e == "ok" for e in c["estados"]) and not c["spill_gb"]:
            continue
        q = c["query_id"].replace("_", "\\_")
        lineas.append(f"{c['perfil']} & {NOMBRE_MOTOR[c['engine']]} {q} & {c['concurrency']} & "
                      f"{estado_corto(c['estados'])} & {fmt(c['spill_gb'], 1)} & {c['oom_kills']} \\\\")
    lineas += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lineas) + "\n"


def tabla_m3(celdas, perfiles):
    lineas = ["\\begin{tabular}{ll" + "rr" * len(perfiles) + "}", "\\toprule",
              " & & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{Perfil {p}}}" for p in perfiles) + " \\\\",
              " ".join(f"\\cmidrule(lr){{{3 + 2 * i}-{4 + 2 * i}}}" for i in range(len(perfiles))),
              "Motor & Query & " + " & ".join("CPU-s & MB" for _ in perfiles) + " \\\\", "\\midrule"]
    for motor in MOTORES:
        for qid in QUERIES[motor]:
            celdas_fila = []
            for p in perfiles:
                c = celdas.get((p, motor, qid, 1))   # 1 cliente: costo por consulta sin cola
                if not c:
                    celdas_fila += ["--", "--"]
                    continue
                marca = "$^\\dagger$" if c["cpu_estimado"] else ""
                celdas_fila += [fmt(c["cpu_s_por_1000_docs"], 4) + marca, fmt(c["mb_por_1000_docs"], 3)]
            lineas.append(f"{NOMBRE_MOTOR[motor]} & {qid.replace('_', chr(92) + '_')} & "
                          + " & ".join(celdas_fila) + " \\\\")
        if motor == "mongodb":
            lineas.append("\\midrule")
    lineas += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lineas) + "\n"


def leyenda(ax, perfiles, loc="upper left"):
    h = [Line2D([], [], color=COLOR[m], lw=2, label=NOMBRE_MOTOR[m]) for m in MOTORES]
    h += [Line2D([], [], color=TINTA2, marker=MARCA[p], ls=TRAZO[p], label=f"Perfil {p}")
          for p in perfiles]
    ax.legend(handles=h, loc=loc, fontsize=8)


def fig_p99(celdas, perfiles):
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8), sharey=True)
    techo = VENTANA * 1.6
    for ax, papel in zip(axes, ("Q1", "Q2r", "Q2a")):
        for motor in MOTORES:
            qid = next(q for q in QUERIES[motor] if PAPEL[q] == papel)
            for p in perfiles:
                xs, ys, lo, hi, cens = [], [], [], [], []
                for conc in CONC:
                    c = celdas.get((p, motor, qid, conc))
                    if not c:
                        continue
                    if c["latency_p99_ms"] is None:
                        cens.append(conc)
                        continue
                    y = c["latency_p99_ms"] / 1000
                    xs.append(conc), ys.append(y)
                    lo.append(y - c["latency_p99_ms_min"] / 1000)
                    hi.append(c["latency_p99_ms_max"] / 1000 - y)
                ax.errorbar(xs, ys, yerr=[lo, hi], color=COLOR[motor], marker=MARCA[p],
                            ls=TRAZO[p], capsize=2, elinewidth=0.8, markeredgecolor="white",
                            markeredgewidth=0.6)
                if cens:   # ninguna consulta terminó en 300 s: latencia censurada
                    ax.scatter(cens, [techo] * len(cens), marker=MARCA[p], facecolors="none",
                               edgecolors=COLOR[motor], s=36, linewidths=1.2, zorder=3)
        ax.axhline(VENTANA, color=TINTA2, lw=0.8, ls=(0, (4, 3)))
        ax.set_xscale("log"), ax.set_yscale("log")
        ax.set_xticks(CONC, [str(c) for c in CONC]), ax.minorticks_off()
        ax.set_title(TITULO_PAPEL[papel], loc="left", color=TINTA)
        ax.set_xlabel("Clientes concurrentes")
    axes[0].set_ylabel("P99 (s, escala log)")
    axes[1].text(1, VENTANA * 0.72, "ventana 300 s", fontsize=7, color=TINTA2)
    axes[1].text(1, techo * 0.72, "sin consultas terminadas", fontsize=7, color=TINTA2)
    leyenda(axes[2], perfiles, loc="lower right")
    guardar(fig, "p99_vs_concurrencia")


def fig_throttling(celdas, perfiles):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for ax, papeles, titulo in ((axes[0], ("Q1",), "Q1"), (axes[1], ("Q2r", "Q2a"), "Q2 (ambas variantes)")):
        for motor in MOTORES:
            for qid in QUERIES[motor]:
                if PAPEL[qid] not in papeles:
                    continue
                for p in perfiles:
                    pts = [celdas.get((p, motor, qid, conc)) for conc in CONC]
                    pts = [c for c in pts if c and c["cpu_throttled_seconds"] is not None]
                    x = [c["cpu_throttled_seconds"] for c in pts]
                    y = [max(c["throughput_qps"], 0.005) for c in pts]
                    ax.plot(x, y, color=COLOR[motor], marker=MARCA[p], ls=TRAZO[p], lw=1.0,
                            markeredgecolor="white", markeredgewidth=0.6)
                    if pts and qid in ("Q1", "Q2_DISK1", "Q2_WM64"):
                        ax.annotate(f"c{pts[-1]['concurrency']}", (x[-1], y[-1]), fontsize=6.5,
                                    color=TINTA2, xytext=(3, 2), textcoords="offset points")
        ax.set_yscale("log")
        ax.set_xlabel("Tiempo de throttling CFS en la ventana (s)")
        ax.set_title(titulo, loc="left", color=TINTA)
    axes[0].set_ylabel("Throughput (QPS, escala log)")
    leyenda(axes[1], perfiles, loc="upper right")
    guardar(fig, "throttling_vs_qps")


def serie(perfil, motor, qid, conc, rep, filas):
    corto = "MONGO" if motor == "mongodb" else "PG"
    fila = next((r for r in filas if r["perfil"] == perfil and r["engine"] == motor
                 and r["query_id"] == qid and int(r["concurrency"]) == conc
                 and int(r["run_number"]) == rep), None)
    if not fila:
        return None
    ruta = ROOT / "results" / "series" / f"ronda{fila['ronda']}" / f"{perfil}_{corto}_{qid}_c{conc}_r{rep}.csv.gz"
    if not ruta.exists():
        return None
    t0 = int(fila["timestamp_epoch"])
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        pts = [(int(r["t_epoch"]) - t0, float(r["rss_mb"])) for r in csv.DictReader(f) if r["rss_mb"]]
    return pts


def fig_rss(filas, perfiles):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.6), sharex=True)
    for fila_ax, conc in zip(axes, (10, 50)):
        for ax, motor in zip(fila_ax, MOTORES):
            for p in perfiles:
                pts = serie(p, motor, "Q1", conc, 1, filas)
                if pts:
                    ax.plot([t for t, _ in pts], [v for _, v in pts], color=COLOR[motor],
                            ls=TRAZO[p], lw=1.1, label=f"Perfil {p} (límite {MEM[p]} MB)")
            ax.axvspan(-60, 0, color=REJILLA, alpha=0.5, lw=0)
            ax.set_title(f"{NOMBRE_MOTOR[motor]} · Q1 · {conc} clientes", loc="left", color=TINTA)
    h = [Line2D([], [], color=TINTA2, ls=TRAZO[p], label=f"Perfil {p} (límite {MEM[p]} MB)")
         for p in perfiles]
    fig.legend(handles=h, loc="lower center", ncol=len(perfiles), fontsize=8,
               bbox_to_anchor=(0.5, -0.04))
    fig.subplots_adjust(hspace=0.35)
    for ax in axes[1]:
        ax.set_xlabel("s desde el inicio de la medición")
    for ax in axes[:, 0]:
        ax.set_ylabel("RSS (MB)")
    guardar(fig, "curva_rss_q1")


def guardar(fig, nombre):
    fig.savefig(OUT / "figures" / f"{nombre}.pdf")
    if os.environ.get("PNG_DIR"):   # vista previa para revisar la figura sin LaTeX
        fig.savefig(Path(os.environ["PNG_DIR"]) / f"{nombre}.png", dpi=130)
    plt.close(fig)


def main():
    filas, cpu, spill = cargar()
    celdas = consolidar(filas, cpu, spill)
    perfiles = [p for p in "ABC" if any(k[0] == p for k in celdas)]
    for d in ("tablas", "figures", "datos"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    escribir_csv(celdas)
    for p in perfiles:
        (OUT / "tablas" / f"resultados_{p}.tex").write_text(tabla_resultados(celdas, p), encoding="utf-8")
    (OUT / "tablas" / "spill_oom.tex").write_text(tabla_spill(celdas), encoding="utf-8")
    (OUT / "tablas" / "m3.tex").write_text(tabla_m3(celdas, perfiles), encoding="utf-8")
    fig_p99(celdas, perfiles)
    fig_throttling(celdas, perfiles)
    fig_rss(filas, perfiles)
    print(f"{len(filas)} corridas, {len(celdas)} celdas, perfiles {perfiles} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
