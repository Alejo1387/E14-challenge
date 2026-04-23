"""
register_downloaded_pdfs.py - Registrar PDFs Descargados por Persona A

Este script es el PUENTE entre Persona A y TÚ.

¿Cuándo lo usas?
    Después de que Persona A descargue PDFs, ejecutas esto para registrarlos.

¿Qué hace?
    1. Lee los archivos JSON que Persona A genera (metadata de descargas)
    2. Verifica que los PDFs existen y no están dañados
    3. Calcula el hash SHA-256 de cada uno
    4. Registra cada PDF en la BD con estado PENDING
    5. Reporta resultados

¿Cómo ejecutar?
    cd backend
    python scripts/register_downloaded_pdfs.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Importar
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_RAW_DIR, ELECTION_ID
from src.database.crud import crear_formulario
from src.database.queries import obtener_mesa, obtener_municipio
from src.utils.hashing import calcular_sha256
from src.storage.local_storage import LocalStorageManager, obtener_ruta_pdf

# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class RegistradorPDFs:
    """
    Gestiona el registro de PDFs descargados en la BD.
    
    Workflow:
        1. Detecta PDFs nuevos en data/raw/
        2. Verifica integridad (calcula hash)
        3. Los registra en la BD
        4. Reporta resultados
    """
    
    def __init__(self):
        """Inicializa el registrador"""
        self.storage_manager = LocalStorageManager()
        self.stats = {
            "total_encontrados": 0,
            "registrados": 0,
            "ya_existentes": 0,
            "errores": 0,
            "detalles_errores": []
        }
    
    # ========================================================================
    # MÉTODO 1: Detectar PDFs nuevos
    # ========================================================================
    
    def detectar_pdfs_nuevos(self) -> list:
        """
        Detecta todos los PDFs en data/raw/ que NO estén registrados aún.
        
        Returns:
            list: Lista de rutas a PDFs nuevos
        """
        
        print("🔍 Buscando PDFs nuevos en data/raw/...\n")
        
        # Obtener todos los PDFs
        todos_pdfs = self.storage_manager.listar_pdfs()
        
        print(f"   Total de PDFs encontrados: {len(todos_pdfs)}\n")
        
        return todos_pdfs
    
    # ========================================================================
    # MÉTODO 2: Extraer información de la ruta
    # ========================================================================
    
    def extraer_info_de_ruta(self, ruta_pdf: Path) -> dict:
        """
        Extrae información de la ruta de un PDF.
        
        Estructura esperada:
        backend/data/raw/{dept_code}_{dept_name}/{muni_code}_{muni_name}/{form_serial}.pdf
        
        Ejemplo:
        backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf
        
        Args:
            ruta_pdf: Ruta del PDF
        
        Returns:
            dict con: dept_code, dept_name, muni_code, muni_name, form_serial
        """
        
        try:
            # Partes de la ruta
            partes = ruta_pdf.parts
            
            # Obtener: dept_dept, muni_muni, form_serial
            # Ejemplo: ['backend', 'data', 'raw', '05_Antioquia', '001_Medellin', '5036317.pdf']
            
            # El nombre del archivo (sin extensión) es el form_serial
            form_serial = ruta_pdf.stem  # "5036317"
            
            # Las carpetas padre
            muni_folder = ruta_pdf.parent.name  # "001_Medellin"
            dept_folder = ruta_pdf.parent.parent.name  # "05_Antioquia"
            
            # Parsear carpetas
            # Formato: "05_Antioquia"
            dept_partes = dept_folder.split("_", 1)
            dept_code = dept_partes[0]
            dept_name = dept_partes[1] if len(dept_partes) > 1 else "Desconocido"
            
            # Formato: "001_Medellin"
            muni_partes = muni_folder.split("_", 1)
            muni_code = muni_partes[0]
            muni_name = muni_partes[1] if len(muni_partes) > 1 else "Desconocido"
            
            return {
                "form_serial": form_serial,
                "dept_code": dept_code,
                "dept_name": dept_name,
                "muni_code": muni_code,
                "muni_name": muni_name,
                "ruta_completa": str(ruta_pdf)
            }
        
        except Exception as e:
            print(f"   ❌ Error extrayendo info de ruta {ruta_pdf}: {e}")
            return None
    
    # ========================================================================
    # MÉTODO 3: Validar PDF
    # ========================================================================
    
    def validar_pdf(self, ruta_pdf: Path) -> tuple:
        """
        Valida que el PDF existe y es válido.
        
        Returns:
            Tuple: (es_válido, mensaje_error)
        """
        
        # ¿Existe?
        if not ruta_pdf.exists():
            return False, "Archivo no existe"
        
        # ¿Es un archivo?
        if not ruta_pdf.is_file():
            return False, "No es un archivo"
        
        # ¿Empieza con %PDF?
        try:
            with open(ruta_pdf, "rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    return False, "No es un PDF válido"
        except Exception as e:
            return False, f"Error leyendo archivo: {e}"
        
        return True, None
    
    # ========================================================================
    # MÉTODO 4: Registrar un PDF
    # ========================================================================
    
    def registrar_pdf(self, info: dict) -> bool:
        """
        Registra un PDF en la BD.
        
        Args:
            info: Diccionario con info del PDF (de extraer_info_de_ruta)
        
        Returns:
            bool: True si se registró, False si error
        """
        
        form_serial = info["form_serial"]
        dept_code = info["dept_code"]
        muni_code = info["muni_code"]
        ruta_completa = Path(info["ruta_completa"])
        
        try:
            # PASO 1: Validar que exista y sea válido
            es_valido, error_msg = self.validar_pdf(ruta_completa)
            if not es_valido:
                self.stats["errores"] += 1
                self.stats["detalles_errores"].append({
                    "form_serial": form_serial,
                    "error": error_msg
                })
                print(f"   ❌ {form_serial}: {error_msg}")
                return False
            
            # PASO 2: Calcular hash
            hash_sha256 = calcular_sha256(ruta_completa)
            
            # PASO 3: Obtener ID de la mesa
            # Problema: No sabemos a cuál mesa corresponde este PDF
            # Por ahora, usamos la mesa 1 como default
            # (Persona A debe darnos esta información)
            voting_table_id = 1  # ⚠️ ESTO DEBE VENIR DE PERSONA A
            
            # PASO 4: Registrar en BD
            form_id = crear_formulario(
                form_serial=form_serial,
                election_id=ELECTION_ID,
                department_code=dept_code,
                municipality_code=muni_code,
                voting_table_id=voting_table_id,
                local_path=str(ruta_completa),
                file_hash=hash_sha256
            )
            
            if form_id:
                self.stats["registrados"] += 1
                print(f"   ✅ {form_serial}: Registrado (ID: {form_id})")
                return True
            else:
                self.stats["errores"] += 1
                self.stats["detalles_errores"].append({
                    "form_serial": form_serial,
                    "error": "Ya existe en la BD"
                })
                self.stats["ya_existentes"] += 1
                return False
        
        except Exception as e:
            self.stats["errores"] += 1
            self.stats["detalles_errores"].append({
                "form_serial": form_serial,
                "error": str(e)
            })
            print(f"   ❌ {form_serial}: Error: {e}")
            return False
    
    # ========================================================================
    # MÉTODO 5: Ejecutar el registro completo
    # ========================================================================
    
    def ejecutar(self) -> dict:
        """
        Ejecuta el proceso completo de registro.
        
        Returns:
            dict: Estadísticas del proceso
        """
        
        print("\n" + "="*70)
        print("📝 REGISTRANDO PDFs DESCARGADOS")
        print("="*70 + "\n")
        
        # PASO 1: Detectar PDFs
        pdfs = self.detectar_pdfs_nuevos()
        self.stats["total_encontrados"] = len(pdfs)
        
        if len(pdfs) == 0:
            print("✅ No hay PDFs nuevos para registrar\n")
            return self.stats
        
        # PASO 2: Registrar cada uno
        print("📥 Registrando PDFs...\n")
        
        for i, ruta_pdf in enumerate(pdfs, 1):
            # Extraer información
            info = self.extraer_info_de_ruta(ruta_pdf)
            
            if not info:
                self.stats["errores"] += 1
                continue
            
            # Registrar
            self.registrar_pdf(info)
        
        # PASO 3: Mostrar resumen
        self.mostrar_resumen()
        
        return self.stats
    
    # ========================================================================
    # MÉTODO 6: Mostrar resumen
    # ========================================================================
    
    def mostrar_resumen(self):
        """Muestra un resumen de lo que pasó"""
        
        print("\n" + "="*70)
        print("📊 RESUMEN")
        print("="*70 + "\n")
        
        print(f"Total encontrados:      {self.stats['total_encontrados']}")
        print(f"Registrados exitosamente: {self.stats['registrados']}")
        print(f"Ya existentes:          {self.stats['ya_existentes']}")
        print(f"Errores:                {self.stats['errores']}")
        print()
        
        if self.stats["detalles_errores"]:
            print("Errores detectados:")
            for error in self.stats["detalles_errores"]:
                print(f"  • {error['form_serial']}: {error['error']}")
            print()
        
        print("="*70 + "\n")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Ejecuta el script"""
    
    registrador = RegistradorPDFs()
    stats = registrador.ejecutar()
    
    # Salir con código de error si hay problemas
    return 0 if stats["errores"] == 0 else 1


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)