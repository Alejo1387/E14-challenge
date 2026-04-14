"""
config.py - Configuración Global del Proyecto E14 Challenge

Este archivo define todas las rutas y configuraciones que usará el proyecto.
Otros archivos lo importan para saber dónde guardar cosas.

Analogía: Es como el "carnet de identidad" del proyecto.
"""

from pathlib import Path

# ============================================================================
# 1. RAÍZ DEL PROYECTO
# ============================================================================

# Path() crea una ruta que funciona en Windows, Mac y Linux
# __file__ = "dónde está este archivo (config.py)"
# .parent = la carpeta padre (backend/)
BASE_DIR = Path(__file__).parent

print(f"DEBUG: BASE_DIR = {BASE_DIR}")

# ============================================================================
# 2. RUTAS DE DATOS
# ============================================================================

# Carpeta donde Persona A descarga los PDFs
DATA_RAW_DIR = BASE_DIR / "data" / "raw"

# Carpeta donde irán datos procesados después
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Carpeta general de datos
DATA_DIR = BASE_DIR / "data"

# ============================================================================
# 3. BASE DE DATOS
# ============================================================================

# Ubicación del archivo SQLite (la BD)
# Usamos SQLite durante desarrollo, PostgreSQL en producción
DATABASE_PATH = DATA_DIR / "e14_challenge.db"

# URL para conectar a SQLite
# Formato: "sqlite:////ruta/absoluta/archivo.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ============================================================================
# 4. ELECCIÓN (election_id)
# ============================================================================

# Identificador de la elección que estamos procesando
# Ejemplo: "PRES_1V_2022" = Presidencial, 1er vuelta, 2022
ELECTION_ID = "PRES_1V_2022"

# Año de la elección
ELECTION_YEAR = 2022

# ============================================================================
# 5. CONFIGURACIÓN DE ALMACENAMIENTO
# ============================================================================

# Estructura de carpetas para organizar PDFs
# Formato: {dept_code}_{dept_name}/{muni_code}_{muni_name}/
STORAGE_STRUCTURE = "{dept_code}_{dept_name}/{muni_code}_{muni_name}"

# ============================================================================
# 6. CONFIGURACIÓN DE VALIDACIÓN
# ============================================================================

# Tamaño máximo de un PDF (en bytes)
# 10 MB = 10485760 bytes
MAX_PDF_SIZE = 10 * 1024 * 1024

# Extensiones permitidas de archivo
ALLOWED_EXTENSIONS = {".pdf"}

# ============================================================================
# 7. CONFIGURACIÓN DE LOGGING
# ============================================================================

# Nivel de log (DEBUG = muestra todo, INFO = info importante, ERROR = solo errores)
LOG_LEVEL = "DEBUG"

# Carpeta donde guardar logs
LOGS_DIR = BASE_DIR / "logs"

# ============================================================================
# 8. CREAR CARPETAS SI NO EXISTEN
# ============================================================================

def create_directories():
    """
    Crea todas las carpetas necesarias si no existen.
    
    ¿Por qué? Para que no falle cuando intentes guardar un PDF
    si la carpeta no existe.
    """
    for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Carpeta lista: {directory}")

# Ejecutar cuando alguien importe este archivo
create_directories()

# ============================================================================
# 9. INFORMACIÓN DE DEPURACIÓN
# ============================================================================

if __name__ == "__main__":
    """
    Este código solo se ejecuta si haces:
    python backend/config.py
    
    Sirve para verificar que todas las rutas están correctas.
    """
    print("\n" + "="*60)
    print("🔧 CONFIGURACIÓN DEL PROYECTO E14 CHALLENGE")
    print("="*60)
    print(f"Base Directory:     {BASE_DIR}")
    print(f"Data Raw:           {DATA_RAW_DIR}")
    print(f"Data Processed:     {DATA_PROCESSED_DIR}")
    print(f"Database:           {DATABASE_PATH}")
    print(f"Database URL:       {DATABASE_URL}")
    print(f"Election ID:        {ELECTION_ID}")
    print("="*60 + "\n")