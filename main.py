# ============================================================
#  EduBot AI — API de Predicción de Deserción
#  Versión estandarizada con:
#    - API Key para autenticación
#    - Validación estricta de entradas (Pydantic + Field)
#    - Endpoints obligatorios: /health, /info, /version
#    - Mensajes de error entendibles
#    - Protección contra datos sensibles innecesarios
# ============================================================

from fastapi import FastAPI, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
import os

# ══════════════════════════════════════════════════════
#  CONFIGURACIÓN GENERAL
# ══════════════════════════════════════════════════════
API_VERSION    = "2.0.0"
API_NAME       = "EduBot AI — API de Predicción de Deserción"
STARTUP_TIME   = datetime.utcnow().isoformat()

# API Key — se lee desde variable de entorno (Railway → Variables)
# En Railway: agregar variable EDUBOT_API_KEY con el valor que elijas
API_KEY_VALUE  = os.getenv("EDUBOT_API_KEY", "edubot-dev-key-2026")
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# ══════════════════════════════════════════════════════
#  INICIALIZAR APP
# ══════════════════════════════════════════════════════
app = FastAPI(
    title=API_NAME,
    description="API estandarizada que calcula la probabilidad de abandono (Pd) de un estudiante de EduBot AI.",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ══════════════════════════════════════════════════════
#  CARGAR MODELO AL ARRANCAR
# ══════════════════════════════════════════════════════
MODEL_PATH   = os.getenv("MODEL_PATH",   "modelo_edubot.pkl")
SCALER_PATH  = os.getenv("SCALER_PATH",  "scaler_edubot.pkl")
COLUMNS_PATH = os.getenv("COLUMNS_PATH", "columnas_entrenamiento.pkl")

try:
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    X_cols = joblib.load(COLUMNS_PATH)
    MODEL_STATUS = "cargado"
    print("✅ Modelo, scaler y columnas cargados correctamente.")
except FileNotFoundError as e:
    model, scaler, X_cols = None, None, None
    MODEL_STATUS = "no cargado"
    print(f"⚠️  Archivo no encontrado: {e}")


# ══════════════════════════════════════════════════════
#  AUTENTICACIÓN — API KEY
# ══════════════════════════════════════════════════════
def verificar_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Valida que el header X-API-Key esté presente y sea correcto.
    Si no se envía o es incorrecto, responde con 401.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Autenticación requerida",
                "mensaje": "Debes enviar el header 'X-API-Key' con tu clave de acceso."
            }
        )
    if api_key != API_KEY_VALUE:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "API Key inválida",
                "mensaje": "La clave proporcionada no es correcta o ha expirado."
            }
        )
    return api_key


# ══════════════════════════════════════════════════════
#  MANEJO GLOBAL DE ERRORES DE VALIDACIÓN
#  (mensajes entendibles, no mensajes técnicos de Pydantic)
# ══════════════════════════════════════════════════════
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = []
    for error in exc.errors():
        campo = " → ".join(str(e) for e in error["loc"] if e != "body")
        tipo  = error["type"]
        msg   = error["msg"]

        # Mensajes personalizados por tipo de error
        if "missing" in tipo:
            descripcion = f"El campo '{campo}' es obligatorio y no fue enviado."
        elif "greater_than_equal" in tipo or "less_than_equal" in tipo:
            descripcion = f"El campo '{campo}' está fuera del rango permitido. {msg}."
        elif "string_pattern_mismatch" in tipo:
            descripcion = f"El campo '{campo}' tiene un valor no permitido. {msg}."
        elif "int_parsing" in tipo or "float_parsing" in tipo:
            descripcion = f"El campo '{campo}' debe ser un número, no texto."
        else:
            descripcion = f"Error en '{campo}': {msg}."

        errores.append({"campo": campo, "problema": descripcion})

    return JSONResponse(
        status_code=422,
        content={
            "error": "Datos de entrada inválidos",
            "total_errores": len(errores),
            "detalle": errores,
            "sugerencia": "Revisa los tipos y rangos de cada campo antes de reintentar."
        }
    )


# ══════════════════════════════════════════════════════
#  SCHEMAS — ENTRADA Y SALIDA
# ══════════════════════════════════════════════════════
class DatosEstudiante(BaseModel):
    """
    Datos de comportamiento del estudiante.
    Todos los campos son obligatorios.
    No se aceptan campos vacíos, fuera de rango o de tipo incorrecto.
    """
    # ── Identificador ──────────────────────────────
    usuario_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="ID único del usuario (ID de Telegram, no datos personales)"
    )

    # ── Variables de actividad ─────────────────────
    sesiones_semana: int = Field(
        ..., ge=0, le=7,
        description="Días activo en los últimos 7 días (0 a 7)"
    )
    quizzes_completados: int = Field(
        ..., ge=0, le=500,
        description="Total de quizzes respondidos correctamente"
    )
    quizzes_fallados: int = Field(
        ..., ge=0, le=500,
        description="Total de quizzes respondidos incorrectamente"
    )
    tiempo_por_leccion: float = Field(
        ..., ge=0.0, le=300.0,
        description="Minutos promedio por lección (0 a 300)"
    )
    dias_sin_ingresar: int = Field(
        ..., ge=0, le=365,
        description="Días desde el último acceso (0 a 365)"
    )
    modulos_completados: int = Field(
        ..., ge=0, le=100,
        description="Módulos completos hasta ahora"
    )
    porcentaje_progreso: float = Field(
        ..., ge=0.0, le=100.0,
        description="Porcentaje del curso completado (0.0 a 100.0)"
    )
    mensajes_enviados: int = Field(
        ..., ge=0, le=10000,
        description="Total de mensajes enviados al bot"
    )
    calificacion_promedio: float = Field(
        ..., ge=0.0, le=100.0,
        description="Promedio de notas en quizzes (0.0 a 100.0)"
    )

    # ── Variables categóricas ──────────────────────
    nivel: str = Field(
        ...,
        pattern="^(basico|intermedio|avanzado)$",
        description="Nivel del estudiante: 'basico', 'intermedio' o 'avanzado'"
    )
    dispositivo: str = Field(
        ...,
        pattern="^(movil|desktop|tablet)$",
        description="Dispositivo usado: 'movil', 'desktop' o 'tablet'"
    )

    # ── Validaciones adicionales de lógica de negocio ──
    @field_validator("usuario_id")
    @classmethod
    def usuario_id_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El usuario_id no puede ser un texto vacío o solo espacios.")
        return v.strip()

    @field_validator("porcentaje_progreso")
    @classmethod
    def progreso_coherente(cls, v):
        # Redondear a 2 decimales para evitar ruido
        return round(v, 2)

    @field_validator("calificacion_promedio")
    @classmethod
    def calificacion_coherente(cls, v):
        return round(v, 2)

    class Config:
        # Rechaza campos extra que no estén definidos en el schema
        extra = "forbid"
        json_schema_extra = {
            "example": {
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
        }


class ResultadoPrediccion(BaseModel):
    usuario_id: str
    prob_abandono: float
    prob_abandono_pct: str
    prediccion: str
    activar_modo_refuerzo: bool
    confianza: str
    nivel_riesgo: str
    timestamp: str


# ══════════════════════════════════════════════════════
#  ENDPOINTS OBLIGATORIOS (sin API Key — son públicos)
# ══════════════════════════════════════════════════════

@app.get("/health", tags=["Sistema"])
def health():
    """
    Estado del servicio.
    Devuelve si la API y el modelo están operativos.
    No requiere autenticación.
    """
    return {
        "status": "ok",
        "modelo": MODEL_STATUS,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_desde": STARTUP_TIME
    }


@app.get("/info", tags=["Sistema"])
def info():
    """
    Información general de la API:
    nombre, versión, descripción y endpoints disponibles.
    No requiere autenticación.
    """
    return {
        "nombre": API_NAME,
        "version": API_VERSION,
        "descripcion": "API de predicción de probabilidad de deserción estudiantil para EduBot AI.",
        "autores": "Equipo EduBot AI — Universidad Gerardo Barrios",
        "endpoints": {
            "GET  /health":         "Estado del servicio (público)",
            "GET  /info":           "Información de la API (público)",
            "GET  /version":        "Versión de la API (público)",
            "POST /predecir":       "Predicción con modelo ML (requiere X-API-Key)",
            "POST /predecir/demo":  "Predicción heurística para pruebas (requiere X-API-Key)"
        },
        "autenticacion": "Header X-API-Key requerido en endpoints de predicción"
    }


@app.get("/version", tags=["Sistema"])
def version():
    """
    Versión actual de la API.
    No requiere autenticación.
    """
    return {
        "version": API_VERSION,
        "modelo_ml": MODEL_STATUS,
        "framework": "FastAPI 0.115.0",
        "python": "3.12"
    }


# ══════════════════════════════════════════════════════
#  ENDPOINTS DE PREDICCIÓN (requieren API Key)
# ══════════════════════════════════════════════════════

@app.post(
    "/predecir",
    response_model=ResultadoPrediccion,
    tags=["Predicción"],
    summary="Predecir deserción con modelo ML"
)
def predecir(datos: DatosEstudiante, api_key: str = Security(verificar_api_key)):
    """
    Recibe los datos de comportamiento de un estudiante y devuelve
    la probabilidad de abandono calculada por el modelo de Machine Learning.

    Requiere el header: X-API-Key
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Servicio no disponible",
                "mensaje": "El modelo de predicción no está cargado. Contacta al administrador.",
                "alternativa": "Usa el endpoint /predecir/demo para pruebas sin modelo."
            }
        )

    try:
        # Construir DataFrame replicando el preprocesamiento del entrenamiento
        entrada = {
            "sesiones_semana"      : datos.sesiones_semana,
            "quizzes_completados"  : datos.quizzes_completados,
            "quizzes_fallados"     : datos.quizzes_fallados,
            "tiempo_por_leccion"   : datos.tiempo_por_leccion,
            "dias_sin_ingresar"    : datos.dias_sin_ingresar,
            "modulos_completados"  : datos.modulos_completados,
            "porcentaje_progreso"  : datos.porcentaje_progreso,
            "mensajes_enviados"    : datos.mensajes_enviados,
            "calificacion_promedio": datos.calificacion_promedio,
            "nivel"                : datos.nivel,
            "dispositivo"          : datos.dispositivo,
        }

        df_nuevo = pd.DataFrame([entrada])
        df_nuevo = pd.get_dummies(df_nuevo, columns=["nivel", "dispositivo"])

        # Completar columnas faltantes con 0 (mismo esquema que entrenamiento)
        for col in X_cols:
            if col not in df_nuevo.columns:
                df_nuevo[col] = 0
        df_nuevo = df_nuevo[X_cols]

        datos_scaled = scaler.transform(df_nuevo)
        prob = float(model.predict_proba(datos_scaled)[0][1])

        nivel_riesgo = "bajo" if prob < 0.40 else "medio" if prob < 0.65 else "alto"

        return ResultadoPrediccion(
            usuario_id            = datos.usuario_id,
            prob_abandono         = round(prob, 4),
            prob_abandono_pct     = f"{prob * 100:.1f}%",
            prediccion            = "Riesgo de abandono" if prob >= 0.5 else "Comprometido",
            activar_modo_refuerzo = prob > 0.65,
            confianza             = f"{max(prob, 1 - prob) * 100:.1f}%",
            nivel_riesgo          = nivel_riesgo,
            timestamp             = datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error interno al procesar la predicción",
                "mensaje": str(e)
            }
        )


@app.post(
    "/predecir/demo",
    tags=["Predicción"],
    summary="Predecir deserción con reglas heurísticas (sin modelo ML)"
)
def predecir_demo(datos: DatosEstudiante, api_key: str = Security(verificar_api_key)):
    """
    Calcula la probabilidad de deserción usando reglas heurísticas ponderadas,
    sin necesidad del modelo ML entrenado.

    Usar mientras no se tengan suficientes datos reales para validar el modelo.
    Requiere el header: X-API-Key
    """
    try:
        score = 0.0
        score += max(0, (7 - datos.sesiones_semana) / 7) * 0.25
        score += min(datos.dias_sin_ingresar / 10, 1.0) * 0.30
        tasa_fallo = datos.quizzes_fallados / max(
            datos.quizzes_completados + datos.quizzes_fallados, 1
        )
        score += tasa_fallo * 0.20
        score += max(0, (50 - datos.calificacion_promedio) / 50) * 0.15
        score += max(0, (50 - datos.porcentaje_progreso) / 100) * 0.10

        prob = round(min(score, 0.99), 4)
        nivel_riesgo = "bajo" if prob < 0.40 else "medio" if prob < 0.65 else "alto"

        return {
            "usuario_id"            : datos.usuario_id,
            "prob_abandono"         : prob,
            "prob_abandono_pct"     : f"{prob * 100:.1f}%",
            "prediccion"            : "Riesgo de abandono" if prob >= 0.5 else "Comprometido",
            "activar_modo_refuerzo" : prob > 0.65,
            "confianza"             : "N/A (modo heurístico)",
            "nivel_riesgo"          : nivel_riesgo,
            "timestamp"             : datetime.utcnow().isoformat(),
            "nota"                  : "Modo demo — reemplazar con /predecir cuando el modelo esté validado"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error interno al calcular la predicción",
                "mensaje": str(e)
            }
        )
