# ============================================================
#  EduBot AI — Capa Controller (Routes)
#  Define todos los endpoints HTTP.
# ============================================================

from fastapi import APIRouter, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from datetime import datetime, timezone
import os

from app.schemas.prediction import DatosEstudiante, ResultadoPrediccion
from app.services.ai_service import ejecutar_prediccion
from app.models.model_loader import MODEL_STATUS

router = APIRouter()

API_KEY_VALUE  = os.getenv("EDUBOT_API_KEY", "edubot-dev-key-2026")
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

API_VERSION   = "2.1.0"
MODEL_VERSION = "v2.1.0"
API_NAME      = "EduBot AI — API de Predicción de Deserción"


def verificar_api_key(api_key: str = Security(API_KEY_HEADER)):
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


# ── Endpoints del sistema (públicos) ───────────────────────

@router.get("/health", tags=["Sistema"])
def health():
    return {
        "status"   : "ok",
        "modelo"   : MODEL_STATUS,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/metadata", tags=["Sistema"])
def metadata():
    return {
        "nombre"            : API_NAME,
        "version"           : API_VERSION,
        "model_version"     : MODEL_VERSION,
        "modelo_tipo"       : "Regresión Logística (scikit-learn 1.6.1)",
        "modelo_status"     : MODEL_STATUS,
        "proposito"         : "Predecir probabilidad de deserción estudiantil en EduBot AI",
        "endpoint_principal": "/predict",
        "autenticacion"     : "Header X-API-Key requerido en endpoints de predicción",
        "documentacion"     : "/docs"
    }


@router.get("/info", tags=["Sistema"])
def info():
    return {
        "nombre"     : API_NAME,
        "version"    : API_VERSION,
        "descripcion": "API de predicción de probabilidad de deserción estudiantil para EduBot AI.",
        "autores"    : "Equipo EduBot AI — Universidad Gerardo Barrios",
        "endpoints"  : {
            "GET  /health"       : "Estado del servicio (público)",
            "GET  /metadata"     : "Metadatos del modelo y servicio (público)",
            "GET  /info"         : "Información general (público)",
            "GET  /version"      : "Versión actual (público)",
            "POST /predict"      : "Predicción con modelo ML (requiere X-API-Key)",
            "POST /predict/demo" : "Predicción heurística (requiere X-API-Key)"
        }
    }


@router.get("/version", tags=["Sistema"])
def version():
    return {
        "api_version"  : API_VERSION,
        "model_version": MODEL_VERSION,
        "modelo_status": MODEL_STATUS,
        "framework"    : "FastAPI 0.115.0",
        "python"       : "3.11.9"
    }


# ── Endpoints de predicción (requieren X-API-Key) ──────────

@router.post(
    "/predict",
    response_model=ResultadoPrediccion,
    tags=["Predicción"],
    summary="Predecir deserción con modelo ML"
)
def predict(datos: DatosEstudiante, api_key: str = Security(verificar_api_key)):
    try:
        return ejecutar_prediccion(datos, usar_modelo=True)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno al procesar la predicción", "mensaje": str(e)}
        )


@router.post(
    "/predict/demo",
    tags=["Predicción"],
    summary="Predecir deserción con reglas heurísticas (sin modelo ML)"
)
def predict_demo(datos: DatosEstudiante, api_key: str = Security(verificar_api_key)):
    try:
        resultado = ejecutar_prediccion(datos, usar_modelo=False)
        data = resultado.model_dump()   # ← model_dump() en lugar de .dict()
        data["nota"] = "Modo demo — reemplazar con /predict cuando el modelo esté validado"
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno al calcular la predicción", "mensaje": str(e)}
        )


# ── Aliases para compatibilidad con Activepieces ───────────

@router.post("/predecir", include_in_schema=False)
def predecir_alias(datos: DatosEstudiante, api_key: str = Security(verificar_api_key)):
    return predict(datos, api_key)


@router.post("/predecir/demo", include_in_schema=False)
def predecir_demo_alias(datos: DatosEstudiante, api_key: str = Security(verificar_api_key)):
    return predict_demo(datos, api_key)