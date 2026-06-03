"""
main.py - Servidor FastAPI para E14 Challenge

Endpoints:
  - POST /upload-pdf - Subir un PDF
  - GET /pdfs - Listar PDFs registrados
  - GET /pdfs/{form_id} - Obtener info de un PDF
  - GET / - Raíz (html o status)
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import hashlib
from typing import Optional
from datetime import datetime

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_RAW_DIR, BASE_DIR, ELECTION_ID, DATABASE_URL
from src.storage.local_storage import LocalStorageManager
from src.database.crud import crear_formulario, resolver_voting_table, asegurar_eleccion
from src.utils.hashing import calcular_sha256
from src.database.schema import create_engine_connection
from sqlalchemy.orm import sessionmaker

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

app = FastAPI(
    title="E14 Challenge API",
    description="API para gestionar formularios E-14 de auditoría electoral",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Storage manager
storage_manager = LocalStorageManager(DATA_RAW_DIR)

# DB
engine = create_engine_connection(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# ============================================================================
# HELPERS
# ============================================================================

def get_db_session():
    """Obtener sesión de BD."""
    return SessionLocal()


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Raíz - Servir página de upload."""
    upload_html = Path(__file__).parent / "static" / "upload.html"
    if upload_html.exists():
        return upload_html.read_text()
    
    # Fallback si no existe upload.html
    return """
    <!DOCTYPE html>
    <html>
    <head><title>E14 Challenge API</title></head>
    <body>
        <h1>E14 Challenge API</h1>
        <p>API activo. Documentación: <a href="/docs">/docs</a></p>
    </body>
    </html>
    """


@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    dept_code: str = Form(...),
    muni_code: str = Form(...),
    zone_code: str = Form(...),
    station_code: str = Form(...),
    table_number: str = Form(...),
):
    """
    Subir un PDF de formulario E-14.
    
    Args:
        file: Archivo PDF
        dept_code: Código de departamento (ej: "01")
        muni_code: Código de municipio (ej: "001")
        zone_code: Código de zona (ej: "001")
        station_code: Código de puesto (ej: "01")
        table_number: Número de mesa (ej: "001")
    
    Returns:
        {"success": bool, "message": str, "form_id": int, "details": dict}
    """
    
    try:
        # Leer contenido del archivo
        contents = await file.read()
        
        if not contents.startswith(b"%PDF"):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Archivo no es un PDF válido (no empieza con %PDF)",
                    "error": "INVALID_PDF_FORMAT"
                }
            )
        
        if len(contents) > 10 * 1024 * 1024:  # 10 MB
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"PDF muy grande: {len(contents)} bytes > 10 MB",
                    "error": "PDF_TOO_LARGE"
                }
            )
        
        # Guardar PDF en disco
        ruta_pdf, hash_sha256 = storage_manager.guardar_pdf(
            contenido=contents,
            dept_code=dept_code,
            muni_code=muni_code,
            zone_code=zone_code,
            station_code=station_code,
            table_number=table_number,
        )
        
        # Generar form_serial
        from src.storage.pdf_paths import generar_form_serial
        form_serial = generar_form_serial(
            dept_code, muni_code, zone_code, station_code, table_number
        )
        
        # Asegurar elección en BD
        asegurar_eleccion(ELECTION_ID)
        
        # Resolver mesa de votación
        mesa = resolver_voting_table(
            department_code=dept_code,
            municipality_code=muni_code,
            zone_number=zone_code,
            station_number=station_code,
            table_number=table_number,
        )
        
        if not mesa:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "No se encontró la mesa de votación. Verifica los códigos.",
                    "error": "VOTING_TABLE_NOT_FOUND",
                    "provided": {
                        "dept": dept_code,
                        "muni": muni_code,
                        "zone": zone_code,
                        "station": station_code,
                        "table": table_number,
                    }
                }
            )
        
        voting_table_id = mesa["id"]
        ruta_relativa = str(ruta_pdf.relative_to(BASE_DIR))
        
        # Registrar en BD
        form_id = crear_formulario(
            form_serial=form_serial,
            election_id=ELECTION_ID,
            department_code=dept_code,
            municipality_code=muni_code,
            voting_table_id=voting_table_id,
            local_path=ruta_relativa,
            file_hash=hash_sha256,
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "PDF subido y registrado exitosamente",
                "form_id": form_id,
                "details": {
                    "form_serial": form_serial,
                    "file_path": str(ruta_pdf),
                    "file_hash": hash_sha256,
                    "file_size_bytes": len(contents),
                    "file_size_mb": round(len(contents) / (1024 * 1024), 2),
                    "voting_table_id": voting_table_id,
                    "uploaded_at": datetime.now().isoformat(),
                }
            }
        )
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"Error de validación: {str(e)}",
                "error": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error interno: {str(e)}",
                "error": "INTERNAL_ERROR"
            }
        )


@app.get("/pdfs")
async def list_pdfs():
    """Listar PDFs registrados en la BD."""
    try:
        session = get_db_session()
        from src.database.schema import Form
        
        forms = session.query(Form).all()
        
        result = {
            "total": len(forms),
            "forms": [
                {
                    "id": f.id,
                    "form_serial": f.form_serial,
                    "department": f.department_code,
                    "municipality": f.municipality_code,
                    "local_path": f.local_path,
                    "file_hash": f.file_hash,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in forms
            ]
        }
        
        session.close()
        return JSONResponse(content=result)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "election_id": ELECTION_ID,
        "database": "sqlite",
        "raw_data_dir": str(DATA_RAW_DIR)
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 80)
    print("🚀 INICIANDO SERVIDOR FASTAPI E14 CHALLENGE")
    print("=" * 80)
    print(f"📍 Dirección: http://127.0.0.1:8000")
    print(f"📚 Documentación: http://127.0.0.1:8000/docs")
    print(f"📊 Base de datos: {DATABASE_URL}")
    print("=" * 80 + "\n")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
