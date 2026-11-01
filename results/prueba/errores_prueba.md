# ERRORES DE LA SUITE DE PRUEBA

## Errores abiertos o en corrección

| ID | Fecha/hora | Origen | Descripción | Causa | Corrección aplicada | ESTATUS |
|---|---|---|---|---|---|---|
| E-001 | 2026-11-01 11:44:48 | C:PG:Q1:c50:r1 | Corrida terminó en `oom`: warmup: {'error': 53}; oom_kill en el contenedor: 5; fallos en medición: {'error': 1262}; OperationalError: consuming input failed: server closed the connection unexpectedly 	This probably means the server terminated abnormally 	before or while processing the request.; ninguna consulta terminó dentro de la ventana | Esperado: 50 consultas Q1 con spill en 1 GB agotan la memoria (resultado válido para M2) | Ninguna; detectado por delta de oom_kill, con reconexión | 🔵 Aceptado |
