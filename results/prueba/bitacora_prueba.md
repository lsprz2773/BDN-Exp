# BITÁCORA DE LA SUITE DE PRUEBA

## Corridas

| Fecha/hora inicio | Fecha/hora fin | Ronda | Suite | Motor | Perfil | query_id | Conc. | Rep. | status | QPS | P99 (ms) | Throttled (s) | Max RSS (MB) | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-01 11:37:26 | 2026-11-01 11:38:07 | prueba | suite_a | mongodb | A | Q1 | 1 | 1 | ok | 0.6 | 1703.82 | 0.0 | 607.8 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 11:37:26 | 2026-11-01 11:38:07 | prueba | suite_c | mongodb | C | Q1 | 1 | 1 | ok | 0.5 | 2336.13 | 3.887 | 527.3 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 11:38:08 | 2026-11-01 11:38:41 | prueba | suite_a | mongodb | A | Q1 | 10 | 1 | ok | 0.5 | 19901.22 | 128.793 | 818.8 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 11:38:08 | 2026-11-01 11:38:41 | prueba | suite_c | mongodb | C | Q1 | 10 | 1 | error | 0.0 |  | 190.472 | 538.3 | warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:38:42 | 2026-11-01 11:39:16 | prueba | suite_a | mongodb | A | Q1 | 50 | 1 | error | 0.0 |  | 158.284 | 955.6 | warmup: {'corte': 50}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:38:42 | 2026-11-01 11:39:16 | prueba | suite_c | mongodb | C | Q1 | 50 | 1 | error | 0.0 |  | 220.055 | 576.6 | warmup: {'corte': 53}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:39:17 | 2026-11-01 11:39:50 | prueba | suite_a | mongodb | A | Q2_DISK0 | 1 | 1 | ok | 2.15 | 524.96 | 0.0 | 985.3 | warmup: {'corte': 1} |
| 2026-11-01 11:39:17 | 2026-11-01 11:39:50 | prueba | suite_c | mongodb | C | Q2_DISK0 | 1 | 1 | ok | 0.2 | 5174.06 | 6.586 | 651.1 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 11:39:51 | 2026-11-01 11:40:24 | prueba | suite_a | mongodb | A | Q2_DISK0 | 10 | 1 | ok | 4.15 | 3420.93 | 124.774 | 969.6 | warmup: {'corte': 10}; fallos en medición: {'corte': 8} |
| 2026-11-01 11:39:52 | 2026-11-01 11:40:25 | prueba | suite_c | mongodb | C | Q2_DISK0 | 10 | 1 | error | 0.0 |  | 128.332 | 635.9 | warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:40:26 | 2026-11-01 11:40:59 | prueba | suite_a | mongodb | A | Q2_DISK0 | 50 | 1 | ok | 0.3 | 19488.54 | 157.353 | 977.3 | warmup: {'corte': 73}; fallos en medición: {'corte': 136} |
| 2026-11-01 11:40:26 | 2026-11-01 11:40:59 | prueba | suite_c | mongodb | C | Q2_DISK0 | 50 | 1 | error | 0.0 |  | 198.261 | 665.3 | warmup: {'corte': 54}; fallos en medición: {'corte': 75}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:41:01 | 2026-11-01 11:41:33 | prueba | suite_a | mongodb | A | Q2_DISK1 | 1 | 1 | ok | 2.3 | 467.82 | 0.0 | 955.7 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 11:41:01 | 2026-11-01 11:41:34 | prueba | suite_c | mongodb | C | Q2_DISK1 | 1 | 1 | ok | 0.2 | 4631.51 | 5.316 | 654.6 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 11:41:34 | 2026-11-01 11:42:07 | prueba | suite_a | mongodb | A | Q2_DISK1 | 10 | 1 | ok | 3.0 | 4231.39 | 127.475 | 961.7 | warmup: {'corte': 10}; fallos en medición: {'corte': 11} |
| 2026-11-01 11:41:35 | 2026-11-01 11:42:08 | prueba | suite_c | mongodb | C | Q2_DISK1 | 10 | 1 | error | 0.0 |  | 150.133 | 645.9 | warmup: {'corte': 10}; fallos en medición: {'corte': 11}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:42:09 | 2026-11-01 11:42:42 | prueba | suite_a | mongodb | A | Q2_DISK1 | 50 | 1 | ok | 1.45 | 19672.79 | 157.459 | 958.1 | warmup: {'corte': 105}; fallos en medición: {'corte': 144} |
| 2026-11-01 11:42:09 | 2026-11-01 11:42:42 | prueba | suite_c | mongodb | C | Q2_DISK1 | 50 | 1 | error | 0.0 |  | 196.82 | 660.6 | warmup: {'corte': 68}; fallos en medición: {'corte': 68}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:42:44 | 2026-11-01 11:43:24 | prueba | suite_c | postgresql | C | Q1 | 1 | 1 | spill | 0.15 | 5861.38 | 8.314 | 99.8 | warmup: {'corte': 1}; spill: +3274506240 (temp_bytes); fallos en medición: {'corte': 1} |
| 2026-11-01 11:42:43 | 2026-11-01 11:43:24 | prueba | suite_a | postgresql | A | Q1 | 1 | 1 | spill | 0.35 | 3227.36 | 0.027 | 100.3 | warmup: {'corte': 1}; spill: +6521413632 (temp_bytes); fallos en medición: {'corte': 1} |
| 2026-11-01 11:43:25 | 2026-11-01 11:43:59 | prueba | suite_a | postgresql | A | Q1 | 10 | 1 | error | 0.0 |  | 32.498 | 519.5 | warmup: {'corte': 10}; spill: +6078898176 (temp_bytes); fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:43:25 | 2026-11-01 11:43:59 | prueba | suite_c | postgresql | C | Q1 | 10 | 1 | error | 0.0 |  | 54.142 | 520.7 | warmup: {'corte': 10}; spill: +766189568 (temp_bytes); fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:44:00 | 2026-11-01 11:44:38 | prueba | suite_a | postgresql | A | Q1 | 50 | 1 | error | 0.0 |  | 60.64 | 1782.6 | warmup: {'corte': 50}; spill: +9235939328 (temp_bytes); fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:44:01 | 2026-11-01 11:44:48 | prueba | suite_c | postgresql | C | Q1 | 50 | 1 | oom | 0.0 |  | 117.619 | 956.1 | warmup: {'error': 53}; oom_kill en el contenedor: 5; fallos en medición: {'error': 1262}; OperationalError: consuming input failed: server closed the connection unexpectedly 	This probably means the server terminated abnormally 	before or while processing the request.; ninguna consulta terminó dentro de la ventana |
| 2026-11-01 11:44:50 | 2026-11-01 11:45:22 | prueba | suite_c | postgresql | C | Q2_WM4 | 1 | 1 | ok | 1.45 | 787.79 | 67.189 | 13.1 | warmup: {'corte': 1} |
| 2026-11-01 11:44:49 | 2026-11-01 11:45:22 | prueba | suite_a | postgresql | A | Q2_WM4 | 1 | 1 | ok | 7.5 | 215.54 | 9.422 | 12.1 | fallos en medición: {'corte': 1} |
| 2026-11-01 11:45:23 | 2026-11-01 11:45:56 | prueba | suite_a | postgresql | A | Q2_WM4 | 10 | 1 | ok | 1.7 | 10042.24 | 122.116 | 40.4 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 11:45:23 | 2026-11-01 11:45:56 | prueba | suite_c | postgresql | C | Q2_WM4 | 10 | 1 | ok | 0.2 | 16293.53 | 172.579 | 40.7 | warmup: {'corte': 10}; fallos en medición: {'corte': 9} |
| 2026-11-01 11:45:58 | 2026-11-01 11:46:31 | prueba | suite_a | postgresql | A | Q2_WM4 | 50 | 1 | ok | 0.45 | 18839.87 | 135.311 | 121.0 | warmup: {'corte': 50}; fallos en medición: {'corte': 50} |
| 2026-11-01 11:45:58 | 2026-11-01 11:46:31 | prueba | suite_c | postgresql | C | Q2_WM4 | 50 | 1 | ok | 0.2 | 18803.13 | 153.268 | 121.7 | warmup: {'corte': 50}; fallos en medición: {'corte': 50} |
| 2026-11-01 11:46:33 | 2026-11-01 11:47:05 | prueba | suite_a | postgresql | A | Q2_WM64 | 1 | 1 | ok | 7.4 | 243.29 | 10.85 | 12.1 | fallos en medición: {'corte': 1} |
| 2026-11-01 11:46:33 | 2026-11-01 11:47:06 | prueba | suite_c | postgresql | C | Q2_WM64 | 1 | 1 | ok | 1.4 | 861.04 | 59.873 | 13.8 | warmup: {'corte': 1}; fallos en medición: {'corte': 1} |
| 2026-11-01 11:47:07 | 2026-11-01 11:47:40 | prueba | suite_a | postgresql | A | Q2_WM64 | 10 | 1 | ok | 1.7 | 10258.01 | 121.86 | 41.0 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 11:47:07 | 2026-11-01 11:47:41 | prueba | suite_c | postgresql | C | Q2_WM64 | 10 | 1 | ok | 0.2 | 15435.74 | 171.962 | 41.1 | warmup: {'corte': 10}; fallos en medición: {'corte': 10} |
| 2026-11-01 11:47:42 | 2026-11-01 11:48:15 | prueba | suite_a | postgresql | A | Q2_WM64 | 50 | 1 | ok | 0.4 | 19017.39 | 131.481 | 121.6 | warmup: {'corte': 50}; fallos en medición: {'corte': 50} |
| 2026-11-01 11:47:42 | 2026-11-01 11:48:16 | prueba | suite_c | postgresql | C | Q2_WM64 | 50 | 1 | ok | 0.05 | 19859.74 | 155.924 | 121.8 | warmup: {'corte': 50}; fallos en medición: {'corte': 49} |
