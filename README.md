# EduBot AI — API de Predicción de Deserción

Microservicio REST que analiza el comportamiento de un estudiante dentro del chatbot educativo EduBot AI y calcula la probabilidad de que abandone el curso (**Pd**). Cuando esa probabilidad supera el umbral definido (Pd > 0.65), la API activa la bandera `activar_modo_refuerzo` para que el flujo de Activepieces intervenga con contenido simplificado generado por IA.

---

## Información general

**Módulo:** Módulo 4 - Desarrollo de Aplicaciones con IA    
**Nombre del equipo:** EduBot AI  
**Integrantes:**

- Melvin Josué Pereira Amaya
- Gabriel Eduardo Henriquez Gonzalez
- Alexis Manuel Caliz Magaña

| Campo | Valor |
|---|---|
| **URL base** | `https://edubot-api-db1w.onrender.com` |
| **Documentación interactiva** | `https://edubot-api-db1w.onrender.com/docs` |
| **Versión** | 2.1.0 |
| **Framework** | FastAPI 0.115.0 — Python 3.11 |
| **Modelo ML** | Regresión Logística (scikit-learn) |
| **Hosting** | Render (free tier) |
| **Autenticación** | API Key — header `X-API-Key` |

---

## Cómo encaja en el flujo de EduBot AI

```
Estudiante responde quiz en Telegram
              ↓
         Activepieces
              ↓
    POST /predict  ←──── esta API
              ↓
  ┌─────────────────────┐
  │ activar_modo_refuerzo│
  └─────────────────────┘
       ↙           ↘
    true           false
      ↓               ↓
  API de lenguaje   Siguiente
  (Modo Refuerzo)   lección
      ↓
  Explicación simplificada
  enviada al estudiante
```

La API recibe las métricas del estudiante desde Activepieces, calcula la Pd con el modelo ML y devuelve si se debe activar o no el Modo Refuerzo. El flujo completo lo orquesta Activepieces — esta API es solo el componente de decisión inteligente.

---

## Autenticación

Todos los endpoints de predicción requieren el header `X-API-Key`. Los endpoints del sistema (`/health`, `/metadata`, `/info`, `/version`) son públicos.

```
X-API-Key: {clave proporcionada por el equipo}
```

| Sin header | Con header incorrecto | Con header correcto |
|---|---|---|
| 401 Unauthorized | 403 Forbidden | 200 OK |

---

## Endpoints

### Sistema — públicos

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio y del modelo ML |
| `/metadata` | GET | Versión, tipo de modelo y propósito |
| GET | `/info` | Lista completa de endpoints disponibles |
| GET | `/version` | Versión de la API y del framework |

**Ejemplo `/health`:**
```json
{
  "status": "ok",
  "modelo": "cargado",
  "timestamp": "2026-07-12T16:37:08.440699+00:00"
}
```

---

### Predicción — requieren `X-API-Key`

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/predict` | Predicción con el modelo ML real |
| POST | `/predict/demo` | Predicción con reglas heurísticas (sin modelo) |

> Los alias `/predecir` y `/predecir/demo` también funcionan para compatibilidad con configuraciones anteriores de Activepieces.

---

## Contrato de entrada — `POST /predict`

Todos los campos son obligatorios. La API rechaza automáticamente campos faltantes, de tipo incorrecto o fuera de rango.

```json
{
  "usuario_id":           "123456789",
  "sesiones_semana":       3,
  "quizzes_completados":   5,
  "quizzes_fallados":      2,
  "tiempo_por_leccion":    4.5,
  "dias_sin_ingresar":     1,
  "modulos_completados":   1,
  "porcentaje_progreso":   35.0,
  "mensajes_enviados":     12,
  "calificacion_promedio": 72.5,
  "nivel":                 "basico",
  "dispositivo":           "movil"
}
```

| Campo | Tipo | Rango |
|---|---|---|
| `usuario_id` | string | 1–50 caracteres |
| `sesiones_semana` | integer | 0 a 7 |
| `quizzes_completados` | integer | ≥ 0 |
| `quizzes_fallados` | integer | ≥ 0 |
| `tiempo_por_leccion` | float | 0.0 a 300.0 |
| `dias_sin_ingresar` | integer | 0 a 365 |
| `modulos_completados` | integer | ≥ 0 |
| `porcentaje_progreso` | float | 0.0 a 100.0 |
| `mensajes_enviados` | integer | ≥ 0 |
| `calificacion_promedio` | float | 0.0 a 100.0 |
| `nivel` | string | `basico` \| `intermedio` \| `avanzado` |
| `dispositivo` | string | `movil` \| `desktop` \| `tablet` |

---

## Contrato de salida

```json
{
  "result":                "Comprometido",
  "confidence":            0.2341,
  "model_version":         "v2.1.0",
  "warnings":              [],
  "request_id":            "a3f2c1d4-...",
  "usuario_id":            "123456789",
  "prob_abandono":         0.2341,
  "prob_abandono_pct":     "23.4%",
  "activar_modo_refuerzo": false,
  "nivel_riesgo":          "bajo",
  "timestamp":             "2026-07-12T16:37:08+00:00"
}
```

**El campo clave para Activepieces es `activar_modo_refuerzo`** — si es `true`, el flujo debe llamar a la API de lenguaje para generar la explicación simplificada.

---

## Lógica de riesgo

| Probabilidad (Pd) | `nivel_riesgo` | `activar_modo_refuerzo` | Acción en Activepieces |
|---|---|---|---|
| 0.00 – 0.39 | bajo | `false` | Enviar siguiente lección |
| 0.40 – 0.65 | medio | `false` | Continuar, opcional: mensaje motivacional |
| 0.66 – 1.00 | alto | `true` | Llamar API de lenguaje → Modo Refuerzo |

---

## Warnings automáticos

La API genera advertencias contextuales en el campo `warnings` según el estado del estudiante:

| Warning | Cuándo aparece |
|---|---|
| Riesgo alto detectado — intervención inmediata | Pd > 0.65 |
| El estudiante lleva X días sin ingresar | `dias_sin_ingresar` > 7 |
| Calificación promedio por debajo del 50% | `calificacion_promedio` < 50 |

---

## Integración con Activepieces

Configuración del nodo HTTP Request en el flujo de Activepieces:

```
Method:  POST
URL:     https://edubot-api-db1w.onrender.com/predict
Headers:
  Content-Type: application/json
  X-API-Key:    {clave del equipo}
```

**Body:**
```json
{
  "usuario_id":           "{{trigger.body.message.from.id}}",
  "sesiones_semana":       {{steps.contadores.datos_obj.sesiones_semana}},
  "quizzes_completados":   {{steps.contadores.datos_obj.quizzes_completados}},
  "quizzes_fallados":      {{steps.contadores.datos_obj.quizzes_fallados}},
  "tiempo_por_leccion":    {{steps.contadores.datos_obj.tiempo_por_leccion}},
  "dias_sin_ingresar":     {{steps.contadores.datos_obj.dias_sin_ingresar}},
  "modulos_completados":   {{steps.contadores.datos_obj.modulos_completados}},
  "porcentaje_progreso":   {{steps.contadores.datos_obj.porcentaje_progreso}},
  "mensajes_enviados":     {{steps.contadores.datos_obj.mensajes_enviados}},
  "calificacion_promedio": {{steps.contadores.datos_obj.calificacion_promedio}},
  "nivel":                 "basico",
  "dispositivo":           "movil"
}
```

**Branch después del HTTP Request:**
```
{{steps.api_prediccion.body.activar_modo_refuerzo}} equals true
```

---

## Errores

| Código | Causa | Mensaje |
|---|---|---|
| 401 | No se envió `X-API-Key` | Autenticación requerida |
| 403 | API Key incorrecta | API Key inválida |
| 422 | Campo faltante, tipo incorrecto o fuera de rango | Datos de entrada inválidos + detalle por campo |
| 503 | Modelo ML no cargado | Servicio no disponible |
| 500 | Error interno | Error interno al procesar la predicción |

**Ejemplo de error 422:**
```json
{
  "error": "Datos de entrada inválidos",
  "total_errores": 1,
  "detalle": [
    {
      "campo": "sesiones_semana",
      "problema": "El campo 'sesiones_semana' está fuera del rango permitido. Input should be less than or equal to 7."
    }
  ],
  "sugerencia": "Revisa los tipos y rangos de cada campo antes de reintentar."
}
```

---

## Estructura del repositorio

```
edubot-api/
├── main.py                          # Punto de entrada (Render arranca desde aquí)
├── conftest.py                      # Configuración de pytest
├── requirements.txt                 # Dependencias de producción
├── requirements-dev.txt             # Dependencias de desarrollo y CI
├── Procfile                         # Comando de arranque
├── runtime.txt                      # Versión de Python
├── nixpacks.toml                    # Configuración de build
├── modelo_edubot.pkl                # Modelo ML entrenado
├── scaler_edubot.pkl                # Normalizador de variables
├── columnas_entrenamiento.pkl       # Orden de columnas del entrenamiento
├── app/
│   ├── main.py                      # Inicializa FastAPI y registra rutas
│   ├── api/
│   │   └── routes.py                # Controller: endpoints HTTP
│   ├── schemas/
│   │   └── prediction.py            # Contratos de entrada y salida
│   ├── services/
│   │   └── ai_service.py            # Service: lógica de negocio
│   └── models/
│       └── model_loader.py          # Model: carga .pkl e inferencia
├── docs/
│   └── api.md                       # Contrato documentado
├── tests/
│   └── test_predict.py              # 6 pruebas automáticas con pytest
└── .github/
    └── workflows/
        └── ci.yml                   # Pipeline CI con GitHub Actions
```

---

## Instalación local

```bash
git clone https://github.com/MelvinAmaya/edubot-api.git
cd edubot-api

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements-dev.txt

# Configurar variable de entorno
set EDUBOT_API_KEY=tu_clave_aqui     # Windows
export EDUBOT_API_KEY=tu_clave_aqui  # Mac/Linux

uvicorn main:app --reload --port 8000
```

Abrir: `http://127.0.0.1:8000/docs`

---

## Ejecutar tests

```bash
pip install pytest httpx
pytest tests/ -v
```

---

## Variables de entorno

| Variable | Descripción | Obligatoria |
|---|---|---|
| `EDUBOT_API_KEY` | Clave de autenticación | Sí |
| `MODEL_PATH` | Ruta al modelo `.pkl` | No (usa valor por defecto) |
| `SCALER_PATH` | Ruta al scaler `.pkl` | No (usa valor por defecto) |
| `COLUMNS_PATH` | Ruta a columnas `.pkl` | No (usa valor por defecto) |

> ⚠️ Nunca expongas `EDUBOT_API_KEY` en el código. Configúrala como variable de entorno en Render y como secret en GitHub Actions.

---

## Notas

- El plan gratuito de Render puede generar un **cold start de ~30 segundos** si el servicio estuvo inactivo. El segundo request es inmediato.
- El modelo fue entrenado con datos sintéticos del laboratorio. Requiere reentrenamiento con datos reales una vez recopilados del piloto.
- Los alias `/predecir` y `/predecir/demo` no aparecen en `/docs` pero responden normalmente para compatibilidad con configuraciones existentes de Activepieces.
