"""Utilidades compartidas para ejecutar las queries de queries/ dentro de los contenedores.

Se usa desde los scripts de validación y de captura de planes (no desde el runner, que
abre conexiones directas con pymongo y psycopg).
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUERIES = ROOT / "queries"
DB = "control_academico"
COLL = "resultados_unidad"

# query_id -> (archivo base, opciones de Mongo, SET de PostgreSQL)
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


def sh(*cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}...: {r.stderr.strip()[:500]}")
    return r


def suite(perfil, accion, motor=None):
    args = [str(ROOT / "scripts" / "suite.sh"), perfil, accion] + ([motor] if motor else [])
    sh(*args)


def contenedor(perfil, motor):
    return f"suite_{perfil.lower()}-{'mongodb' if motor == 'mongodb' else 'postgres'}-1"


def pipeline(nombre):
    return (QUERIES / "mongodb" / f"{nombre}.json").read_text(encoding="utf-8")


def sql(nombre):
    return (QUERIES / "postgresql" / f"{nombre}.sql").read_text(encoding="utf-8").strip().rstrip(";")


def mongo_eval(perfil, js):
    r = sh("docker", "exec", contenedor(perfil, "mongodb"), "mongosh", "--quiet", DB, "--eval", js)
    return r.stdout.strip()


def psql(perfil, *comandos):
    args = ["docker", "exec", contenedor(perfil, "postgresql"), "psql", "-v", "ON_ERROR_STOP=1",
            "-U", "bench", "-d", DB, "-tAq"]
    for c in comandos:
        args += ["-c", c]
    return sh(*args).stdout.strip()


def mongo_aggregate(perfil, nombre, opciones):
    js = (f"EJSON.stringify(db.{COLL}.aggregate({pipeline(nombre)}, {json.dumps(opciones)}).toArray(),"
          " {relaxed: true})")
    return json.loads(mongo_eval(perfil, js))


def pg_query(perfil, nombre, work_mem=None):
    pre = [f"SET work_mem = '{work_mem}'"] if work_mem else []
    out = psql(perfil, *pre, f"SELECT coalesce(json_agg(t), '[]') FROM ({sql(nombre)}) t")
    return json.loads(out)   # json_agg separa elementos con saltos de línea
