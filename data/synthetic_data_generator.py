#!/usr/bin/env python3
"""Generador del dataset `resultados_unidad` (ver data/ESQUEMA_DATASET.md).

Escribe un NDJSON (un documento JSON por línea) que se carga igual en MongoDB
y en PostgreSQL. Es determinista: misma semilla, mismo archivo.

Uso:
    python3 data/synthetic_data_generator.py [--n 500000] [--seed 42]
                                             [--out data/generated/resultados_unidad.ndjson]
Al terminar imprime en stderr un resumen de las distribuciones generadas.
"""
import argparse
import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

MATERIAS = [
    "Algoritmos", "Estructuras de Datos", "Programación Orientada a Objetos",
    "Bases de Datos", "Bases de Datos en la Nube", "Sistemas Operativos",
    "Redes de Computadoras", "Ingeniería de Software", "Desarrollo Web Integral",
    "Desarrollo Móvil", "Cálculo Diferencial", "Cálculo Integral",
    "Álgebra Lineal", "Matemáticas Discretas", "Probabilidad y Estadística",
    "Arquitectura de Computadoras", "Seguridad Informática", "Inteligencia Artificial",
    "Minería de Datos", "Computación en la Nube", "Administración de Proyectos",
    "Interacción Humano-Computadora", "Física", "Inglés Técnico",
    "Ética Profesional", "Innovación Digital", "Internet de las Cosas",
    "Graficación", "Compiladores", "Calidad de Software",
]
UNIDADES = [
    "Fundamentos", "Conceptos básicos", "Modelado", "Diseño", "Implementación",
    "Pruebas", "Optimización", "Integración", "Aplicaciones", "Proyecto integrador",
    "Casos de estudio", "Temas avanzados",
]
CRITERIOS = ["Examen", "Tareas", "Exposición", "Entregable", "Proyecto", "Participación"]
NOMBRES = [
    "Ana", "Luis", "María", "José", "Fernanda", "Carlos", "Daniela", "Jorge", "Valeria",
    "Miguel", "Sofía", "Diego", "Camila", "Andrés", "Paola", "Ricardo", "Mariana", "Javier",
    "Alejandra", "Fernando", "Gabriela", "Eduardo", "Lucía", "Roberto", "Karla", "Héctor",
    "Ximena", "Iván", "Renata", "Óscar",
]
APELLIDOS = [
    "López", "Martínez", "García", "Hernández", "Pérez", "González", "Rodríguez", "Sánchez",
    "Ramírez", "Cruz", "Gómez", "Morales", "Vázquez", "Jiménez", "Reyes", "Díaz", "Torres",
    "Gutiérrez", "Ruiz", "Mendoza", "Aguilar", "Ortiz", "Castillo", "Moreno", "Chávez",
    "Velázquez", "Domínguez", "Ramos", "Herrera", "Medina",
]
LETRAS_GRUPO = "ABCD"           # 4 grupos por materia y cuatrimestre (RN-01)
N_ALUMNOS = 120_000
FECHA_INI = datetime(2025, 1, 1, tzinfo=timezone.utc)
FECHA_FIN = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


def new_uuid(rng):
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def cuatrimestre(fecha):
    # Ene–Abr = 1, May–Ago = 2, Sep–Dic = 3
    return f"{fecha.year}-{(fecha.month - 1) // 4 + 1}"


def porcentajes(rng, k):
    # k porcentajes múltiplos de 5, cada uno >= 5, que suman 100 (RN-11)
    cortes = sorted(rng.sample(range(5, 100, 5), k - 1))
    puntos = [0] + cortes + [100]
    return [puntos[i + 1] - puntos[i] for i in range(k)]


def promedio_criterio(rng):
    # Normal(7.2, 3.0) recortada a [0, 10]: ~65 % > 6 (selectividad del filtro de Q1)
    return round(min(10.0, max(0.0, rng.gauss(7.2, 3.0))), 1)


def build_catalogos(rng):
    materias = [
        {"id": new_uuid(rng), "nombre": nombre, "nivel": i % 9 + 1}
        for i, nombre in enumerate(MATERIAS)
    ]
    alumnos = []
    for i in range(N_ALUMNOS):
        anio = rng.choice((2021, 2022, 2023, 2024, 2025))
        alumnos.append({
            "id": new_uuid(rng),
            "matricula": f"{anio}{i:06d}",
            "nombre_completo": f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}",
            "estado": rng.choices(("activo", "baja", "cambio_grupo"), (90, 5, 5))[0],
        })
    return materias, alumnos


def build_doc(rng, materias, alumnos, grupos):
    segundos = int((FECHA_FIN - FECHA_INI).total_seconds())
    cerrado = FECHA_INI + timedelta(seconds=rng.randrange(segundos + 1))
    cuatri = cuatrimestre(cerrado)
    materia = rng.choice(materias)
    letra = rng.choice(LETRAS_GRUPO)
    clave_grupo = (materia["id"], cuatri, letra)
    if clave_grupo not in grupos:
        grupos[clave_grupo] = new_uuid(rng)
    estado_unidad = rng.choices(("cerrada", "reabierta"), (85, 15))[0]

    k = rng.choices((2, 3, 4), (25, 50, 25))[0]
    desglose = []
    for criterio, pct in zip(rng.sample(CRITERIOS, k), porcentajes(rng, k)):
        prom = promedio_criterio(rng)
        totales = rng.randint(1, 10)
        entregadas = min(totales, max(0, round(totales * (prom / 10 + rng.uniform(-0.15, 0.15)))))
        desglose.append({
            "criterio": criterio,
            "porcentaje": pct,
            "promedio": prom,
            "actividades_entregadas": entregadas,
            "actividades_totales": totales,
        })
    final = round(sum(d["porcentaje"] * d["promedio"] for d in desglose) / 100, 2)

    sesiones = rng.randint(15, 25)
    ausente = rng.randint(0, sesiones // 5)
    justificado = rng.randint(1, 3) if rng.random() < 0.3 else 0

    return {
        "resultado_id": new_uuid(rng),
        "cerrado_en": cerrado.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vigente": estado_unidad == "cerrada",
        "unidad": {
            "numero": rng.randint(1, 4),
            "nombre": rng.choice(UNIDADES),
            "estado": estado_unidad,
        },
        "alumno": rng.choice(alumnos),
        "contexto": {
            "cuatrimestre": cuatri,
            "materia": {"id": materia["id"], "nombre": materia["nombre"]},
            "grupo": {"id": grupos[clave_grupo], "nombre": f"{materia['nivel']}{letra}"},
        },
        "calificacion": {
            "final": final,
            "version_criterios": rng.randint(1, 5),
            "desglose": desglose,
        },
        "asistencias": {
            "presente": sesiones - ausente - justificado,
            "ausente": ausente,
            "justificado": justificado,
        },
        "version": rng.randint(1, 3),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=500_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/generated/resultados_unidad.ndjson")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    materias, alumnos = build_catalogos(rng)
    grupos = {}

    stats = {"k": {2: 0, 3: 0, 4: 0}, "items": 0, "prom_gt6": 0, "prom_sum": 0.0,
             "desde_2026": 0, "cerrada": 0, "q2": 0, "alumnos": set()}
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        for _ in range(args.n):
            doc = build_doc(rng, materias, alumnos, grupos)
            f.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")

            desglose = doc["calificacion"]["desglose"]
            stats["k"][len(desglose)] += 1
            stats["items"] += len(desglose)
            stats["prom_gt6"] += sum(d["promedio"] > 6 for d in desglose)
            stats["prom_sum"] += sum(d["promedio"] for d in desglose)
            nuevo = doc["cerrado_en"] >= "2026-01-01T00:00:00Z"
            cerrada = doc["unidad"]["estado"] == "cerrada"
            stats["desde_2026"] += nuevo
            stats["cerrada"] += cerrada
            stats["q2"] += nuevo and cerrada
            stats["alumnos"].add(doc["alumno"]["id"])

    n, items = args.n, stats["items"]
    print(f"documentos: {n} -> {args.out}", file=sys.stderr)
    print(f"desglose 2/3/4: {stats['k'][2]}/{stats['k'][3]}/{stats['k'][4]}"
          f" (promedio {items / n:.3f} ítems)", file=sys.stderr)
    print(f"promedio > 6 (filtro Q1): {stats['prom_gt6'] / items:.1%};"
          f" media de promedio: {stats['prom_sum'] / items:.2f}", file=sys.stderr)
    print(f"cerrado_en >= 2026: {stats['desde_2026'] / n:.1%}; cerrada: {stats['cerrada'] / n:.1%};"
          f" pasan el filtro de Q2: {stats['q2']} ({stats['q2'] / n:.1%})", file=sys.stderr)
    print(f"alumnos distintos: {len(stats['alumnos'])}; grupos: {len(grupos)}", file=sys.stderr)


if __name__ == "__main__":
    main()
