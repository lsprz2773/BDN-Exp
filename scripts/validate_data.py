#!/usr/bin/env python3
"""Valida el dataset y su carga en las suites (actividad F2.5).

1. NDJSON: número de documentos, formato de fecha (100 %), ids únicos, 2-4 criterios,
   porcentajes que suman 100 y calificación final coherente.
2. Por cada suite: conteos en MongoDB y PostgreSQL, índices exigidos (y ninguno sobre
   calificacion.final) y muestras idénticas en los dos motores y en el NDJSON.

Uso: python3 -I scripts/validate_data.py [A B C]   (las suites deben poder levantarse)
"""
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "generated" / "resultados_unidad.ndjson"
DB = "control_academico"
FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
N_ESPERADO = 500_000
N_MUESTRA = 25

errores = []


def check(cond, msg):
    print(("  OK  " if cond else "  FALLA ") + msg)
    if not cond:
        errores.append(msg)


def sh(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def validar_ndjson():
    print(f"== NDJSON {DATA.name}")
    ids, n, fechas_mal, pct_mal, final_mal, k_mal = set(), 0, 0, 0, 0, 0
    with open(DATA, encoding="utf-8") as f:
        for linea in f:
            doc = json.loads(linea)
            n += 1
            ids.add(doc["resultado_id"])
            fechas_mal += not FECHA_RE.match(doc["cerrado_en"])
            desglose = doc["calificacion"]["desglose"]
            k_mal += not 2 <= len(desglose) <= 4
            pct_mal += sum(d["porcentaje"] for d in desglose) != 100
            final = round(sum(d["porcentaje"] * d["promedio"] for d in desglose) / 100, 2)
            final_mal += abs(final - doc["calificacion"]["final"]) > 0.005
    check(n == N_ESPERADO, f"{n} documentos (esperados {N_ESPERADO})")
    check(len(ids) == n, f"resultado_id únicos: {len(ids)}")
    check(fechas_mal == 0, f"cerrado_en con formato YYYY-MM-DDTHH:MM:SSZ en el 100 % ({fechas_mal} mal)")
    check(k_mal == 0, f"desglose de 2 a 4 criterios ({k_mal} mal)")
    check(pct_mal == 0, f"porcentajes suman 100 ({pct_mal} mal)")
    check(final_mal == 0, f"calificacion.final = Σ(porcentaje×promedio)/100 ({final_mal} mal)")

    # Muestra fija para comparar entre motores; se guardan solo esas líneas
    muestra = set(random.Random(7).sample(sorted(ids), N_MUESTRA))
    docs = {}
    with open(DATA, encoding="utf-8") as f:
        for linea in f:
            doc = json.loads(linea)
            if doc["resultado_id"] in muestra:
                docs[doc["resultado_id"]] = doc
    return n, docs


def validar_suite(perfil, n, docs):
    p = perfil.lower()
    mongo, pg = f"suite_{p}-mongodb-1", f"suite_{p}-postgres-1"
    print(f"== Suite {perfil}")
    sh(str(ROOT / "scripts" / "suite.sh"), perfil, "up")

    def mongo_eval(js):
        return sh("docker", "exec", mongo, "mongosh", "--quiet", DB, "--eval", js)

    def psql(sql):
        return sh("docker", "exec", pg, "psql", "-U", "bench", "-d", DB, "-tAc", sql)

    n_m = int(mongo_eval("db.resultados_unidad.countDocuments()"))
    n_p = int(psql("SELECT count(*) FROM resultados_unidad"))
    check(n_m == n, f"MongoDB: {n_m} documentos")
    check(n_p == n, f"PostgreSQL: {n_p} filas")

    idx_m = json.loads(mongo_eval("JSON.stringify(db.resultados_unidad.getIndexes().map(i => i.key))"))
    claves_m = sorted(k for i in idx_m for k in i)
    check(claves_m == ["_id", "cerrado_en", "resultado_id"], f"índices MongoDB: {claves_m}")
    idx_p = psql("SELECT string_agg(indexdef, ' ; ') FROM pg_indexes WHERE tablename = 'resultados_unidad'")
    check("(id)" in idx_p and "cerrado_en" in idx_p and "final" not in idx_p and "gin" not in idx_p.lower(),
          f"índices PostgreSQL: PK id + B-Tree cerrado_en ({idx_p.count(';') + 1} en total)")
    ok_id = psql("SELECT count(*) FROM resultados_unidad WHERE id::text <> data->>'resultado_id'")
    check(ok_id == "0", "id = data->>'resultado_id' en todas las filas")

    muestra = sorted(docs)
    lista = json.dumps(muestra)
    en_m = json.loads(mongo_eval(
        f"EJSON.stringify(db.resultados_unidad.find({{resultado_id: {{$in: {lista}}}}}, {{_id: 0}}).toArray(), {{relaxed: true}})"))
    ids_sql = ",".join(f"'{i}'" for i in muestra)
    en_p = json.loads(psql(f"SELECT json_agg(data) FROM resultados_unidad WHERE id IN ({ids_sql})"))
    por_id_m = {d["resultado_id"]: d for d in en_m}
    por_id_p = {d["resultado_id"]: d for d in en_p}
    iguales = sum(docs[i] == por_id_m.get(i) == por_id_p.get(i) for i in muestra)
    check(iguales == N_MUESTRA, f"muestra de {N_MUESTRA} documentos idéntica en NDJSON, MongoDB y PostgreSQL ({iguales}/{N_MUESTRA})")


def main():
    perfiles = sys.argv[1:] or ["A", "B", "C"]
    n, docs = validar_ndjson()
    for perfil in perfiles:
        validar_suite(perfil, n, docs)
        sh(str(ROOT / "scripts" / "suite.sh"), perfil, "stop")
    print(f"\nResultado: {'OK' if not errores else f'{len(errores)} fallas'}")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
