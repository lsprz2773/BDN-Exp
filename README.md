# MongoDB vs PostgreSQL JSONB bajo contención (cgroups v2)

Bases de Datos en la Nube · IT2iD · Universidad Politécnica de Chiapas · 2026

Medición de latencia (P50/P95/P99), throughput, throttling de CPU, RSS, spill a disco y OOM
al ejecutar agregaciones JSON anidadas con límites estrictos de CPU y memoria (Docker cgroups v2),
comparando MongoDB 9.0.4 con PostgreSQL 18.6 (JSONB).

El reporte de métricas está en [report/reporte.pdf](report/reporte.pdf) (fuente: [report/reporte.tex](report/reporte.tex)).

## Estructura
- `data/`: especificación del dataset ([ESQUEMA_DATASET.md](data/ESQUEMA_DATASET.md)) y generador
- `queries/`: esquemas físicos y consultas Q1/Q2 de MongoDB y PostgreSQL ([README](queries/README.md))
- `infra/`: docker-compose parametrizado, perfiles de recursos A/B/C y stack de monitoreo
- `scripts/`: preparación, control de suites, carga, validación, automatización de la matriz y análisis
- `runner/`: benchmark runner (Python, un proceso por suite y clientes en hilos)
- `results/`: CSV de mediciones por ronda, latencias crudas, series, planes de ejecución, entorno y evidencia de spill/OOM
- `report/`: reporte de métricas, tablas, figuras y consolidado

## Entregables

Correspondencia con lo que pide el playbook de la actividad (§8).

### Repositorio de código (§8.1)

| Entregable | Ubicación |
|---|---|
| `docker-compose.yml` con perfiles de recursos parametrizados | [infra/docker-compose.yml](infra/docker-compose.yml) y [infra/profiles/](infra/profiles/) (`profile_a.env`, `profile_b.env`, `profile_c.env`) |
| `synthetic_data_generator.py` (dataset de 500k) | [data/synthetic_data_generator.py](data/synthetic_data_generator.py), esquema en [data/ESQUEMA_DATASET.md](data/ESQUEMA_DATASET.md) |
| `benchmark_runner` (Python) | [runner/](runner/): `benchmark_runner.py`, `run_matrix.py`, `metrics.py` |
| `queries/` (agregaciones MongoDB y SQL PostgreSQL) | [queries/mongodb/](queries/mongodb/) (`q1.json`, `q2.json`, `schema.js`) y [queries/postgresql/](queries/postgresql/) (`q1.sql`, `q2.sql`, `schema.sql`) |
| `run_benchmarks.sh` (automatización de la matriz) | [scripts/run_benchmarks.sh](scripts/run_benchmarks.sh) |

### Evidencia

| Entregable | Ubicación |
|---|---|
| CSV de mediciones con el esquema fijo de 14 columnas (§8.2) | [results/csv/mediciones_ronda1.csv](results/csv/mediciones_ronda1.csv) (perfiles A y C, 108 filas) y [results/csv/mediciones_ronda2.csv](results/csv/mediciones_ronda2.csv) (perfil B, 54 filas); mismo encabezado, concatenables |
| Logs de spill/OOM | [results/evidencia_spill_oom/](results/evidencia_spill_oom/) (`ronda1/`, `ronda2/`) |
| Planes de ejecución (`explain("executionStats")` / `EXPLAIN (ANALYZE, BUFFERS)`) | [results/explain/](results/explain/) |
| Host, límites reales de la cgroup y versión de cada motor | [results/entorno/](results/entorno/) |
| Latencias crudas por corrida | [results/raw/](results/raw/) |
| Series de RSS y CPU por corrida (cada 1 s) | [results/series/](results/series/) |
| Logs de consola de cada ronda | [results/logs/](results/logs/) |

### Reporte de métricas (§8.3, 7 secciones)

| Entregable | Ubicación |
|---|---|
| Reporte (PDF) | [report/reporte.pdf](report/reporte.pdf) |
| Fuente LaTeX | [report/reporte.tex](report/reporte.tex) |
| Tablas consolidadas | [report/tablas/](report/tablas/) |
| Figuras: P99 vs concurrencia, throttling vs QPS, curva RSS | [report/figures/](report/figures/) |
| Consolidado por celda (mediana y rango de 3 repeticiones, M3) | [report/datos/consolidado.csv](report/datos/consolidado.csv) |

## Diseño experimental

| Perfil | CPUs | Memoria | Swap |
|---|---|---|---|
| A `PROFILE_A_BASELINE` | 4,0 | 4096 MB | 0 |
| B `PROFILE_B_MEDIUM` | 2,0 | 2048 MB | 0 |
| C `PROFILE_C_SEVERE` | 1,0 | 1024 MB | 0 |

- **Matriz:** 2 motores × 3 perfiles × (Q1 + 2 variantes de memoria de Q2) × concurrencias 1/10/50
  × 3 repeticiones = **162 corridas** (54 por perfil).
- **Ciclo por corrida:** flush de caché (`drop_caches`) → warmup 60 s → medición 300 s → cooldown 60 s
  (~7 min por corrida, ~6,5 h por perfil).
- **Variantes de Q2:** `Q2_DISK0`/`Q2_DISK1` (`allowDiskUse` false/true) en MongoDB y
  `Q2_WM4`/`Q2_WM64` (`work_mem` 4 MB/64 MB) en PostgreSQL, codificadas en `query_id`.
- **Distribución usada:** ronda 1 = perfiles A y C en paralelo en un equipo; ronda 2 = perfil B en
  un segundo equipo. El host de cada ronda queda en `results/entorno/ronda*/host.txt`.

## Requisitos
- Linux o Windows 11 con **WSL2** (Ubuntu) y **Docker** con cgroup v2. En Windows: Docker Desktop con
  *Settings → Resources → WSL integration → Ubuntu* activado.
- Python ≥ 3.10 con `venv` (Ubuntu: `sudo apt install python3-venv`), `curl` y `git`.
- RAM disponible para Docker: ~6 GB para A, ~4,5 GB para B, ~3,5 GB para C y ~7 GB para A + C en
  paralelo. En WSL2 el límite por defecto es el 50 % de la RAM del equipo; se ajusta en
  `%USERPROFILE%\.wslconfig`, por ejemplo:
  ```ini
  [wsl2]
  memory=5GB
  swap=2GB
  ```
  y después `wsl --shutdown` en PowerShell y reabrir Docker Desktop.
- Disco libre: ≥ 40 GB por suite. PostgreSQL vuelca a disco del orden de 1 GB por consulta Q1, y con
  50 clientes eso llega a decenas de GB temporales por corrida.
- Durante una ronda, el equipo conectado a la corriente, sin suspensión y sin actualizaciones
  automáticas pendientes.

## Ejecución

Todo se ejecuta **dentro de WSL/Linux**, desde la raíz del repositorio.

1. **Clonar**
   ```bash
   git clone https://github.com/lsprz2773/BDN-Exp.git
   cd BDN-Exp
   ```

2. **Preparar el entorno de un perfil.** Verifica requisitos, crea el entorno virtual
   (`~/.venvs/bdn`), genera el dataset con semilla 42 y comprueba su sha256, carga los datos en la
   suite, los valida y levanta el monitoreo (cAdvisor, Node Exporter y Prometheus). Tarda ~5–10 min
   y se puede repetir sin riesgo:
   ```bash
   scripts/setup_env.sh A
   ```
   Para preparar otra suite en el mismo equipo sin volver a cargar, se copian los volúmenes ya
   cargados:
   ```bash
   scripts/copy_volumes.sh A B C
   ```

3. **(Opcional) Prueba rápida** del flujo con ventanas cortas, ~4 min. Escribe solo en
   `results/prueba/`:
   ```bash
   scripts/run_benchmarks.sh --profile A --test --only mongodb:Q1
   ```

4. **Correr la matriz de un perfil** (~6,5 h). Cada perfil se corre con su número de ronda, que
   define los archivos de salida (`mediciones_ronda<N>.csv`, `raw/ronda<N>/`, …):
   ```bash
   scripts/run_benchmarks.sh --profile B --round 2 2>&1 | tee results/logs/ronda2_B.log
   ```
   Para correr dos perfiles en paralelo en el mismo equipo (como A y C en la ronda 1), se lanzan en
   dos terminales con la misma `--session`; una barrera sincroniza el flush de caché entre ambas:
   ```bash
   scripts/run_benchmarks.sh --profile A --round 1 --parties A,C --session r1 2>&1 | tee results/logs/ronda1_A.log
   ```
   ```bash
   scripts/run_benchmarks.sh --profile C --round 1 --parties A,C --session r1 2>&1 | tee results/logs/ronda1_C.log
   ```

5. **Reanudar** una ronda interrumpida: se vuelve a lanzar el mismo comando con `tee -a`. Las
   corridas ya terminadas se saltan. Si es una ronda en paralelo, se usa una `--session` nueva
   (por ejemplo `r1b`) en ambas terminales.

6. **Exportar las series** de RSS y CPU por corrida, con el monitoreo todavía arriba:
   ```bash
   ~/.venvs/bdn/bin/python -I scripts/export_series.py 2
   ```
   Escribe en `results/series/ronda<N>/`. Si cAdvisor no publica la cgroup de los contenedores
   (ocurre con algunas versiones de Docker Desktop), usa la serie que el runner lee directamente
   de la cgroup.

7. **Regenerar tablas, figuras y consolidado** a partir de todos los resultados en `results/`:
   ```bash
   ~/.venvs/bdn/bin/python -I scripts/analyze_results.py
   ```

8. **Compilar el reporte** desde `report/` (dos pasadas, por las referencias):
   ```bash
   cd report && pdflatex reporte.tex && pdflatex reporte.tex
   ```
   También se puede compilar en Overleaf subiendo `reporte.tex`, `tablas/` y `figures/`.

### Juntar resultados de varios equipos

Cada ronda escribe en rutas propias (`*ronda<N>*`), así que los resultados de equipos distintos se
juntan con git sin conflictos: en cada equipo, después del paso 6,
```bash
git add results/
git commit -m "data(results): ronda 2, perfil B"
git pull --rebase --autostash
git push
```

## Otras herramientas
- `scripts/suite.sh <A|B|C> <up|stop|down|ps|logs> [mongodb|postgres]`: control manual de una suite
- `scripts/check_env.sh`: límites reales de los contenedores en ejecución
- `scripts/validate_data.py`: conteos, índices y muestra idéntica entre motores y el NDJSON
- `scripts/check_queries.py [perfil]`: equivalencia de resultados de Q1/Q2 entre motores
- `scripts/capture_explain.py [perfiles]`: planes de ejecución en `results/explain/`
