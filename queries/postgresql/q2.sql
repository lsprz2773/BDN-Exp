SELECT data->>'resultado_id' AS resultado_id,
       data->'alumno'->>'id' AS alumno_id,
       (data->'calificacion'->>'final')::numeric AS final
FROM resultados_unidad
WHERE data->'unidad'->>'estado' = 'cerrada'
  AND data->>'cerrado_en' >= '2026-01-01T00:00:00Z'
ORDER BY (data->'calificacion'->>'final')::numeric DESC
LIMIT 1000;
