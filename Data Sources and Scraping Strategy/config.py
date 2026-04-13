# ========================================
# CONFIGURACIÓN DEL PROYECTO E14-CHALLENGE
# ========================================
# Aquí guardamos TODA la configuración del scraper
# (URLs, tokens, rutas, etc.)
# Esto hace que el código sea más limpio y fácil de cambiar

import os
from pathlib import Path

# ========== RUTAS ==========
# Path.home() = la carpeta del usuario (ej: C:\Users\140jo)
# Creamos carpetas donde guardaremos los PDFs descargados

BASE_DIR = Path(__file__).parent  # Carpeta del proyecto actual
OUTPUT_DIR = BASE_DIR / "pdfs_descargados"  # Carpeta donde irán los PDFs

# Crear la carpeta si no existe
OUTPUT_DIR.mkdir(exist_ok=True)

# ========== URL Y ENDPOINTS ==========
# El servidor de la Registraduría está aquí:

BASE_URL = "https://e14_pres1v_2022.registraduria.gov.co"  # URL base del servidor
DESCARGA_ENDPOINT = "/descargae14"  # El "camino" específico para descargar

# Construir URL completa
DESCARGA_URL = BASE_URL + DESCARGA_ENDPOINT
print(f"URL de descarga: {DESCARGA_URL}")

# ========== TOKEN DE AUTENTICACIÓN ==========
# Este token es como tu contraseña para acceder a los PDFs
# IMPORTANTE: En producción, NUNCA guardes tokens en el código
# Usa variables de entorno (.env) en su lugar

TOKEN_REGISTRO_PRESIDENCIAL = "84a6J7jvUm+sKzlTVgLB98kt+a2Maam82/8eieWRSPlYd5mJlVtwlXEB/DJsSSo/llyyLteJwHgw3f8/QcLGLtY020BJEvHWX7wW/VNwsSk="

# ========== OPCIONES DE CONEXIÓN ==========
# Configuraciones para las peticiones HTTP

TIMEOUT = 30  # Máximo tiempo en segundos para esperar respuesta (30 = bastante tiempo)
VERIFY_SSL = False  # No verificar certificado SSL (solo para desarrollo)
