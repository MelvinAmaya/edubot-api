# ============================================================
#  EduBot AI — Schemas (contratos de entrada y salida)
# ============================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List


class DatosEstudiante(BaseModel):
    """
    Contrato de ENTRADA.
    Todos los campos son obligatorios.
    """
    model_config = ConfigDict(extra="forbid", json_schema_extra={
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
    })

    usuario_id: str = Field(
        ..., min_length=1, max_length=50,
        description="ID único del usuario (ID de Telegram, no datos personales)"
    )
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
    nivel: str = Field(
        ..., pattern="^(basico|intermedio|avanzado)$",
        description="Nivel del estudiante: 'basico', 'intermedio' o 'avanzado'"
    )
    dispositivo: str = Field(
        ..., pattern="^(movil|desktop|tablet)$",
        description="Dispositivo usado: 'movil', 'desktop' o 'tablet'"
    )

    @field_validator("usuario_id")
    @classmethod
    def usuario_id_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El usuario_id no puede ser un texto vacío o solo espacios.")
        return v.strip()

    @field_validator("porcentaje_progreso", "calificacion_promedio")
    @classmethod
    def redondear_decimales(cls, v):
        return round(v, 2)


class ResultadoPrediccion(BaseModel):
    """
    Contrato de SALIDA — estándar Módulo 4 Semana 2.
    """
    result: str
    confidence: float
    model_version: str
    warnings: List[str]
    request_id: str
    usuario_id: str
    prob_abandono: float
    prob_abandono_pct: str
    activar_modo_refuerzo: bool
    nivel_riesgo: str
    timestamp: str