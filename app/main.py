# ============================================================
#  EduBot AI — Punto de entrada principal
#  Arranca la aplicación FastAPI y registra las rutas.
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone

from app.api.routes import router   # ← MODEL_STATUS eliminado de aquí

API_VERSION  = "2.1.0"
API_NAME     = "EduBot AI — API de Predicción de Deserción"
STARTUP_TIME = datetime.now(timezone.utc).isoformat()

app = FastAPI(
    title=API_NAME,
    description="API estandarizada que calcula la probabilidad de abandono (Pd) de un estudiante de EduBot AI.",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = []
    for error in exc.errors():
        campo = " → ".join(str(e) for e in error["loc"] if e != "body")
        tipo  = error["type"]
        msg   = error["msg"]

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

app.include_router(router)