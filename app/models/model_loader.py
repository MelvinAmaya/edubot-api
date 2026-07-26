# ============================================================
#  EduBot AI — Capa Model
#  Carga los artefactos del modelo ML y expone las
#  funciones de inferencia (ML y heurística).
# ============================================================

import joblib
import pandas as pd
import os

# ── Rutas de los artefactos ─────────────────────────────────
MODEL_PATH   = os.getenv("MODEL_PATH",   "modelo_edubot.pkl")
SCALER_PATH  = os.getenv("SCALER_PATH",  "scaler_edubot.pkl")
COLUMNS_PATH = os.getenv("COLUMNS_PATH", "columnas_entrenamiento.pkl")

# ── Carga al arrancar el servidor ───────────────────────────
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


def predecir_con_modelo(datos: dict) -> float:
    """
    Inferencia con el modelo de Regresión Logística real.
    Aplica el mismo preprocesamiento del entrenamiento:
      1. DataFrame desde el dict de entrada
      2. One-Hot Encoding de variables categóricas
      3. Rellenar columnas faltantes con 0
      4. Reordenar columnas igual que en el entrenamiento
      5. Normalizar con el scaler guardado
      6. Predecir probabilidad de abandono (clase 1)
    """
    df = pd.DataFrame([datos])
    df = pd.get_dummies(df, columns=["nivel", "dispositivo"])
    for col in X_cols:
        if col not in df.columns:
            df[col] = 0
    df = df[X_cols]
    datos_scaled = scaler.transform(df)
    return float(model.predict_proba(datos_scaled)[0][1])


def predecir_heuristico(datos: dict) -> float:
    """
    Inferencia con reglas heurísticas ponderadas.
    No requiere archivos .pkl.
    Usado cuando el modelo ML no está disponible.
    """
    score = 0.0
    score += max(0, (7 - datos["sesiones_semana"]) / 7) * 0.25
    score += min(datos["dias_sin_ingresar"] / 10, 1.0) * 0.30
    total_q = datos["quizzes_completados"] + datos["quizzes_fallados"]
    tasa_fallo = datos["quizzes_fallados"] / max(total_q, 1)
    score += tasa_fallo * 0.20
    score += max(0, (50 - datos["calificacion_promedio"]) / 50) * 0.15
    score += max(0, (50 - datos["porcentaje_progreso"]) / 100) * 0.10
    return round(min(score, 0.99), 4)
