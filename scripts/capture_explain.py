#!/usr/bin/env python3
"""Captura los planes de ejecución de cada query y variante por perfil (actividad F3.4).

MongoDB:    explain("executionStats") del pipeline     -> results/explain/mongodb/<P>_<query_id>.json
PostgreSQL: EXPLAIN (ANALYZE, BUFFERS)                 -> results/explain/postgresql/<P>_<query_id>.txt

Al final imprime un resumen: tiempo, uso del índice de fecha, método de ordenamiento
y si hubo volcado a disco (spill) o error por memoria.

Uso: python3 -I scripts/capture_explain.py [A B C]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dbexec import COLL, ROOT, VARIANTES, mongo_eval, pipeline, psql, sql, suite

OUT = ROOT / "results" / "explain"


def buscar(obj, clave):
    """Todos los valores de `clave` en un JSON anidado."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == clave:
                yield v
            yield from buscar(v, clave)
    elif isinstance(obj, list):
        for v in obj:
            yield from buscar(v, clave)


def explain_mongo(perfil, qid, base, opciones):
    js = (f"try {{ EJSON.stringify(db.{COLL}.explain('executionStats').aggregate("
          f"{pipeline(base)}, {json.dumps(opciones)}), {{relaxed: true}}) }}"
          " catch (e) { JSON.stringify({error: e.message, code: e.code}) }")
    plan = json.loads(mongo_eval(perfil, js))
    (OUT / "mongodb" / f"{perfil}_{qid}.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    if "error" in plan:
        return {"error": plan["error"][:120]}
    etapas = [s for s in buscar(plan, "stage")] + [k for st in buscar(plan, "stages") for e in st for k in e]
    return {
        "ms": max(buscar(plan, "executionTimeMillisEstimate"), default=None),
        "indice": "IXSCAN" in etapas,
        "usedDisk": any(buscar(plan, "usedDisk")),
        "spills": sum(v for v in buscar(plan, "spills") if isinstance(v, int)),
    }


def explain_pg(perfil, qid, base, work_mem):
    pre = [f"SET work_mem = '{work_mem}'"] if work_mem else []
    plan = psql(perfil, *pre, f"EXPLAIN (ANALYZE, BUFFERS) {sql(base)}")
    (OUT / "postgresql" / f"{perfil}_{qid}.txt").write_text(plan + "\n", encoding="utf-8")
    t = re.search(r"Execution Time: ([\d.]+) ms", plan)
    sort = re.findall(r"Sort Method: ([^\n]+)", plan)
    return {
        "ms": float(t.group(1)) if t else None,
        "indice": "idx_resultados_cerrado_en" in plan,
        "sort": "; ".join(s.strip() for s in sort) or "-",
        "disco": bool(re.search(r"external|Disk Usage: [1-9]|Disk: [1-9]", plan)),
    }


def main():
    perfiles = sys.argv[1:] or ["A", "B", "C"]
    for d in ("mongodb", "postgresql"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for perfil in perfiles:
        print(f"== Perfil {perfil}")
        suite(perfil, "up", "mongodb")
        for qid, (base, opciones) in VARIANTES["mongodb"].items():
            print(f"  mongodb    {qid:9} {explain_mongo(perfil, qid, base, opciones)}")
        suite(perfil, "stop", "mongodb")
        suite(perfil, "up", "postgres")
        for qid, (base, work_mem) in VARIANTES["postgresql"].items():
            print(f"  postgresql {qid:9} {explain_pg(perfil, qid, base, work_mem)}")
        suite(perfil, "stop", "postgres")


if __name__ == "__main__":
    main()
