# ============================================================
#  EduBot AI — API de Predicción de Deserción
#  Convierte el laboratorio ML en un servicio REST
#  Listo para deployar en Railway / Render
# ============================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import joblib
import os

# ── Inicializar app ─────────────────────────────────────────
app = FastAPI(
    title="EduBot AI — Predicción de Deserción",
    description="API que calcula la probabilidad de abandono (Pd) de un estudiante.",
    version="1.0.0"
)

# ── Cargar modelo y scaler al arrancar ──────────────────────
# (Estos archivos los exportas desde tu Colab con joblib.dump)
MODEL_PATH  = os.getenv("MODEL_PATH",  "modelo_edubot.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "scaler_edubot.pkl")
COLUMNS_PATH = os.getenv("COLUMNS_PATH", "columnas_entrenamiento.pkl")

try:
    model   = joblib.load(MODEL_PATH)
    scaler  = joblib.load(SCALER_PATH)
    X_cols  = joblib.load(COLUMNS_PATH)   # lista de columnas del entrenamiento
    print("✅ Modelo, scaler y columnas cargados correctamente.")
except FileNotFoundError as e:
    print(f"⚠️  Archivo no encontrado: {e}. Asegúrate de exportar los archivos desde Colab.")
    model, scaler, X_cols = None, None, None


# ── Schema de entrada ───────────────────────────────────────
class DatosEstudiante(BaseModel):
    usuario_id: str = Field(..., description="ID único del usuario en WhatsApp")
    sesiones_semana: int = Field(..., ge=0, le=7)
    quizzes_completados: int = Field(..., ge=0)
    quizzes_fallados: int = Field(..., ge=0)
    tiempo_por_leccion: float = Field(..., ge=0, description="Minutos promedio por lección")
    dias_sin_ingresar: int = Field(..., ge=0)
    modulos_completados: int = Field(..., ge=0)
    porcentaje_progreso: float = Field(..., ge=0, le=100)
    mensajes_enviados: int = Field(..., ge=0)
    calificacion_promedio: float = Field(..., ge=0, le=100)
    nivel: str = Field(..., pattern="^(basico|intermedio|avanzado)$")
    dispositivo: str = Field(..., pattern="^(movil|desktop|tablet)$")


# ── Schema de salida ────────────────────────────────────────
class ResultadoPrediccion(BaseModel):
    usuario_id: str
    prob_abandono: float        # 0.0 - 1.0
    prob_abandono_pct: str      # "72.3%"
    prediccion: str             # "Comprometido" | "Riesgo de abandono"
    activar_modo_refuerzo: bool # True si Pd > 0.65
    confianza: str              # "84.1%"
    nivel_riesgo: str           # "bajo" | "medio" | "alto"


# ── Endpoint principal ──────────────────────────────────────
@app.post("/predecir", response_model=ResultadoPrediccion)
def predecir(datos: DatosEstudiante):
    """
    Recibe los datos de comportamiento de un estudiante
    y devuelve la probabilidad de que abandone el curso (Pd).
    n8n llama este endpoint después de cada lección/quiz.
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Modelo no cargado. Exporta el modelo desde Colab primero."
        )

    # Construir DataFrame igual que en el entrenamiento
    entrada = {
        'sesiones_semana'      : datos.sesiones_semana,
        'quizzes_completados'  : datos.quizzes_completados,
        'quizzes_fallados'     : datos.quizzes_fallados,
        'tiempo_por_leccion'   : datos.tiempo_por_leccion,
        'dias_sin_ingresar'    : datos.dias_sin_ingresar,
        'modulos_completados'  : datos.modulos_completados,
        'porcentaje_progreso'  : datos.porcentaje_progreso,
        'mensajes_enviados'    : datos.mensajes_enviados,
        'calificacion_promedio': datos.calificacion_promedio,
        'nivel'                : datos.nivel,
        'dispositivo'          : datos.dispositivo,
    }

    df_nuevo = pd.DataFrame([entrada])

    # One-Hot Encoding igual que en entrenamiento
    df_nuevo = pd.get_dummies(df_nuevo, columns=['nivel', 'dispositivo'])

    # Agregar columnas faltantes con 0
    for col in X_cols:
        if col not in df_nuevo.columns:
            df_nuevo[col] = 0

    # Mismo orden de columnas
    df_nuevo = df_nuevo[X_cols]

    # Escalar y predecir
    datos_scaled = scaler.transform(df_nuevo)
    prob = float(model.predict_proba(datos_scaled)[0][1])  # prob de clase 1 (abandono)

    # Determinar nivel de riesgo
    if prob < 0.40:
        nivel_riesgo = "bajo"
    elif prob < 0.65:
        nivel_riesgo = "medio"
    else:
        nivel_riesgo = "alto"

    return ResultadoPrediccion(
        usuario_id             = datos.usuario_id,
        prob_abandono          = round(prob, 4),
        prob_abandono_pct      = f"{prob * 100:.1f}%",
        prediccion             = "Riesgo de abandono" if prob >= 0.5 else "Comprometido",
        activar_modo_refuerzo  = prob > 0.65,   # ← El umbral del anteproyecto
        confianza              = f"{max(prob, 1 - prob) * 100:.1f}%",
        nivel_riesgo           = nivel_riesgo,
    )


# ── Endpoint de salud (para Railway/Render) ─────────────────
@app.get("/health")
def health():
    return {
        "status" : "ok",
        "modelo" : "cargado" if model else "no cargado"
    }


# ── Endpoint de prueba (sin modelo real) ────────────────────
@app.post("/predecir/demo")
def predecir_demo(datos: DatosEstudiante):
    """
    Demo sin modelo real — calcula Pd con reglas simples.
    Úsalo mientras entrenas el modelo con datos reales.
    """
    # Regla heurística basada en las variables más importantes
    score = 0.0
    score += max(0, (7 - datos.sesiones_semana) / 7) * 0.25
    score += min(datos.dias_sin_ingresar / 10, 1.0) * 0.30
    tasa_fallo = datos.quizzes_fallados / max(datos.quizzes_completados + datos.quizzes_fallados, 1)
    score += tasa_fallo * 0.20
    score += max(0, (50 - datos.calificacion_promedio) / 50) * 0.15
    score += max(0, (50 - datos.porcentaje_progreso) / 100) * 0.10

    prob = round(min(score, 0.99), 4)

    if prob < 0.40:
        nivel_riesgo = "bajo"
    elif prob < 0.65:
        nivel_riesgo = "medio"
    else:
        nivel_riesgo = "alto"

    return {
        "usuario_id"            : datos.usuario_id,
        "prob_abandono"         : prob,
        "prob_abandono_pct"     : f"{prob * 100:.1f}%",
        "prediccion"            : "Riesgo de abandono" if prob >= 0.5 else "Comprometido",
        "activar_modo_refuerzo" : prob > 0.65,
        "nivel_riesgo"          : nivel_riesgo,
        "nota"                  : "⚠️ Modo demo — reemplazar con modelo ML real"
    }
