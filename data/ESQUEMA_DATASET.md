# Esquema del dataset: `resultados_unidad`

> Basado en la colección `resultados_unidad` del proyecto *Sistema de Control Académico para Maestros* (`Proyecto-221026/Proyecto-Maestro/contexto/Diseno_BD_NoSQL_Control_Academico (1).xlsx`, hojas "Colecciones" e "Integridad"), adaptada a los requisitos de la práctica.
> Las desviaciones respecto al esquema de ejemplo del playbook se justifican en el reporte de métricas (sección 2).
> Este documento es la **especificación del generador** (`synthetic_data_generator.py`).

## 1. Requisitos de la práctica y cómo se cumplen

| Requisito | Cumplimiento |
|---|---|
| 500 000 registros | 500 000 documentos |
| JSON, mismo documento en ambos motores | NDJSON único que se carga en MongoDB y en PostgreSQL |
| 3 niveles de anidamiento | `contexto.materia.nombre`, `contexto.grupo.nombre`, `calificacion.desglose[].criterio` |
| ~3 ítems por registro | `calificacion.desglose`: 2, 3 o 4 elementos (25 % / 50 % / 25 %, promedio 3,0) |
| Id UUID | `resultado_id` (y columna `id` en PostgreSQL, con el mismo valor) |
| Fecha ISO-8601 | `cerrado_en`, formato fijo `YYYY-MM-DDTHH:MM:SSZ` (UTC) |

## 2. Documento de ejemplo

```json
{
  "resultado_id": "3f9c2b1e-8a4d-4c6f-9b2e-1d7a5e0c4f21",
  "cerrado_en": "2026-10-09T18:00:00Z",
  "vigente": true,
  "unidad":   { "numero": 1, "nombre": "Fundamentos", "estado": "cerrada" },
  "alumno":   { "id": "a1b2c3d4-...", "matricula": "2023170145",
                "nombre_completo": "Ana López Martínez", "estado": "activo" },
  "contexto": { "cuatrimestre": "2026-3",
                "materia": { "id": "m1...", "nombre": "Desarrollo Web Integral" },
                "grupo":   { "id": "g1...", "nombre": "5B" } },
  "calificacion": {
    "final": 9.27,
    "version_criterios": 3,
    "desglose": [
      { "criterio": "Examen",     "porcentaje": 40, "promedio": 9.1, "actividades_entregadas": 2, "actividades_totales": 2 },
      { "criterio": "Tareas",     "porcentaje": 30, "promedio": 9.5, "actividades_entregadas": 7, "actividades_totales": 8 },
      { "criterio": "Exposición", "porcentaje": 30, "promedio": 9.3, "actividades_entregadas": 1, "actividades_totales": 1 }
    ]
  },
  "asistencias": { "presente": 18, "ausente": 1, "justificado": 1 },
  "version": 1
}
```

## 3. Campos, tipos y distribución (36 valores por documento con 3 criterios)

| Campo | Nivel | Tipo | Origen en el Excel | Distribución para el generador |
|---|---|---|---|---|
| `resultado_id` | 1 | UUID v4 (texto) | `_id` | Único |
| `cerrado_en` | 1 | texto ISO-8601 UTC | `fecha_cierre` (pasa a tener hora) | Uniforme entre 2025-01-01 y 2026-12-31: **~50 % ≥ 2026-01-01** |
| `vigente` | 1 | bool | `vigente` | `true` si `unidad.estado = cerrada`; `false` si `reabierta` |
| `version` | 1 | int | `version` (convención de las demás colecciones) | 1–3 |
| `unidad.numero` | 2 | int | `unidad` | 1–4 |
| `unidad.nombre` | 2 | texto | `materias.unidades.nombre` | Catálogo de ~12 nombres |
| `unidad.estado` | 2 | texto | `materias.unidades.estado` / `reabierta` | **`cerrada` 85 %**, `reabierta` 15 % |
| `alumno.id` | 2 | UUID | `alumno_id` | ~120 000 alumnos distintos |
| `alumno.matricula` | 2 | texto (10 dígitos) | `alumnos.matricula` | Única por alumno |
| `alumno.nombre_completo` | 2 | texto | `alumnos.nombre_completo` | Combinaciones de nombres y apellidos |
| `alumno.estado` | 2 | texto | `alumnos.estado` | activo 90 %, baja 5 %, cambio_grupo 5 % |
| `contexto.cuatrimestre` | 2 | texto | `cuatrimestre` | `2025-1` … `2026-3`, coherente con `cerrado_en` |
| `contexto.materia.id` | 3 | UUID | `materia_id` | ~30 materias |
| `contexto.materia.nombre` | 3 | texto | `materias.nombre` | **~30 valores** (clave de agrupación de Q1) |
| `contexto.grupo.id` | 3 | UUID | `grupo_id` | 4 por materia y cuatrimestre (RN-01) |
| `contexto.grupo.nombre` | 3 | texto | `grupos.nombre` | `1A` … `9D` |
| `calificacion.final` | 2 | numérico (2 decimales) | `calificacion_final` | Σ(porcentaje × promedio)/100; rango 0–10 (RN-10) |
| `calificacion.version_criterios` | 2 | int | `version_criterios` | 1–5 |
| `calificacion.desglose[]` | 2 | arreglo | **nuevo** (congelado por RN-18) | 2–4 elementos, promedio 3 |
| `….criterio` | 3 | texto | `criterios_evaluacion.nombre` | Examen, Tareas, Exposición, Entregable, Proyecto, Participación; sin repetir dentro del documento |
| `….porcentaje` | 3 | int | `criterios_evaluacion.porcentaje` | **Suman 100** dentro del documento (RN-11) |
| `….promedio` | 3 | numérico (1 decimal) | calculado de `entregas` | Normal(7,2; 3,0) recortada a 0–10 (media real 6,93): **65,0 % > 6** (filtro de Q1) |
| `….actividades_entregadas` | 3 | int | conteo de `entregas` | 0 … `actividades_totales` |
| `….actividades_totales` | 3 | int | conteo de `actividades` | 1–10 (RN-22: máx. 40 por unidad) |
| `asistencias.presente` / `ausente` / `justificado` | 2 | int | `asistencias` | Suman 15–25 sesiones por unidad |

Semilla fija del generador: **42**.

## 4. Esquemas físicos

| | MongoDB | PostgreSQL |
|---|---|---|
| Contenedor | colección `resultados_unidad` (sin sharding, WiredTiger) | tabla `resultados_unidad (id UUID PRIMARY KEY, data JSONB NOT NULL)` |
| Índices | `_id`, `{cerrado_en: 1}`, `{resultado_id: 1}` | PK `id`, B-Tree `((data->>'cerrado_en'))` |
| **Sin índice** | `calificacion.final` y cualquier otro | `calificacion.final`, GIN y cualquier otro |
| Archivo | [queries/mongodb/schema.js](../queries/mongodb/schema.js) | [queries/postgresql/schema.sql](../queries/postgresql/schema.sql) |
