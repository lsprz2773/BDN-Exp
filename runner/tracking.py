"""Registro automático de cada corrida en los documentos de seguimiento (Markdown).

- Bitácora: una fila por repetición en la tabla "## Corridas".
- Control de matriz: marca el estado de la corrida y recalcula el resumen.
- Errores: una fila nueva (E-###) cuando la corrida termina en error u oom.

Las escrituras se serializan con un lock de archivo porque dos suites corren a la vez.
En modo prueba se escriben copias en results/prueba/ y no se toca el control de matriz.
seguimiento/ no está en el repo: en un clon nuevo los tres archivos se crean al vuelo.
"""
import fcntl
import re
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEGUIMIENTO = ROOT / "seguimiento"
PRUEBA = ROOT / "results" / "prueba"
LOCK = ROOT / "results" / "logs" / ".tracking.lock"

MARCA = {"ok": "✔", "spill": "⚠", "oom": "✖", "error": "✖"}
MOTOR_CORTO = {"mongodb": "MONGO", "postgresql": "PG"}

PLANTILLA_BITACORA = """# BITÁCORA DE {titulo}

## Corridas

| Fecha/hora inicio | Fecha/hora fin | Ronda | Suite | Motor | Perfil | query_id | Conc. | Rep. | status | QPS | P99 (ms) | Throttled (s) | Max RSS (MB) | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
"""
PLANTILLA_ERRORES = """# ERRORES DE {titulo}

## Errores abiertos o en corrección

| ID | Fecha/hora | Origen | Descripción | Causa | Corrección aplicada | ESTATUS |
|---|---|---|---|---|---|---|
"""


@contextmanager
def bloqueo():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield
        fcntl.flock(f, fcntl.LOCK_UN)


def id_corrida(perfil, motor, qid, conc, rep):
    return f"{perfil}:{MOTOR_CORTO[motor]}:{qid}:c{conc}:r{rep}"


def _celda(texto):
    return str(texto).replace("|", "/").replace("\n", " ")


def _insertar_en_tabla(ruta, encabezado, fila):
    """Inserta `fila` al final de la primera tabla que sigue a `encabezado`."""
    lineas = ruta.read_text(encoding="utf-8").split("\n")
    i = lineas.index(encabezado)
    while not lineas[i].startswith("|"):
        i += 1
    while i < len(lineas) and lineas[i].startswith("|"):
        i += 1
    # Quita la fila vacía de plantilla ("| | | ... |") si es la última
    if re.fullmatch(r"\|( \|)+", lineas[i - 1].strip()):
        lineas[i - 1] = fila
    else:
        lineas.insert(i, fila)
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def _archivos(prueba):
    if prueba:
        carpeta, bit, err, titulo = PRUEBA, "bitacora_prueba.md", "errores_prueba.md", "LA SUITE DE PRUEBA"
    else:
        carpeta, bit, err, titulo = SEGUIMIENTO, "BITACORA_EJECUCION.md", "ESTATUS_ERRORES.md", "EJECUCIÓN"
    carpeta.mkdir(parents=True, exist_ok=True)
    bit, err = carpeta / bit, carpeta / err
    if not bit.exists():
        bit.write_text(PLANTILLA_BITACORA.format(titulo=titulo), encoding="utf-8")
    if not err.exists():
        err.write_text(PLANTILLA_ERRORES.format(titulo=titulo), encoding="utf-8")
    return bit, err


def asegurar_control(corridas_por_perfil):
    """Crea seguimiento/CONTROL_MATRIZ.md si no existe (p. ej. en un clon nuevo del repo).
    `corridas_por_perfil`: lista ordenada de (motor, qid, conc, rep) de un perfil."""
    ruta = SEGUIMIENTO / "CONTROL_MATRIZ.md"
    if ruta.exists():
        return
    SEGUIMIENTO.mkdir(parents=True, exist_ok=True)
    n = len(corridas_por_perfil)
    partes = ["# CONTROL DE MATRIZ", "",
              "> Estado: ☐ Pendiente · ✔ ok · ⚠ spill · ✖ oom/error · ↻ Repetir", "",
              "## Resumen", "", "| Perfil | Ronda | Total | ✔ | ⚠ | ✖ | ↻ | ☐ |",
              "|---|---|---|---|---|---|---|---|"]
    # Ronda 1: A + C en paralelo (PC principal); ronda 2: B (otra PC)
    partes += [f"| {p} | {r} | {n} | 0 | 0 | 0 | 0 | {n} |" for p, r in (("A", "R1"), ("B", "R2"), ("C", "R1"))]
    partes.append(f"| **Total** | | **{3 * n}** | 0 | 0 | 0 | 0 | {3 * n} |")
    i = 0
    for p in "ABC":
        partes += ["", f"## Perfil {p}", "",
                   "| # | ID de corrida | Motor | query_id | Conc. | Rep. | Estado | Fecha/hora | Notas |",
                   "|---|---|---|---|---|---|---|---|---|"]
        for motor, qid, conc, rep in corridas_por_perfil:
            i += 1
            rid = id_corrida(p, motor, qid, conc, rep)
            partes.append(f"| {i} | `{rid}` | {MOTOR_CORTO[motor]} | {qid} | {conc} | {rep} | ☐ | | |")
    ruta.write_text("\n".join(partes) + "\n", encoding="utf-8")


def registrar(fila, notas, ronda, perfil, inicio, fin, prueba, falla_real=True):
    """falla_real=False: el `error` solo se debe a que ninguna consulta cupo en la ventana
    (resultado esperado en perfiles severos, D-26); va a la bitácora pero no a errores."""
    bitacora, errores = _archivos(prueba)
    rid = id_corrida(perfil, fila["engine"], fila["query_id"], fila["concurrency"], fila["run_number"])
    fmt = lambda t: datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    with bloqueo():
        _insertar_en_tabla(bitacora, "## Corridas", "| " + " | ".join(_celda(x) for x in [
            fmt(inicio), fmt(fin), f"R{ronda}" if ronda else "prueba", f"suite_{perfil.lower()}",
            fila["engine"], perfil, fila["query_id"], fila["concurrency"], fila["run_number"],
            fila["status"], fila["throughput_qps"], fila["latency_p99_ms"],
            fila["cpu_throttled_seconds"], fila["max_rss_mb"], "; ".join(notas) or "-",
        ]) + " |")

        if fila["status"] in ("error", "oom") and falla_real:
            texto = errores.read_text(encoding="utf-8")
            n = max([int(x) for x in re.findall(r"\| E-(\d+) \|", texto)] or [0]) + 1
            _insertar_en_tabla(errores, "## Errores abiertos o en corrección", "| " + " | ".join(_celda(x) for x in [
                f"E-{n:03d}", fmt(fin), rid, f"Corrida terminó en `{fila['status']}`: " + ("; ".join(notas) or "-"),
                "Por analizar", "-", "🔴 Abierto",
            ]) + " |")

        if not prueba:
            marcar_control(rid, MARCA[fila["status"]], fmt(fin), "; ".join(notas))


def marcar_control(rid, marca, fecha, nota):
    ruta = SEGUIMIENTO / "CONTROL_MATRIZ.md"
    lineas = ruta.read_text(encoding="utf-8").split("\n")
    for i, linea in enumerate(lineas):
        if f"| `{rid}` |" in linea:
            celdas = _celdas(linea)
            celdas[6], celdas[7], celdas[8] = marca, fecha, _celda(nota)[:150]
            lineas[i] = "| " + " | ".join(celdas) + " |"
            break
    else:
        raise KeyError(f"corrida {rid} no está en CONTROL_MATRIZ.md")
    ruta.write_text(_recalcular_resumen("\n".join(lineas)), encoding="utf-8")


def estado_control(rid):
    ruta = SEGUIMIENTO / "CONTROL_MATRIZ.md"
    if not ruta.exists():
        return None
    for linea in ruta.read_text(encoding="utf-8").split("\n"):
        if f"| `{rid}` |" in linea:
            return _celdas(linea)[6]
    return None


def _celdas(linea):
    # "| 1 | `A:...` | MONGO | Q1 | 1 | 1 | ☐ | | |" -> 9 celdas
    return [c.strip() for c in linea.strip()[1:-1].split("|")]


def _recalcular_resumen(texto):
    simbolos = ["✔", "⚠", "✖", "↻", "☐"]
    conteo = {p: {s: 0 for s in simbolos} for p in "ABC"}
    for m in re.finditer(r"^\| \d+ \| `([ABC]):[^`]+` \|(?:[^|]*\|){4} (\S) \|", texto, re.M):
        conteo[m.group(1)][m.group(2)] = conteo[m.group(1)].get(m.group(2), 0) + 1
    salida = []
    for linea in texto.split("\n"):
        m = re.match(r"^\| ([ABC]) \| (R\S*) \| (\d+) \|", linea)
        if m:
            c = conteo[m.group(1)]
            linea = f"| {m.group(1)} | {m.group(2)} | {m.group(3)} | " + " | ".join(str(c[s]) for s in simbolos) + " |"
        elif linea.startswith("| **Total** |"):
            tot = {s: sum(conteo[p][s] for p in "ABC") for s in simbolos}
            total = re.match(r"^\| \*\*Total\*\* \| \| (\*\*\d+\*\*) \|", linea).group(1)
            linea = f"| **Total** | | {total} | " + " | ".join(str(tot[s]) for s in simbolos) + " |"
        salida.append(linea)
    return "\n".join(salida)
