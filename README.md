# EduBot AI — API de Predicción de Deserción

> Microservicio inteligente que calcula la probabilidad de abandono de un estudiante dentro del chatbot educativo EduBot AI.

## 1. Información General

**Módulo:** Módulo 4 - Desarrollo de Aplicaciones con IA    
**Nombre del equipo:** EduBot AI  
**Integrantes:**

- Melvin Josué Pereira Amaya
- Gabriel Eduardo Henriquez Gonzalez
- Alexis Manuel Caliz Magaña

---

## 2. Descripción del Problema

El chatbot educativo EduBot AI enfrenta el problema de la deserción estudiantil en cursos en línea, donde las tasas de abandono pueden superar el 80%. El sistema necesita detectar de forma anticipada qué estudiantes están en riesgo de abandonar para poder intervenir con contenido simplificado antes de que deserten.

**Preguntas guía:**

- ¿Qué problema real se quiere resolver? La detección temprana de deserción en estudiantes que usan el bot de Telegram.
- ¿A quién afecta? A estudiantes universitarios que aprenden a través del chatbot EduBot AI.
- ¿En qué contexto ocurre? Durante la interacción del estudiante con el bot (quizzes, lecciones, tiempo de respuesta).
- ¿Por qué una IA puede aportar valor? Porque analiza patrones de comportamiento en tiempo real y genera una probabilidad objetiva de abandono, algo que no es posible determinar manualmente a escala.

---

## 3. Usuarios o Beneficiarios

| Usuario / Beneficiario | Necesidad principal | Cómo ayuda la aplicación |
|---|---|---|
| Bot de Telegram (EduBot) | Saber si un estudiante está en riesgo para activar el Modo Refuerzo | Llama a la API después de cada quiz y recibe la predicción automáticamente |
| Estudiante universitario | Recibir ayuda cuando tiene dificultades antes de abandonar | El sistema detecta su riesgo y le envía explicaciones simplificadas |
| Equipo docente | Monitorear qué estudiantes necesitan intervención | La API genera advertencias contextuales sobre el estado de cada estudiante |
| Plataforma de automatización (Activepieces) | Orquestar el flujo del bot según el riesgo del estudiante | Consume la API vía HTTP y bifurca el flujo según `activar_modo_refuerzo` |

---

## 4. Descripción de la Solución

La API de Predicción de Deserción es un microservicio REST construido con FastAPI que recibe los datos de comportamiento de un estudiante y devuelve la probabilidad de que abandone el curso (Pd).

- **Entrada:** 12 métricas de comportamiento del estudiante (sesiones, quizzes, progreso, tiempo, etc.)
- **Proceso:** Preprocesamiento de datos + inferencia con modelo de Regresión Logística entrenado en scikit-learn
- **Salida:** Probabilidad de abandono, nivel de riesgo, si se debe activar el Modo Refuerzo y advertencias contextuales

Cuando `activar_modo_refuerzo` es `true` (Pd > 0.65), el bot llama a una segunda API de lenguaje (Groq + Llama 3) que genera una explicación simplificada del tema para el estudiante.

---

## 5. Componente de Inteligencia Artificial

| Elemento | Descripción |
|---|---|
| Tipo de IA utilizada | Machine Learning supervisado — clasificación binaria |
| Modelo | Regresión Logística (scikit-learn 1.6.1) |
| Datos de entrada | 12 métricas: sesiones_semana, quizzes_completados, quizzes_fallados, tiempo_por_leccion, dias_sin_ingresar, modulos_completados, porcentaje_progreso, mensajes_enviados, calificacion_promedio, nivel, dispositivo, usuario_id |
| Resultado generado | Probabilidad de deserción (0.0 a 1.0) y bandera `activar_modo_refuerzo` |
| Métrica de evaluación | Umbral Pd > 0.65 para activar intervención (definido en el anteproyecto) |
| Limitaciones actuales | El modelo fue entrenado con datos sintéticos; requiere reentrenamiento con datos reales de usuarios |

**Explicación breve:**

El modelo analiza el comportamiento del estudiante en tiempo real. Cuando detecta patrones asociados a la deserción (muchos días inactivo, quizzes fallados, calificación baja), calcula una probabilidad alta de abandono y activa automáticamente el Modo Refuerzo, que usa IA generativa (Llama 3 vía Groq) para explicar el tema de forma simplificada.

---

## 6. Estado Actual del Proyecto

### Funcionalidades que ya funcionan

- API deployada en Render con URL pública activa
- Modelo de Regresión Logística cargado y funcionando en producción
- Autenticación con API Key (header `X-API-Key`)
- Validación estricta de entradas con mensajes de error en español
- Endpoints del sistema: `/health`, `/metadata`, `/info`, `/version`
- Endpoints de predicción: `/predict` (ML real) y `/predict/demo` (heurístico)
- Documentación interactiva en `/docs` (Swagger UI)
- Tests automáticos con pytest (6 pruebas, todas pasando)
- README y contrato de API documentados

### Funcionalidades incompletas o pendientes

- Reentrenar el modelo con datos reales de usuarios del bot
- Integración completa con Supabase para persistencia del historial de Pd
- Pipeline CI/CD para deploy automático al hacer push a GitHub

### Evidencias actuales

- API en producción: https://edubot-api-db1w.onrender.com
- Documentación Swagger: https://edubot-api-db1w.onrender.com/docs
- Repositorio: https://github.com/MelvinAmaya/edubot-api

---

## 7. Arquitectura Actual

**Componentes actuales:**

| Componente | Descripción | Estado actual |
|---|---|---|
| Bot de Telegram | Chatbot educativo con flujo de lecciones y quizzes | ✅ Funcionando |
| Activepieces | Plataforma de automatización que orquesta el flujo del bot | ✅ Funcionando |
| API de Predicción | FastAPI en Render — calcula la Pd del estudiante | ✅ Funcionando |
| Modelo ML | Regresión Logística entrenada con scikit-learn | ✅ Cargado |

**Flujo actual:**

```
Bot Telegram → Activepieces → POST /predict → Modelo ML → activar_modo_refuerzo
                                                                    ↓
                                                    true → API Groq+Llama → explicación
                                                    false → siguiente lección
```

---

## 8. Arquitectura Objetivo

**Elementos esperados al finalizar el módulo:**

- API de predicción con modelo reentrenado con datos reales
- Separación completa en capas: Controller → Service → Model ✅ (implementado en Semana 2)
- Tests automáticos con cobertura mínima del 80% (Semana 3)
- Pipeline CI/CD con GitHub Actions (Semana 3)
- Variables de entorno para todas las credenciales ✅ (implementado)
- Logs de predicciones guardados en Supabase
- Consideraciones de seguridad: API Key ✅, sin datos personales en logs ✅

---

## 9. Estructura del Repositorio

```text
edubot-api/
├── main.py                          # Punto de entrada — Render arranca desde aquí
├── conftest.py                      # Configuración de pytest
├── requirements.txt                 # Dependencias de Python
├── Procfile                         # Comando de arranque para Render
├── runtime.txt                      # Versión de Python
├── nixpacks.toml                    # Configuración de build
├── modelo_edubot.pkl                # Modelo ML entrenado (Regresión Logística)
├── scaler_edubot.pkl                # Normalizador de variables numéricas
├── columnas_entrenamiento.pkl       # Orden de columnas tras One-Hot Encoding
├── app/
│   ├── main.py                      # Inicializa FastAPI y registra rutas
│   ├── api/
│   │   └── routes.py                # CONTROLLER: define todos los endpoints
│   ├── schemas/
│   │   └── prediction.py            # Contratos de entrada y salida (Pydantic)
│   ├── services/
│   │   └── ai_service.py            # SERVICE: lógica de negocio y predicción
│   └── models/
│       └── model_loader.py          # MODEL: carga .pkl y funciones de inferencia
├── docs/
│   └── api.md                       # Contrato de la API documentado
└── tests/
    └── test_predict.py              # Tests automáticos con pytest
```

**Notas sobre la estructura:**

- `app/api/` contiene el controlador HTTP — solo recibe y responde, sin lógica de negocio
- `app/services/` contiene toda la lógica de decisión (qué modelo usar, warnings, respuesta)
- `app/models/` contiene la carga de los archivos `.pkl` y las funciones de inferencia puras
- `app/schemas/` define los contratos de entrada y salida con validación automática
- Los archivos `.pkl` van en la raíz porque `model_loader.py` los busca ahí al arrancar

---

## 10. Instalación y Ejecución

### Requisitos previos

- Python 3.11 o superior
- pip
- Los archivos `modelo_edubot.pkl`, `scaler_edubot.pkl` y `columnas_entrenamiento.pkl`

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/MelvinAmaya/edubot-api.git
cd edubot-api

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecución

```bash
uvicorn main:app --reload --port 8000
```

Abrir en el navegador: http://127.0.0.1:8000/docs

### Variables de entorno

| Variable | Descripción | Obligatoria |
|---|---|---|
| `EDUBOT_API_KEY` | Clave de autenticación para los endpoints de predicción | Sí |
| `MODEL_PATH` | Ruta al archivo `modelo_edubot.pkl` | No (usa valor por defecto) |
| `SCALER_PATH` | Ruta al archivo `scaler_edubot.pkl` | No (usa valor por defecto) |
| `COLUMNS_PATH` | Ruta al archivo `columnas_entrenamiento.pkl` | No (usa valor por defecto) |

Crear un archivo `.env` local (no subir a GitHub):

```bash
EDUBOT_API_KEY=tu_clave_secreta_aqui
```

---

## 11. Datos Utilizados

| Fuente de datos | Tipo de datos | Uso dentro del proyecto | Observaciones |
|---|---|---|---|
| Dataset sintético del laboratorio ML | CSV con métricas de comportamiento estudiantil | Entrenamiento del modelo de Regresión Logística | Generado con datos simulados — requiere reemplazo con datos reales |
| Comportamiento del usuario en el bot | Métricas en tiempo real (quizzes, sesiones, tiempo) | Input del endpoint `/predict` en producción | No contiene datos personales — solo el ID de Telegram |

**Consideraciones:**

- Los datos de entrenamiento son sintéticos — el modelo necesita reentrenamiento con datos reales
- El `usuario_id` es el ID numérico de Telegram, no nombre ni datos personales
- No se almacena ningún dato del usuario en la API — es stateless

---

## 12. Riesgos Técnicos y Deuda Técnica

| Riesgo | Categoría | Probabilidad | Impacto | Mitigación propuesta |
|---|---|---|---|---|
| Modelo entrenado con datos sintéticos | Modelo | Alta | Alto | Reentrenar con datos reales de los primeros 100 usuarios piloto |
| Cold start de Render (30s en primer request) | Despliegue | Alta | Medio | Implementar ping periódico o migrar a plan pago si hay usuarios reales |
| API Key hardcodeada en Activepieces | Seguridad | Media | Alto | Rotar la key periódicamente y usar variables de entorno en Activepieces |
| Sin CI/CD — deploy manual | Código | Media | Medio | Implementar GitHub Actions en Semana 3 |
| Sin persistencia de predicciones | Datos | Media | Medio | Integrar Supabase para guardar historial de Pd por usuario |

---

## 13. Plan de Mejora por Semana

| Semana | Mejora esperada | Evidencia esperada |
|---|---|---|
| Semana 2 | API estandarizada con capas Controller/Service/Model, autenticación y contratos | ✅ Endpoints funcionando, Swagger, tests con pytest, README |
| Semana 3 | Tests con mayor cobertura y pipeline CI/CD | Tests automáticos, GitHub Actions, evidencia de pipeline |
| Semana 4 | Contenedor Docker o estrategia de despliegue mejorada | Dockerfile, servicio en contenedor |
| Semana 5 | Observabilidad: logs de predicciones y métricas | Logs en Supabase, dashboard básico |
| Semana 6 | Reentrenamiento con datos reales y documentación final | Modelo actualizado, demo, presentación final |

---

## 14. Limitaciones Actuales

- El modelo fue entrenado con datos sintéticos del laboratorio, no con comportamiento real de estudiantes
- El plan gratuito de Render genera un cold start de ~30 segundos cuando el servicio está inactivo
- No existe pipeline CI/CD — los cambios se despliegan manualmente subiendo a GitHub
- La API no persiste el historial de predicciones — cada request es independiente
- Sin sistema de rotación automática de la API Key

---

## 15. Evidencias

| Evidencia | Enlace o ubicación | Descripción |
|---|---|---|
| API en producción | https://edubot-api-db1w.onrender.com/health | Health check del servicio |
| Swagger UI | https://edubot-api-db1w.onrender.com/docs | Documentación interactiva |
| Repositorio | https://github.com/MelvinAmaya/edubot-api | Código fuente completo |
| Tests automáticos | `tests/test_predict.py` | 6 pruebas — todas pasando |
| Contrato de API | `docs/api.md` | Entrada, salida y errores documentados |
| Notebook de entrenamiento | `laboratorio_1_machine_learning.py` | Entrenamiento del modelo ML |

---

## 16. Créditos y Referencias

- [FastAPI](https://fastapi.tiangolo.com/) — Framework web para Python
- [scikit-learn](https://scikit-learn.org/) — Librería de Machine Learning
- [Pydantic](https://docs.pydantic.dev/) — Validación de datos
- [Render](https://render.com/) — Plataforma de hosting gratuito
- [Groq](https://console.groq.com/) — Inferencia rápida con Llama 3
- [Activepieces](https://www.activepieces.com/) — Plataforma de automatización
- Universidad Gerardo Barrios — Módulo 4, Desarrollo de Aplicaciones con IA

---

## 17. Checklist de Revisión

- [x] El problema está claramente descrito.
- [x] Se explica quién usará o se beneficiará de la aplicación.
- [x] Se identifica dónde está la IA.
- [x] Se describen entradas y salidas.
- [x] Se documenta el estado actual del proyecto.
- [x] Se incluye arquitectura actual.
- [x] Se incluye arquitectura objetivo.
- [x] Se explica cómo ejecutar el proyecto.
- [x] Se identifican riesgos técnicos.
- [x] Se presenta plan de mejora por semana.
- [x] No se incluyen claves, contraseñas ni tokens privados.
