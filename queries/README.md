# Queries de la práctica (esquema `resultados_unidad`)

Adaptación de Q1 y Q2 del playbook (§5) al esquema de [data/ESQUEMA_DATASET.md](../data/ESQUEMA_DATASET.md). Conservan la misma estructura y carga que las originales.

| Archivo | Query | Equivale en el playbook a |
|---|---|---|
| `mongodb/q1.json`, `postgresql/q1.sql` | **Q1 Unwind, Filter & Grouping** (saturación de CPU): desanida `calificacion.desglose`, filtra `promedio > 6` y agrupa suma, promedio y conteo de `porcentaje × promedio` por materia y criterio | `$unwind items` → `price > 50` → `qty × price` por país y categoría |
| `mongodb/q2.json`, `postgresql/q2.sql` | **Q2 Massive Sort & Top-K** (estrés de buffer): resultados con unidad `cerrada` desde 2026-01-01, ordenados desc. por `calificacion.final`, Top-1000, **sin índice** en el total | `payment.status = completed` → sort por `payment.final_total` → Top-1000 |
| `mongodb/schema.js`, `postgresql/schema.sql` | Colección/tabla e índices | §2 Motores objetivo |

## Variantes de Q2 (las aplica el runner, no el texto de la query)

| `query_id` | Motor | Cómo se aplica |
|---|---|---|
| `Q2_DISK0` | MongoDB | `aggregate(pipeline, { allowDiskUse: false })` |
| `Q2_DISK1` | MongoDB | `aggregate(pipeline, { allowDiskUse: true })` |
| `Q2_WM4` | PostgreSQL | `SET work_mem = '4MB';` en la sesión antes de la query |
| `Q2_WM64` | PostgreSQL | `SET work_mem = '64MB';` en la sesión antes de la query |

## Notas

- **Comparación de fechas como texto (D-15):** `cerrado_en` se guarda con formato fijo UTC (`YYYY-MM-DDTHH:MM:SSZ`), así que el orden de texto coincide con el cronológico. PostgreSQL compara `data->>'cerrado_en'` como texto, en lugar de castear a `timestamptz` como el playbook, para que pueda usar el índice B-Tree de expresión. MongoDB también compara como string, igual que en el playbook.
- **Empates en Q2 (D-16):** `calificacion.final` tiene 2 decimales, así que el Top-1000 tiene empates. La equivalencia entre motores se valida comparando la **lista ordenada de valores `final`**, no los ids.
