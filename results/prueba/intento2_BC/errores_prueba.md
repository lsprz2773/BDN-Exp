# ERRORES DE LA SUITE DE PRUEBA

## Errores abiertos o en corrección

| ID | Fecha/hora | Origen | Descripción | Causa | Corrección aplicada | ESTATUS |
|---|---|---|---|---|---|---|
| E-001 | 2026-11-01 10:45:28 | C:PG:Q1:c50:r1 | Corrida terminó en `oom`: warmup: {'corte': 7, 'error': 43}; oom_kill en el contenedor: 9; fallos en medición: {'error': 201}; OperationalError: consuming input failed: server closed the connection unexpectedly 	This probably means the server terminated abnormally 	before or while processing the request.; ninguna consulta terminó dentro de la ventana | Esperado: 50 consultas Q1 con spill en 1 GB agotan la memoria (resultado válido para M2) | Ninguna; el runner lo detectó por delta de oom_kill y reconectó | 🔵 Aceptado |
