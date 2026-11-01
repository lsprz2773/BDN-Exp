SELECT data->'contexto'->'materia'->>'nombre' AS materia,
       d->>'criterio' AS criterio,
       SUM((d->>'porcentaje')::numeric * (d->>'promedio')::numeric) AS total_aporte,
       AVG((d->>'porcentaje')::numeric * (d->>'promedio')::numeric) AS avg_aporte,
       COUNT(*) AS count
FROM resultados_unidad, jsonb_array_elements(data->'calificacion'->'desglose') AS d
WHERE (d->>'promedio')::numeric > 6
GROUP BY 1, 2;
