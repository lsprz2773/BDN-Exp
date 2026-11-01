#!/usr/bin/env python3
"""Verifica que Q1 y Q2 devuelven lo mismo en MongoDB y PostgreSQL (actividad F3.2).

- Q1: mismas claves (materia, criterio) y mismo count; sumas y promedios con
  tolerancia relativa de 1e-9 (Mongo suma en double, PostgreSQL en numeric).
- Q2: 1000 filas en cada variante y la misma lista ordenada de `final`
  (los ids empatados pueden salir en distinto orden).

Uso: python3 -I scripts/check_queries.py [perfil]      (por defecto A)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dbexec import VARIANTES, mongo_aggregate, pg_query, suite

errores = []


def check(cond, msg):
    print(("  OK  " if cond else "  FALLA ") + msg)
    if not cond:
        errores.append(msg)


def main():
    perfil = sys.argv[1] if len(sys.argv) > 1 else "A"
    suite(perfil, "up")

    print(f"== Q1 (perfil {perfil})")
    m = {(r["_id"]["materia"], r["_id"]["criterio"]): r for r in mongo_aggregate(perfil, "q1", {})}
    p = {(r["materia"], r["criterio"]): r for r in pg_query(perfil, "q1")}
    check(set(m) == set(p), f"mismos grupos: {len(m)} en Mongo, {len(p)} en PostgreSQL")
    comunes = set(m) & set(p)
    cnt_mal = sum(m[k]["count"] != p[k]["count"] for k in comunes)
    check(cnt_mal == 0, f"count idéntico en todos los grupos ({cnt_mal} distintos)")
    tol_mal = sum(
        not math.isclose(m[k][c], float(p[k][c]), rel_tol=1e-9)
        for k in comunes for c in ("total_aporte", "avg_aporte")
    )
    check(tol_mal == 0, f"sumas y promedios dentro de 1e-9 relativo ({tol_mal} fuera)")
    print(f"       filas totales agregadas: {sum(r['count'] for r in m.values())}")

    print(f"== Q2 (perfil {perfil})")
    resultados = {}
    for qid, (base, opciones) in VARIANTES["mongodb"].items():
        if base == "q2":
            resultados[qid] = [r["calificacion"]["final"] for r in mongo_aggregate(perfil, base, opciones)]
    for qid, (base, work_mem) in VARIANTES["postgresql"].items():
        if base == "q2":
            resultados[qid] = [float(r["final"]) for r in pg_query(perfil, base, work_mem)]
    for qid, finales in resultados.items():
        check(len(finales) == 1000, f"{qid}: {len(finales)} filas")
        check(finales == sorted(finales, reverse=True), f"{qid}: orden descendente por final")
    listas = {tuple(v) for v in resultados.values()}
    check(len(listas) == 1, "misma lista de valores final en las 4 variantes")
    ref = next(iter(resultados.values()))
    print(f"       final: máximo {ref[0]}, posición 1000 = {ref[-1]}")

    suite(perfil, "stop")
    print(f"\nResultado: {'OK' if not errores else f'{len(errores)} fallas'}")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
