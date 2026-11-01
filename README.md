# MongoDB vs PostgreSQL JSONB bajo contención (cgroups v2)

Bases de Datos en la Nube · IT2iD · Universidad Politécnica de Chiapas · 2026

Medición de latencia (P50/P95/P99), throughput, throttling de CPU, RSS, spill a disco y OOM
al ejecutar agregaciones JSON anidadas con límites estrictos de CPU y memoria (Docker cgroups v2).

## Estructura
- `data/`: especificación del dataset ([ESQUEMA_DATASET.md](data/ESQUEMA_DATASET.md)) y generador
- `queries/`: esquemas físicos y consultas Q1/Q2 de MongoDB y PostgreSQL ([README](queries/README.md))
- `infra/`: docker-compose parametrizado, perfiles de recursos A/B/C y stack de monitoreo
- `scripts/`: preparación, control de suites, carga, validación y automatización de la matriz
- `runner/`: benchmark runner (Python, un proceso por suite y clientes en hilos)
- `results/`: CSV de mediciones por ronda, latencias crudas, planes de ejecución, entorno de cada ronda y evidencia de spill/OOM
- `report/`: reporte de métricas y figuras

## Perfiles y rondas

| Perfil | CPUs | Memoria | Ronda | Equipo |
|---|---|---|---|---|
| A (baseline) | 4,0 | 4096 MB | 1 (en paralelo con C) | PC principal |
| B (media) | 2,0 | 2048 MB | 2 | Segunda PC |
| C (severa) | 1,0 | 1024 MB | 1 (en paralelo con A) | PC principal |

Las dos rondas corren al mismo tiempo en equipos distintos. Cada perfil corre 54 corridas:
2 motores × (Q1 + 2 variantes de Q2) × concurrencias 1/10/50 × 3 repeticiones, cada una con warmup de
60 s, medición de 300 s y cooldown de 60 s (~6,5 h por perfil).

## Requisitos
- Linux o Windows 11 con **WSL2** (Ubuntu) y **Docker** con cgroup v2. En Windows: Docker Desktop con
  *Settings → Resources → WSL integration → Ubuntu* activado y las actualizaciones automáticas desactivadas.
- Python ≥ 3.10 con `venv` (Ubuntu: `sudo apt install python3-venv`), `curl` y `git`.
- RAM disponible para Docker/WSL: ~4,5 GB para B sola; ~7 GB para A + C en paralelo.
  En WSL2 el límite por defecto es el 50 % de la RAM del equipo (se cambia en `%USERPROFILE%\.wslconfig`).
- Disco libre: ≥ 40 GB por suite. PostgreSQL vuelca a disco hasta ~650 MB por consulta Q1, y con
  50 clientes eso puede llegar a decenas de GB temporales.

## Correr la suite B en la segunda PC

Todo se ejecuta **dentro de WSL/Linux**, desde la raíz del repositorio.

0. **Solo en equipos con 8 GB de RAM** (por ejemplo, la Dell Vostro 3400): WSL2 recibe por defecto la
   mitad de la RAM (~3,8 GB), que no alcanza para el perfil B con el monitoreo. Antes de empezar, en
   Windows crear `%USERPROFILE%\.wslconfig` con:
   ```ini
   [wsl2]
   memory=5GB
   swap=2GB
   ```
   Después, en PowerShell ejecutar `wsl --shutdown`, reabrir Docker Desktop y comprobar dentro de WSL con
   `free -h` que aparecen ~4,8 GB. Durante la ronda, **cerrar el navegador y las demás aplicaciones**
   y dejar el equipo conectado y sin suspensión.

1. Clonar:
   ```bash
   git clone https://github.com/lsprz2773/BDN-Exp.git
   cd BDN-Exp
   ```
2. Preparar la PC. Verifica requisitos, crea el entorno virtual (`~/.venvs/bdn`), genera el dataset
   y comprueba su sha256, carga los datos en la suite B, los valida y levanta el monitoreo (~5–10 min):
   ```bash
   scripts/setup_env.sh B
   ```
3. (Opcional, ~4 min) Prueba rápida del flujo con ventanas cortas; escribe solo en `results/prueba/`:
   ```bash
   scripts/run_benchmarks.sh --profile B --test --only mongodb:Q1
   ```
4. Correr la ronda (~6,5 h):
   ```bash
   scripts/run_benchmarks.sh --profile B --round 2 2>&1 | tee results/logs/ronda2_B.log
   ```
   Si se interrumpe, se vuelve a lanzar el mismo comando y continúa donde se quedó.
5. Al terminar, entregar los resultados (ver la sección siguiente).

### Al terminar: sincronizar los resultados

Primero, **en la misma PC y con el monitoreo todavía arriba**, exportar de Prometheus las series
por corrida (RSS y CPU usada cada 1 s, y los CPU-s de cada ventana para M3):
```bash
~/.venvs/bdn/bin/python -I scripts/export_series.py 2
```
Escribe en `results/series/ronda2/`. Las corridas sin serie en Prometheus quedan en
`resumen.csv` con las columnas vacías.

Cada ronda escribe en rutas propias (`*ronda2*`), así que los resultados de las dos PCs se juntan
**con git y sin conflictos**:

```bash
git add results/
git commit -m "data(results): ronda 2, perfil B"
git pull --rebase
git push
```

Además hay que **enviar aparte** la carpeta `seguimiento/`, que no se versiona: comprimirla y mandarla.
Contiene la bitácora con el detalle de cada corrida, los errores y el control de la matriz.

| Qué | Ruta | Cómo llega |
|---|---|---|
| Mediciones (54 filas) | `results/csv/mediciones_ronda2.csv` | git |
| Latencias crudas (54 archivos) | `results/raw/ronda2/` | git |
| Host, límites reales y versión del motor | `results/entorno/ronda2/` | git |
| Evidencia de spill/OOM | `results/evidencia_spill_oom/ronda2/` | git |
| Log de consola de la ronda | `results/logs/ronda2_B.log` | git |
| Series de RSS y CPU por corrida | `results/series/ronda2/` | git |
| Bitácora, errores y control de la matriz | `seguimiento/BITACORA_EJECUCION.md`, `seguimiento/ESTATUS_ERRORES.md`, `seguimiento/CONTROL_MATRIZ.md` | **enviar aparte** (zip) |

Si en esa PC no hay acceso para hacer `git push`, se envían en un zip la carpeta `results/` completa
y la carpeta `seguimiento/`.

Para comprobar que la ronda terminó completa antes de entregar:
```bash
echo "filas: $(($(wc -l < results/csv/mediciones_ronda2.csv) - 1)) de 54"
grep -E "^\| B \|" seguimiento/CONTROL_MATRIZ.md
```
La fila del perfil B del control debe quedar sin corridas pendientes (☐ = 0).

> **Comparabilidad:** B se mide en un equipo distinto al de A y C. `results/entorno/ronda*/host.txt`
> registra la CPU, la RAM y Docker de cada equipo para documentarlo en la sección 1 del reporte.

## Correr la ronda 1 (A + C en paralelo, PC principal)

Preparar con `scripts/setup_env.sh A` y copiar los datos a C con `scripts/copy_volumes.sh A C`.
Después, en dos terminales y con la misma `--session`:
```bash
scripts/run_benchmarks.sh --profile A --round 1 --parties A,C --session r1 2>&1 | tee results/logs/ronda1_A.log
```
```bash
scripts/run_benchmarks.sh --profile C --round 1 --parties A,C --session r1 2>&1 | tee results/logs/ronda1_C.log
```
Para reanudar una ronda interrumpida se usa una sesión nueva (por ejemplo `r1b`).
Al terminar, exportar las series con `~/.venvs/bdn/bin/python -I scripts/export_series.py 1`.

## Otras herramientas
- `scripts/suite.sh <A|B|C> <up|stop|down|ps|logs> [mongodb|postgres]`: control manual de una suite
- `scripts/check_env.sh`: límites reales de los contenedores en ejecución
- `scripts/check_queries.py [perfil]`: equivalencia de resultados de Q1/Q2 entre motores
- `scripts/capture_explain.py [perfiles]`: planes de ejecución en `results/explain/`
