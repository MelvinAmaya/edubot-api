# ============================================================
#  conftest.py — Configuración de pytest
#  Le dice a pytest dónde está la raíz del proyecto
#  para que pueda importar los módulos correctamente.
# ============================================================

import sys
import os

# Agregar la raíz del proyecto al path de Python
sys.path.insert(0, os.path.dirname(__file__))
