"""Orquestador de la matriz de mediciones de un perfil (playbook §6).

Recorre motores × query_id × concurrencia × repetición en un orden fijo, para que dos
suites lanzadas a la vez avancen en paralelo. Antes de cada corrida:
  1. enciende solo el motor que toca (D-21),
  2. espera en una barrera a las demás suites de la ronda y hace UN flush de caché
     compartido (drop_caches es global del host, D-07),
  3. ejecuta la corrida (warmup -> medición -> cooldown) y la registra al terminar.

Es reanudable: salta las corridas que CONTROL_MATRIZ.md ya marca como hechas.

Uso (normalmente vía scripts/run_benchmarks.sh):
  run_matrix.py --profile B --round 1 --parties B,C
  run_matrix.py --profile B --test --parties B,C          # suite de prueba (F5.5)
  run_matrix.py --profile A --only mongodb:Q1:1 --reps 1 --warmup 5 --duration 30 --cooldown 5 --test
"""
import argparse
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path

import benchmark_runner as br
import csv_writer
import metrics
import tracking

ROOT = br.ROOT
CONCURRENCIAS = (1, 10, 50)
HECHAS = {"✔", "⚠", "✖"}
TIMEOUT_BARRERA = 30 * 60


def guardar_entorno(carpeta, perfil, motor):
    """Límites Docker reales, imagen y versión del motor de la suite (diapositiva 5)."""
    nombre = br.contenedor(perfil, motor)
    inspect = subprocess.run(
        ["docker", "inspect", "--format",
         "imagen={{.Config.Image}} digest={{.Image}} NanoCpus={{.HostConfig.NanoCpus}} "
         "Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}}", nombre],
        capture_output=True, text=True).stdout.strip()
    cgroup = " ".join(f"{f}={metrics.cgroup_file(nombre, f)}" for f in ("cpu.max", "memory.max", "memory.swap.max"))
    if motor == "mongodb":
        version = subprocess.run(["docker", "exec", nombre, "mongosh", "--quiet", "--eval", "db.version()"],
                                 capture_output=True, text=True).stdout.strip()
    else:
        version = subprocess.run(["docker", "exec", nombre, "psql", "-U", "bench", "-d", "control_academico",
                                  "-tAc", "SELECT version()"], capture_output=True, text=True).stdout.strip()
    carpeta.mkdir(parents=True, exist_ok=True)
    with open(carpeta / f"{perfil}_{motor}.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} perfil={br.PERFILES[perfil]} motor={motor}\n"
                f"  {inspect}\n  {cgroup}\n  version={version}\n")


def guardar_evidencia(carpeta, rid, perfil, motor, inicio, fila, notas):
    """Logs del motor y eventos de memoria de una corrida con spill, OOM o error (diapositiva 10)."""
    nombre = br.contenedor(perfil, motor)
    desde = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(inicio - 5)) + "Z"
    logs = subprocess.run(["docker", "logs", "--since", desde, nombre], capture_output=True, text=True)
    try:
        eventos = metrics.cgroup_file(nombre, "memory.events")
    except subprocess.CalledProcessError:
        eventos = "(contenedor detenido)"
    lineas = (logs.stdout + logs.stderr).splitlines()
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"{rid.replace(':', '_')}.log").write_text(
        f"corrida: {rid}\nstatus: {fila['status']}  disk_spill: {fila['disk_spill']}\n"
        f"notas: {'; '.join(notas) or '-'}\n\n== memory.events\n{eventos}\n\n"
        f"== docker logs {nombre} desde {desde} (últimas 300 líneas de {len(lineas)})\n"
        + "\n".join(lineas[-300:]) + "\n", encoding="utf-8")


def matriz(reps):
    for motor in ("mongodb", "postgresql"):
        for qid in br.VARIANTES[motor]:
            for conc in CONCURRENCIAS:
                for rep in range(1, reps + 1):
                    yield motor, qid, conc, rep


def suite(perfil, accion, motor):
    nombre = "mongodb" if motor == "mongodb" else "postgres"
    subprocess.run([str(ROOT / "scripts" / "suite.sh"), perfil, accion, nombre],
                   check=True, capture_output=True)


def puerto_abierto(puerto, segundos):
    limite = time.time() + segundos
    while time.time() < limite:
        try:
            socket.create_connection(("127.0.0.1", puerto), timeout=2).close()
            return True
        except OSError:
            time.sleep(1)
    return False


def encender(perfil, motor):
    """Enciende el motor y comprueba que su puerto responde desde el host. Docker Desktop
    a veces no publica el puerto al arrancar dos suites a la vez (E-006): se reintenta."""
    env = br.perfil_env(perfil)
    puerto = int(env["MONGO_PORT"] if motor == "mongodb" else env["PG_PORT"])
    for intento in range(1, 4):
        suite(perfil, "up", motor)
        if puerto_abierto(puerto, 20):
            return
        print(f"  ! puerto {puerto} sin respuesta (intento {intento}); se reinicia el contenedor", flush=True)
        suite(perfil, "stop", motor)
    raise RuntimeError(f"el puerto {puerto} de {motor} no responde tras 3 intentos")


def barrera(tag, paso, perfil, partes):
    """Todas las suites llegan; la primera (orden alfabético) hace el flush y libera."""
    d = ROOT / "results" / "logs" / "barrera" / tag / f"paso_{paso:03d}"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{perfil}.listo").touch()
    limite = time.time() + TIMEOUT_BARRERA
    while not all((d / f"{p}.listo").exists() for p in partes):
        if time.time() > limite:
            print(f"  ! barrera {paso}: timeout esperando a {partes}; se sigue solo", flush=True)
            break
        time.sleep(0.5)
    if perfil == min(partes):
        metrics.drop_caches()
        (d / "flush.hecho").touch()
    else:
        while not (d / "flush.hecho").exists() and time.time() < limite:
            time.sleep(0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, choices=["A", "B", "C"])
    ap.add_argument("--round", type=int, default=0)
    ap.add_argument("--parties", default=None, help="suites que corren a la vez, p. ej. B,C")
    ap.add_argument("--session", default=None,
                    help="nombre común de la sesión de barrera (obligatorio con varias partes; "
                         "usar uno nuevo al reanudar)")
    ap.add_argument("--test", action="store_true", help="suite de prueba: salida en results/prueba/")
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--warmup", type=int, default=None)
    ap.add_argument("--duration", type=int, default=None)
    ap.add_argument("--cooldown", type=int, default=None)
    ap.add_argument("--only", default=None, help="filtro motor[:query_id[:concurrencia]]")
    a = ap.parse_args()

    if a.test:
        reps, warmup, duracion, cooldown = 1, 5, 20, 5
        csv_path = ROOT / "results" / "prueba" / "mediciones_prueba.csv"
        raw_dir = ROOT / "results" / "prueba" / "raw"
        evid_dir = ROOT / "results" / "prueba" / "evidencia_spill_oom"
        entorno_dir = ROOT / "results" / "prueba" / "entorno"
        tag = "prueba"
    else:
        if not a.round:
            sys.exit("--round es obligatorio fuera de --test")
        reps, warmup, duracion, cooldown = 3, 60, 300, 60
        csv_path = ROOT / "results" / "csv" / "mediciones.csv"
        raw_dir = ROOT / "results" / "raw" / f"ronda{a.round}"
        evid_dir = ROOT / "results" / "evidencia_spill_oom" / f"ronda{a.round}"
        entorno_dir = ROOT / "results" / "entorno" / f"ronda{a.round}"
        tag = f"ronda{a.round}"
    reps = a.reps or reps
    warmup = warmup if a.warmup is None else a.warmup
    duracion = a.duration or duracion
    cooldown = cooldown if a.cooldown is None else a.cooldown
    partes = sorted((a.parties or a.profile).split(","))
    if len(partes) > 1 and not a.session:
        sys.exit("--session es obligatorio cuando hay varias partes (mismo valor en todas las suites)")
    tag = f"{tag}_{a.session or int(time.time())}"

    corridas = list(matriz(reps))
    if a.only:
        filtro = a.only.split(":")
        corridas = [c for c in corridas if all(str(x) == f for x, f in zip(c, filtro))]
    print(f"Suite {a.profile} | {'PRUEBA' if a.test else f'ronda {a.round}'} | partes {partes} | "
          f"{len(corridas)} corridas | ventanas {warmup}/{duracion}/{cooldown} s", flush=True)

    motor_actual = None
    for paso, (motor, qid, conc, rep) in enumerate(corridas, 1):
        rid = tracking.id_corrida(a.profile, motor, qid, conc, rep)
        hecha = not a.test and tracking.estado_control(rid) in HECHAS
        barrera(tag, paso, a.profile, partes)
        if hecha:
            print(f"[{paso}/{len(corridas)}] {rid} ya hecha, se omite", flush=True)
            continue
        print(f"[{paso}/{len(corridas)}] {rid} ...", end=" ", flush=True)
        inicio = time.time()
        raw = raw_dir / f"{rid.replace(':', '_')}.csv.gz"
        try:
            if motor != motor_actual:
                otro = "postgresql" if motor == "mongodb" else "mongodb"
                suite(a.profile, "stop", otro)
                encender(a.profile, motor)
                motor_actual = motor
                guardar_entorno(entorno_dir, a.profile, motor)
            fila, notas, falla_real = br.ejecutar_corrida(a.profile, motor, qid, conc, rep,
                                                          warmup, duracion, cooldown, raw)
        except Exception as exc:   # la corrida no pudo ni medirse: se registra como error
            traceback.print_exc()
            fila = {c: "" for c in csv_writer.COLUMNAS}
            fila.update(timestamp_epoch=int(inicio), engine=motor, profile=br.PERFILES[a.profile],
                        query_id=qid, concurrency=conc, run_number=rep, status="error")
            notas, falla_real = [f"{type(exc).__name__}: {str(exc)[:200]}"], True
            motor_actual = None   # fuerza a reiniciar el motor en la siguiente
        if fila["status"] in ("spill", "oom") or fila["disk_spill"] == "true" or falla_real:
            try:
                guardar_evidencia(evid_dir, rid, a.profile, motor, inicio, fila, notas)
            except Exception as exc:
                print(f"  ! no se pudo guardar la evidencia: {exc}", flush=True)
        if motor_actual and not metrics.estado_contenedor(br.contenedor(a.profile, motor))["running"]:
            motor_actual = None   # el motor cayó (OOM): se vuelve a levantar en la siguiente
        csv_writer.agregar_fila(csv_path, fila)
        tracking.registrar(fila, notas, a.round, a.profile, inicio, time.time(), a.test, falla_real)
        print(f"{fila['status']} | qps={fila['throughput_qps']} p99={fila['latency_p99_ms']} "
              f"thr={fila['cpu_throttled_seconds']} rss={fila['max_rss_mb']}", flush=True)

    if motor_actual:
        suite(a.profile, "stop", motor_actual)
    print("Fin de la suite", flush=True)


if __name__ == "__main__":
    main()
