# ============================================================
#  EduBot AI — Capa Service
#  Coordina la lógica de negocio.
# ============================================================

import uuid
from datetime import datetime, timezone

from app.models.model_loader import (
    model, MODEL_STATUS,
    predecir_con_modelo,
    predecir_heuristico
)
from app.schemas.prediction import DatosEstudiante, ResultadoPrediccion

MODEL_VERSION = "v2.1.0"


def _construir_warnings(prob: float, datos: DatosEstudiante) -> list:
    warnings = []
    if MODEL_STATUS == "no cargado":
        warnings.append("Modelo ML no disponible — resultado calculado con reglas heurísticas.")
    if prob > 0.65:
        warnings.append("Riesgo alto de deserción detectado — se recomienda intervención inmediata.")
    if datos.dias_sin_ingresar > 7:
        warnings.append(f"El estudiante lleva {datos.dias_sin_ingresar} días sin ingresar.")
    if datos.calificacion_promedio < 50:
        warnings.append("Calificación promedio por debajo del 50% — considerar refuerzo académico.")
    return warnings


def ejecutar_prediccion(datos: DatosEstudiante, usar_modelo: bool = True) -> ResultadoPrediccion:
    datos_dict = {
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

    if usar_modelo and model is not None:
        prob = predecir_con_modelo(datos_dict)
        mv   = MODEL_VERSION
    else:
        prob = predecir_heuristico(datos_dict)
        mv   = f"{MODEL_VERSION}-heuristic"

    nivel_riesgo = "bajo" if prob < 0.40 else "medio" if prob < 0.65 else "alto"

    return ResultadoPrediccion(
        result        = "Riesgo de abandono" if prob >= 0.5 else "Comprometido",
        confidence    = round(prob, 4),
        model_version = mv,
        warnings      = _construir_warnings(prob, datos),
        request_id    = str(uuid.uuid4()),
        usuario_id            = datos.usuario_id,
        prob_abandono         = round(prob, 4),
        prob_abandono_pct     = f"{prob * 100:.1f}%",
        activar_modo_refuerzo = prob > 0.65,
        nivel_riesgo          = nivel_riesgo,
        timestamp             = datetime.now(timezone.utc).isoformat()
    )