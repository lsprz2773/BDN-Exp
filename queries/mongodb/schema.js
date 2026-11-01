// Esquema MongoDB para la práctica (ver data/ESQUEMA_DATASET.md).
// Uso: mongosh "mongodb://localhost:<puerto>/control_academico" queries/mongodb/schema.js
// Colección única, sin sharding (WiredTiger por defecto). Índices exigidos por la spec:
// simple en la fecha y simple en el id del documento. No se indexa calificacion.final (Q2).

db.createCollection("resultados_unidad");

db.resultados_unidad.createIndex({ cerrado_en: 1 }, { name: "idx_cerrado_en" });
db.resultados_unidad.createIndex({ resultado_id: 1 }, { name: "idx_resultado_id" });

printjson(db.resultados_unidad.getIndexes());
