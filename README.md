# MongoDB vs PostgreSQL JSONB bajo contención (cgroups v2)

Bases de Datos en la Nube · IT2iD · Universidad Politécnica de Chiapas · 2026

> Esqueleto: se completa en la fase F9 con los pasos de reproducción.

## Estructura
- `data/`: especificación del dataset ([ESQUEMA_DATASET.md](data/ESQUEMA_DATASET.md)) y generador
- `queries/`: esquemas físicos y consultas Q1/Q2 de MongoDB y PostgreSQL ([README](queries/README.md))
- `infra/`: docker-compose parametrizado, perfiles de recursos A/B/C y stack de monitoreo
- `scripts/`: control de suites, verificación de límites y automatización de la matriz
- `runner/`: benchmark runner
- `results/`: CSV de mediciones, planes de ejecución y evidencia de spill/OOM
- `report/`: reporte de métricas y figuras

## Requisitos
_Pendiente (F9): versiones de WSL2, Docker, imágenes y Python._

## Reproducción
_Pendiente (F9):_
1. Generar el dataset
2. Levantar los perfiles
3. Cargar los datos
4. Ejecutar `scripts/run_benchmarks.sh`
5. Consolidar los resultados
