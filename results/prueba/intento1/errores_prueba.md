# ERRORES DE LA SUITE DE PRUEBA

## Errores abiertos o en corrección

| ID | Fecha/hora | Origen | Descripción | Causa | Corrección aplicada | ESTATUS |
|---|---|---|---|---|---|---|
| E-001 | 2026-11-01 10:07:20 | B:MONGO:Q1:c10:r1 | Corrida terminó en `error`: warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-002 | 2026-11-01 10:07:21 | C:MONGO:Q1:c10:r1 | Corrida terminó en `error`: warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-003 | 2026-11-01 10:08:02 | B:MONGO:Q1:c50:r1 | Corrida terminó en `error`: warmup: {'corte': 60}; fallos en medición: {'corte': 64}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-004 | 2026-11-01 10:08:03 | C:MONGO:Q1:c50:r1 | Corrida terminó en `error`: warmup: {'corte': 55}; fallos en medición: {'corte': 52}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-005 | 2026-11-01 10:09:11 | C:MONGO:Q2_DISK0:c10:r1 | Corrida terminó en `error`: warmup: {'corte': 12}; fallos en medición: {'corte': 11}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-006 | 2026-11-01 10:09:45 | B:MONGO:Q2_DISK0:c50:r1 | Corrida terminó en `error`: warmup: {'corte': 59}; fallos en medición: {'corte': 68}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-007 | 2026-11-01 10:09:46 | C:MONGO:Q2_DISK0:c50:r1 | Corrida terminó en `error`: warmup: {'corte': 62}; fallos en medición: {'corte': 54}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-008 | 2026-11-01 10:10:53 | C:MONGO:Q2_DISK1:c10:r1 | Corrida terminó en `error`: warmup: {'corte': 14}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-009 | 2026-11-01 10:11:28 | C:MONGO:Q2_DISK1:c50:r1 | Corrida terminó en `error`: warmup: {'corte': 50}; fallos en medición: {'corte': 55}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-010 | 2026-11-01 10:11:28 | B:MONGO:Q2_DISK1:c50:r1 | Corrida terminó en `error`: warmup: {'corte': 61}; fallos en medición: {'corte': 66}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-011 | 2026-11-01 10:11:37 | B:PG:Q1:c1:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-012 | 2026-11-01 10:12:17 | B:PG:Q1:c10:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-013 | 2026-11-01 10:12:55 | C:PG:Q1:c10:r1 | Corrida terminó en `error`: warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-014 | 2026-11-01 10:12:58 | B:PG:Q1:c50:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-015 | 2026-11-01 10:13:19 | C:PG:Q1:c50:r1 | Corrida terminó en `error`: OperationalError: the connection is closed | Por analizar | - | 🔴 Abierto |
| E-016 | 2026-11-01 10:13:22 | B:PG:Q2_WM4:c1:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-017 | 2026-11-01 10:13:55 | C:PG:Q2_WM4:c1:r1 | Corrida terminó en `oom`: warmup: {'corte': 1}; fallos en medición: {'corte': 1} | Por analizar | - | 🔴 Abierto |
| E-018 | 2026-11-01 10:13:57 | B:PG:Q2_WM4:c10:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-019 | 2026-11-01 10:14:35 | C:PG:Q2_WM4:c10:r1 | Corrida terminó en `oom`: warmup: {'corte': 10}; fallos en medición: {'corte': 10} | Por analizar | - | 🔴 Abierto |
| E-020 | 2026-11-01 10:14:38 | B:PG:Q2_WM4:c50:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-021 | 2026-11-01 10:15:13 | C:PG:Q2_WM4:c50:r1 | Corrida terminó en `oom`: warmup: {'corte': 50}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-022 | 2026-11-01 10:15:16 | B:PG:Q2_WM64:c1:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-023 | 2026-11-01 10:15:47 | C:PG:Q2_WM64:c1:r1 | Corrida terminó en `oom`: fallos en medición: {'corte': 1} | Por analizar | - | 🔴 Abierto |
| E-024 | 2026-11-01 10:15:50 | B:PG:Q2_WM64:c10:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-025 | 2026-11-01 10:16:21 | C:PG:Q2_WM64:c10:r1 | Corrida terminó en `oom`: warmup: {'corte': 10}; fallos en medición: {'corte': 10}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
| E-026 | 2026-11-01 10:16:24 | B:PG:Q2_WM64:c50:r1 | Corrida terminó en `error`: OperationalError: connection failed: connection to server at "127.0.0.1", port 54302 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections? | Por analizar | - | 🔴 Abierto |
| E-027 | 2026-11-01 10:16:56 | C:PG:Q2_WM64:c50:r1 | Corrida terminó en `oom`: warmup: {'corte': 50}; fallos en medición: {'corte': 50}; ninguna consulta terminó dentro de la ventana | Por analizar | - | 🔴 Abierto |
