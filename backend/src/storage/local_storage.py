"""
local_storage.py - Gestionar almacenamiento de PDFs en el disco local

Este módulo se encarga de:
1. Guardar PDFs en las carpetas correctas
2. Leer PDFs cuando se necesitan
3. Verificar integridad (hash)
4. Crear carpetas automáticamente

Analogía: Es el "bibliotecario" que organiza los libros (PDFs) en las estanterías.
"""

from pathlib import Path
from typing import Optional, Tuple
import shutil
import sys

# Importar nuestros módulos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import (
    DATA_RAW_DIR,
    STORAGE_STRUCTURE,
    MAX_PDF_SIZE,
    ALLOWED_EXTENSIONS,
)
from src.utils.hashing import calcular_sha256, es_hash_valido

# ============================================================================
# CLASE PRINCIPAL: LocalStorageManager
# ============================================================================

class LocalStorageManager:
    """
    Gestiona el almacenamiento de PDFs en el disco local.
    
    Ejemplo de uso:
        manager = LocalStorageManager()
        
        # Guardar un PDF
        ruta = manager.guardar_pdf(
            contenido_bytes=pdf_bytes,
            dept_code="05",
            dept_name="Antioquia",
            muni_code="001",
            muni_name="Medellin",
            form_serial="5036317"
        )
        
        # Verificar integridad
        hash_esperado = calcular_sha256(ruta)
        print(hash_esperado)
    """
    
    def __init__(self, base_dir: Path = DATA_RAW_DIR):
        """
        Inicializa el gestor de almacenamiento.
        
        Args:
            base_dir: Carpeta base donde guardar PDFs (default: backend/data/raw/)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # MÉTODO 1: Construir ruta de un PDF
    # ========================================================================
    
    def _construir_ruta(
        self,
        dept_code: str,
        dept_name: str,
        muni_code: str,
        muni_name: str,
        form_serial: str
    ) -> Path:
        """
        Construye la ruta completa donde guardar un PDF.
        
        Usa el patrón definido en config.STORAGE_STRUCTURE.
        
        Args:
            dept_code: Código del departamento (ej: "05")
            dept_name: Nombre del departamento (ej: "Antioquia")
            muni_code: Código del municipio (ej: "001")
            muni_name: Nombre del municipio (ej: "Medellin")
            form_serial: Número único del formulario (ej: "5036317")
        
        Returns:
            Path: Ruta completa (ej: "backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf")
        
        Ejemplo:
            >>> manager = LocalStorageManager()
            >>> ruta = manager._construir_ruta("05", "Antioquia", "001", "Medellin", "5036317")
            >>> print(ruta)
            Path('backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf')
        """
        
        # Usar el patrón de STORAGE_STRUCTURE para crear carpetas
        folder_pattern = STORAGE_STRUCTURE.format(
            dept_code=dept_code,
            dept_name=dept_name,
            muni_code=muni_code,
            muni_name=muni_name
        )
        
        # Combinar: base_dir / patrón / nombre_archivo
        ruta_completa = self.base_dir / folder_pattern / f"{form_serial}.pdf"
        
        return ruta_completa
    
    # ========================================================================
    # MÉTODO 2: Crear carpetas si no existen
    # ========================================================================
    
    def _crear_carpetas(self, ruta: Path) -> None:
        """
        Crea las carpetas necesarias si no existen.
        
        Args:
            ruta: La ruta completa del archivo (se extraen las carpetas)
        
        Ejemplo:
            >>> manager = LocalStorageManager()
            >>> ruta = Path("backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf")
            >>> manager._crear_carpetas(ruta)
            # Crea: backend/data/raw/05_Antioquia/001_Medellin/
        """
        # .parent = la carpeta que contiene el archivo
        carpeta = ruta.parent
        carpeta.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # MÉTODO 3: Validar un PDF
    # ========================================================================
    
    def _validar_pdf(self, contenido: bytes, ruta: Path) -> Tuple[bool, Optional[str]]:
        """
        Valida que el contenido es un PDF válido.
        
        Comprobaciones:
        1. ¿Empieza con "%PDF"?
        2. ¿El tamaño está dentro del límite?
        
        Args:
            contenido: Bytes del archivo
            ruta: Dónde se guardará (para el mensaje de error)
        
        Returns:
            Tuple: (es_válido, mensaje_error)
            - Si es válido: (True, None)
            - Si es inválido: (False, "Razón del error")
        
        Ejemplo:
            >>> es_válido, error = manager._validar_pdf(pdf_bytes, ruta)
            >>> if es_válido:
            ...     print("PDF correcto")
            ... else:
            ...     print(f"Error: {error}")
        """
        
        # Validación 1: ¿Empieza con "%PDF"?
        if not contenido.startswith(b"%PDF"):
            return False, "No es un PDF válido (no empieza con %PDF)"
        
        # Validación 2: ¿El tamaño está dentro del límite?
        tamaño_bytes = len(contenido)
        if tamaño_bytes > MAX_PDF_SIZE:
            return False, f"PDF muy grande: {tamaño_bytes} bytes > {MAX_PDF_SIZE} bytes"
        
        # Si pasó todas las validaciones
        return True, None
    
    # ========================================================================
    # MÉTODO 4: Guardar un PDF (LA FUNCIÓN PRINCIPAL)
    # ========================================================================
    
    def guardar_pdf(
        self,
        contenido: bytes,
        dept_code: str,
        dept_name: str,
        muni_code: str,
        muni_name: str,
        form_serial: str
    ) -> Tuple[Path, str]:
        """
        Guarda un PDF en el almacenamiento local.
        
        PASOS:
        1. Construir la ruta
        2. Validar el PDF
        3. Crear carpetas si no existen
        4. Guardar el archivo
        5. Calcular el hash
        
        Args:
            contenido: Bytes del PDF (contenido descargado)
            dept_code: Código del departamento
            dept_name: Nombre del departamento
            muni_code: Código del municipio
            muni_name: Nombre del municipio
            form_serial: Serial único del formulario
        
        Returns:
            Tuple: (ruta_del_archivo, hash_sha256)
        
        Raises:
            ValueError: Si el PDF es inválido
            IOError: Si hay error al guardar
        
        Ejemplo:
            >>> manager = LocalStorageManager()
            >>> contenido_pdf = descargar_pdf(...)  # bytes descargados
            >>> ruta, hash_valor = manager.guardar_pdf(
            ...     contenido=contenido_pdf,
            ...     dept_code="05",
            ...     dept_name="Antioquia",
            ...     muni_code="001",
            ...     muni_name="Medellin",
            ...     form_serial="5036317"
            ... )
            >>> print(f"Guardado en: {ruta}")
            >>> print(f"Hash: {hash_valor}")
        """
        
        # PASO 1: Construir la ruta
        ruta = self._construir_ruta(dept_code, dept_name, muni_code, muni_name, form_serial)
        
        # PASO 2: Validar el PDF
        es_valido, error_msg = self._validar_pdf(contenido, ruta)
        if not es_valido:
            raise ValueError(f"PDF inválido: {error_msg}")
        
        # PASO 3: Crear carpetas si no existen
        self._crear_carpetas(ruta)
        
        # PASO 4: Guardar el archivo
        try:
            with open(ruta, "wb") as archivo:  # "wb" = write binary (escribir en binario)
                archivo.write(contenido)
        except IOError as e:
            raise IOError(f"Error al guardar PDF: {e}")
        
        # PASO 5: Calcular el hash
        hash_sha256 = calcular_sha256(ruta)
        
        return ruta, hash_sha256
    
    # ========================================================================
    # MÉTODO 5: Leer un PDF
    # ========================================================================
    
    def leer_pdf(self, ruta: Path) -> bytes:
        """
        Lee un PDF del disco.
        
        Args:
            ruta: Ruta del PDF a leer
        
        Returns:
            bytes: Contenido del PDF
        
        Raises:
            FileNotFoundError: Si el archivo no existe
        
        Ejemplo:
            >>> manager = LocalStorageManager()
            >>> contenido = manager.leer_pdf("backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf")
            >>> print(len(contenido), "bytes")
        """
        
        ruta = Path(ruta)
        
        if not ruta.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
        
        with open(ruta, "rb") as archivo:
            return archivo.read()
    
    # ========================================================================
    # MÉTODO 6: Verificar integridad de un PDF
    # ========================================================================
    
    def verificar_integridad(self, ruta: Path, hash_esperado: str) -> bool:
        """
        Verifica que un PDF no se dañó comparando hashes.
        
        Args:
            ruta: Ruta del PDF
            hash_esperado: El hash que debería tener
        
        Returns:
            bool: True si el hash coincide, False si no
        
        Ejemplo:
            >>> manager = LocalStorageManager()
            >>> hash_original = "a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9..."
            >>> es_intacto = manager.verificar_integridad(
            ...     ruta="backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf",
            ...     hash_esperado=hash_original
            ... )
            >>> if es_intacto:
            ...     print("✅ PDF sin daños")
            ... else:
            ...     print("❌ PDF dañado o modificado")
        """
        
        hash_actual = calcular_sha256(ruta)
        return hash_actual == hash_esperado
    
    # ========================================================================
    # MÉTODO 7: Obtener lista de PDFs en una carpeta
    # ========================================================================
    
    def listar_pdfs(self, carpeta_relativa: str = "") -> list:
        """
        Lista todos los PDFs en una carpeta (y subcarpetas).
        
        Args:
            carpeta_relativa: Carpeta dentro de RAW_DATA_DIR (default: todas)
            
        Returns:
            list: Lista de rutas completas a PDFs
        
        Ejemplo:
            >>> manager = LocalStorageManager()
            >>> pdfs = manager.listar_pdfs("05_Antioquia/001_Medellin")
            >>> for pdf in pdfs:
            ...     print(pdf)
            # Imprime: backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf
            # etc...
        """
        
        if carpeta_relativa:
            carpeta = self.base_dir / carpeta_relativa
        else:
            carpeta = self.base_dir
        
        # .glob("**/*.pdf") = busca .pdf en esta carpeta y subcarpetas
        pdfs = list(carpeta.glob("**/*.pdf"))
        
        return sorted(pdfs)
    
    # ========================================================================
    # MÉTODO 8: Obtener información de un PDF
    # ========================================================================
    
    def obtener_info_pdf(self, ruta: Path) -> dict:
        """
        Obtiene información sobre un PDF guardado.
        
        Args:
            ruta: Ruta del PDF
        
        Returns:
            dict con: nombre, tamaño, hash, existe
        
        Ejemplo:
            >>> manager = LocalStorageManager()
            >>> info = manager.obtener_info_pdf("backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf")
            >>> print(info["nombre"])
            5036317.pdf
            >>> print(info["tamaño_mb"])
            2.5
        """
        
        ruta = Path(ruta)
        
        return {
            "nombre": ruta.name,
            "ruta_completa": str(ruta),
            "existe": ruta.exists(),
            "tamaño_bytes": ruta.stat().st_size if ruta.exists() else None,
            "tamaño_mb": round(ruta.stat().st_size / (1024 * 1024), 2) if ruta.exists() else None,
            "hash": calcular_sha256(ruta) if ruta.exists() else None,
        }


# ============================================================================
# FUNCIONES DE UTILIDAD (no usan la clase)
# ============================================================================

def obtener_ruta_pdf(
    dept_code: str,
    dept_name: str,
    muni_code: str,
    muni_name: str,
    form_serial: str
) -> Path:
    """
    Función rápida para obtener la ruta de un PDF sin crear un manager.
    
    Ejemplo:
        >>> ruta = obtener_ruta_pdf("05", "Antioquia", "001", "Medellin", "5036317")
        >>> print(ruta)
        backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf
    """
    manager = LocalStorageManager()
    return manager._construir_ruta(dept_code, dept_name, muni_code, muni_name, form_serial)


# ============================================================================
# PRUEBAS
# ============================================================================

if __name__ == "__main__":
    """
    Para probar este módulo:
    python backend/src/storage/local_storage.py
    """
    
    import tempfile
    from pathlib import Path
    
    print("\n" + "="*60)
    print("🧪 PRUEBAS DE LOCAL STORAGE")
    print("="*60 + "\n")
    
    # Crear un gestor
    manager = LocalStorageManager()
    print(f"✅ Gestor creado")
    print(f"   Base dir: {manager.base_dir}\n")
    
    # Crear un PDF ficticio para probar
    pdf_falso = b"%PDF-1.4\nEste es un PDF de prueba\n"
    
    try:
        # Guardar el PDF
        print("💾 Intentando guardar PDF...")
        ruta, hash_val = manager.guardar_pdf(
            contenido=pdf_falso,
            dept_code="05",
            dept_name="Antioquia",
            muni_code="001",
            muni_name="Medellin",
            form_serial="5036317_TEST"
        )
        
        print(f"✅ PDF guardado")
        print(f"   Ruta: {ruta}")
        print(f"   Hash: {hash_val[:16]}...\n")
        
        # Leer el PDF
        print("📖 Intentando leer PDF...")
        contenido = manager.leer_pdf(ruta)
        print(f"✅ PDF leído: {len(contenido)} bytes\n")
        
        # Verificar integridad
        print("🔍 Verificando integridad...")
        es_intacto = manager.verificar_integridad(ruta, hash_val)
        print(f"✅ Integridad: {'SÍ' if es_intacto else 'NO'}\n")
        
        # Obtener información
        print("ℹ️ Información del PDF:")
        info = manager.obtener_info_pdf(ruta)
        for clave, valor in info.items():
            print(f"   {clave}: {valor}")
        
        # Limpiar (eliminar el archivo de prueba)
        ruta.unlink()
        print(f"\n✅ Archivo de prueba eliminado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60 + "\n")