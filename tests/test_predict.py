# ============================================================
#  EduBot AI — Tests básicos
#  Pruebas unitarias para la Semana 3 (CI/CD)
#  Ejecutar con: pytest tests/
# ============================================================

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

HEADERS_VALIDOS = {"X-API-Key": "edubot-dev-key-2026"}

PAYLOAD_VALIDO = {
    "usuario_id": "test123",
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


def test_health():
    """El servicio debe responder ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metadata():
    """El endpoint /metadata debe devolver el nombre de la API."""
    r = client.get("/metadata")
    assert r.status_code == 200
    assert "EduBot" in r.json()["nombre"]


def test_predict_sin_api_key():
    """Sin API Key debe devolver 401."""
    r = client.post("/predict", json=PAYLOAD_VALIDO)
    assert r.status_code == 401


def test_predict_api_key_incorrecta():
    """Con API Key incorrecta debe devolver 403."""
    r = client.post("/predict", json=PAYLOAD_VALIDO, headers={"X-API-Key": "incorrecta"})
    assert r.status_code == 403


def test_predict_datos_faltantes():
    """Con campos faltantes debe devolver 422."""
    r = client.post("/predict", json={"usuario_id": "test"}, headers=HEADERS_VALIDOS)
    assert r.status_code == 422


def test_predict_demo_correcto():
    """Con datos válidos el demo debe devolver 200 con activar_modo_refuerzo."""
    r = client.post("/predict/demo", json=PAYLOAD_VALIDO, headers=HEADERS_VALIDOS)
    assert r.status_code == 200
    data = r.json()
    assert "activar_modo_refuerzo" in data
    assert "result" in data
    assert "confidence" in data
    assert "warnings" in data
    assert "request_id" in data
