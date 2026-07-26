# EduBot AI — Contrato de la API

## Endpoint principal

**POST /predict**

### Entrada
```json
{
  "usuario_id": "123456789",
  "sesiones_semana": 3,
  "quizzes_completados": 5,
  "quizzes_fallados": 2,
  "tiempo_por_leccion": 4.5,
  "dias_sin_ingresar": 1,
  "modulos_completados": 1,
  "porcentaje_progreso": 35.0,
  "mensajes_enviados": 12,
  "calificacion_promedio": 72.5,
  "nivel": "basico",
  "dispositivo": "movil"
}
```

### Salida exitosa (200)
```json
{
  "result": "Comprometido",
  "confidence": 0.2341,
  "model_version": "v2.1.0",
  "warnings": [],
  "request_id": "uuid-generado",
  "usuario_id": "123456789",
  "prob_abandono": 0.2341,
  "prob_abandono_pct": "23.4%",
  "activar_modo_refuerzo": false,
  "nivel_riesgo": "bajo",
  "timestamp": "2026-07-12T16:37:08"
}
```

### Errores esperados
- **400/422**: entrada inválida — campo faltante, tipo incorrecto o fuera de rango
- **401**: no se envió el header X-API-Key
- **403**: API Key incorrecta
- **503**: modelo ML no cargado
- **500**: falla interna del servicio

### Herramienta de prueba
Thunder Client / Swagger UI en /docs

### Ejemplo inválido (provoca 422)
```json
{
  "usuario_id": "",
  "sesiones_semana": 10
}
```
