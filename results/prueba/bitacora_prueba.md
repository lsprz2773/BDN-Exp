# BITÁCORA DE LA SUITE DE PRUEBA

## Corridas

| Fecha/hora inicio | Fecha/hora fin | Ronda | Suite | Motor | Perfil | query_id | Conc. | Rep. | status | QPS | P99 (ms) | Throttled (s) | Max RSS (MB) | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-01 10:37:27 | 2026-11-01 10:38:13 | prueba | suite_c | mongodb | C | Q1 | 1 | 1 | ok | 0.5 | 2360.24 | 7.689 | 531.8 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:37:27 | 2026-11-01 10:38:13 | prueba | suite_b | mongodb | B | Q1 | 1 | 1 | ok | 0.6 | 1728.34 | 0.444 | 721.3 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:38:14 | 2026-11-01 10:38:50 | prueba | suite_b | mongodb | B | Q1 | 10 | 1 | error | 0.0 |  | 193.301 | 739.9 | warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:38:14 | 2026-11-01 10:38:50 | prueba | suite_c | mongodb | C | Q1 | 10 | 1 | error | 0.0 |  | 215.618 | 467.2 | warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:38:51 | 2026-11-01 10:39:25 | prueba | suite_b | mongodb | B | Q1 | 50 | 1 | error | 0.0 |  | 189.747 | 806.8 | warmup: {'corte': 51}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:38:51 | 2026-11-01 10:39:28 | prueba | suite_c | mongodb | C | Q1 | 50 | 1 | error | 0.0 |  | 208.445 | 579.5 | warmup: {'corte': 50}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:39:28 | 2026-11-01 10:40:01 | prueba | suite_b | mongodb | B | Q2_DISK0 | 1 | 1 | ok | 0.75 | 1652.31 | 0.505 | 697.9 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:39:29 | 2026-11-01 10:40:01 | prueba | suite_c | mongodb | C | Q2_DISK0 | 1 | 1 | ok | 0.2 | 4708.53 | 8.72 | 585.3 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:40:07 | 2026-11-01 10:40:40 | prueba | suite_b | mongodb | B | Q2_DISK0 | 10 | 1 | ok | 0.5 | 16897.09 | 148.63 | 856.2 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 10:40:07 | 2026-11-01 10:40:40 | prueba | suite_c | mongodb | C | Q2_DISK0 | 10 | 1 | error | 0.0 |  | 136.476 | 589.8 | warmup: {'corte': 11}; fallos en medición: {'corte': 11}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:40:41 | 2026-11-01 10:41:15 | prueba | suite_b | mongodb | B | Q2_DISK0 | 50 | 1 | error | 0.0 |  | 174.953 | 865.3 | warmup: {'corte': 58}; fallos en medición: {'corte': 58}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:40:41 | 2026-11-01 10:41:15 | prueba | suite_c | mongodb | C | Q2_DISK0 | 50 | 1 | error | 0.0 |  | 167.807 | 624.6 | warmup: {'corte': 57}; fallos en medición: {'corte': 56}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:41:16 | 2026-11-01 10:41:49 | prueba | suite_b | mongodb | B | Q2_DISK1 | 1 | 1 | ok | 0.6 | 3939.78 | 0.347 | 733.6 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:41:16 | 2026-11-01 10:41:49 | prueba | suite_c | mongodb | C | Q2_DISK1 | 1 | 1 | ok | 0.15 | 7422.23 | 4.573 | 491.5 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:41:50 | 2026-11-01 10:42:23 | prueba | suite_b | mongodb | B | Q2_DISK1 | 10 | 1 | ok | 0.5 | 18873.04 | 148.027 | 873.7 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 10:41:50 | 2026-11-01 10:42:23 | prueba | suite_c | mongodb | C | Q2_DISK1 | 10 | 1 | error | 0.0 |  | 154.121 | 616.7 | warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:42:24 | 2026-11-01 10:43:01 | prueba | suite_b | mongodb | B | Q2_DISK1 | 50 | 1 | error | 0.0 |  | 190.383 | 870.0 | warmup: {'corte': 63}; fallos en medición: {'corte': 65}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:42:24 | 2026-11-01 10:43:01 | prueba | suite_c | mongodb | C | Q2_DISK1 | 50 | 1 | error | 0.0 |  | 188.114 | 639.0 | warmup: {'corte': 53}; fallos en medición: {'corte': 80}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:43:03 | 2026-11-01 10:43:46 | prueba | suite_c | postgresql | C | Q1 | 1 | 1 | error | 0.0 |  | 1.386 | 94.6 | warmup: {'corte': 1}; fallos en medición: {'corte': 1}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:43:02 | 2026-11-01 10:43:50 | prueba | suite_b | postgresql | B | Q1 | 1 | 1 | spill | 0.05 | 14366.22 | 1.819 | 99.2 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:43:51 | 2026-11-01 10:44:34 | prueba | suite_b | postgresql | B | Q1 | 10 | 1 | error | 0.0 |  | 25.426 | 519.7 | warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:43:51 | 2026-11-01 10:44:35 | prueba | suite_c | postgresql | C | Q1 | 10 | 1 | error | 0.0 |  | 77.966 | 517.6 | warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:44:36 | 2026-11-01 10:45:28 | prueba | suite_b | postgresql | B | Q1 | 50 | 1 | error | 0.0 |  | 158.054 | 1757.3 | warmup: {'corte': 50}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:44:37 | 2026-11-01 10:45:28 | prueba | suite_c | postgresql | C | Q1 | 50 | 1 | oom | 0.0 |  | 176.683 | 961.2 | warmup: {'corte': 7, 'error': 43}; oom_kill en el contenedor: 9; fallos en medición: {'error': 201}; OperationalError: consuming input failed: server closed the connection unexpectedly 	This probably means the server terminated abnormally 	before or while processing the request.; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:45:29 | 2026-11-01 10:46:02 | prueba | suite_c | postgresql | C | Q2_WM4 | 1 | 1 | ok | 0.7 | 4039.85 | 67.641 | 14.4 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:45:29 | 2026-11-01 10:46:02 | prueba | suite_b | postgresql | B | Q2_WM4 | 1 | 1 | ok | 1.35 | 2775.78 | 44.938 | 12.1 | - |
| 2026-11-01 10:46:03 | 2026-11-01 10:46:40 | prueba | suite_c | postgresql | C | Q2_WM4 | 10 | 1 | error | 0.0 |  | 169.103 | 40.8 | warmup: {'corte': 10}; fallos en medición: {'corte': 9}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:46:03 | 2026-11-01 10:46:40 | prueba | suite_b | postgresql | B | Q2_WM4 | 10 | 1 | ok | 0.2 | 15990.37 | 179.664 | 41.6 | warmup: {'corte': 10}; fallos en medición: {'corte': 8} |
| 2026-11-01 10:46:41 | 2026-11-01 10:47:17 | prueba | suite_b | postgresql | B | Q2_WM4 | 50 | 1 | ok | 0.2 | 18454.54 | 186.106 | 121.2 | warmup: {'corte': 50}; fallos en medición: {'corte': 50} |
| 2026-11-01 10:46:41 | 2026-11-01 10:47:17 | prueba | suite_c | postgresql | C | Q2_WM4 | 50 | 1 | error | 0.0 |  | 153.214 | 119.0 | warmup: {'corte': 50}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 10:47:19 | 2026-11-01 10:47:52 | prueba | suite_b | postgresql | B | Q2_WM64 | 1 | 1 | ok | 1.9 | 2351.37 | 45.425 | 12.4 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:47:19 | 2026-11-01 10:47:52 | prueba | suite_c | postgresql | C | Q2_WM64 | 1 | 1 | ok | 1.0 | 2895.53 | 62.574 | 12.3 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 10:47:53 | 2026-11-01 10:48:28 | prueba | suite_c | postgresql | C | Q2_WM64 | 10 | 1 | ok | 0.15 | 17999.81 | 145.975 | 41.2 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 10:47:53 | 2026-11-01 10:48:28 | prueba | suite_b | postgresql | B | Q2_WM64 | 10 | 1 | ok | 0.35 | 11406.23 | 159.526 | 40.7 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 10:48:29 | 2026-11-01 10:49:03 | prueba | suite_b | postgresql | B | Q2_WM64 | 50 | 1 | ok | 0.2 | 13618.4 | 173.29 | 121.6 | warmup: {'corte': 50}; fallos en medición: {'corte': 49} |
| 2026-11-01 10:48:29 | 2026-11-01 10:49:03 | prueba | suite_c | postgresql | C | Q2_WM64 | 50 | 1 | ok | 0.15 | 14122.86 | 158.364 | 120.5 | warmup: {'corte': 50}; fallos en medición: {'corte': 50} |
