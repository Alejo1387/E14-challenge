"""
local_storage.py - Gestionar almacenamiento de PDFs en el disco local

Estructura (scraper Playwright):
    backend/data/raw/{depto}/{muni}/{zona}/{puesto}/{mesa}.pdf
"""

from pathlib import Path
from typing import Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DATA_RAW_DIR, MAX_PDF_SIZE
from src.storage.pdf_paths import construir_ruta_pdf, parsear_ruta_pdf
from src.utils.hashing import calcular_sha256


class LocalStorageManager:
    """Gestiona lectura/escritura de PDFs bajo backend/data/raw/."""

    def __init__(self, base_dir: Path = DATA_RAW_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _construir_ruta(
        self,
        dept_code: str,
        muni_code: str,
        zone_code: str,
        station_code: str,
        table_number: str,
    ) -> Path:
        return construir_ruta_pdf(
            self.base_dir,
            dept_code,
            muni_code,
            zone_code,
            station_code,
            table_number,
        )

    def _crear_carpetas(self, ruta: Path) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)

    def _validar_pdf(self, contenido: bytes, ruta: Path) -> Tuple[bool, Optional[str]]:
        if not contenido.startswith(b"%PDF"):
            return False, "No es un PDF válido (no empieza con %PDF)"
        if len(contenido) > MAX_PDF_SIZE:
            return False, f"PDF muy grande: {len(contenido)} bytes > {MAX_PDF_SIZE} bytes"
        return True, None

    def guardar_pdf(
        self,
        contenido: bytes,
        dept_code: str,
        muni_code: str,
        zone_code: str,
        station_code: str,
        table_number: str,
    ) -> Tuple[Path, str]:
        ruta = self._construir_ruta(
            dept_code, muni_code, zone_code, station_code, table_number
        )
        es_valido, error_msg = self._validar_pdf(contenido, ruta)
        if not es_valido:
            raise ValueError(f"PDF inválido: {error_msg}")

        self._crear_carpetas(ruta)
        with open(ruta, "wb") as archivo:
            archivo.write(contenido)

        return ruta, calcular_sha256(ruta)

    def leer_pdf(self, ruta: Path) -> bytes:
        ruta = Path(ruta)
        if not ruta.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
        with open(ruta, "rb") as archivo:
            return archivo.read()

    def verificar_integridad(self, ruta: Path, hash_esperado: str) -> bool:
        return calcular_sha256(ruta) == hash_esperado

    def listar_pdfs(self, carpeta_relativa: str = "") -> list:
        if carpeta_relativa:
            carpeta = self.base_dir / carpeta_relativa
        else:
            carpeta = self.base_dir
        return sorted(carpeta.glob("**/*.pdf"))

    def parsear_ubicacion(self, ruta_pdf: Path) -> Optional[dict]:
        """Extrae depto/muni/zona/puesto/mesa desde la ruta (y sidecar si existe)."""
        return parsear_ruta_pdf(ruta_pdf, self.base_dir)

    def obtener_info_pdf(self, ruta: Path) -> dict:
        ruta = Path(ruta)
        ubicacion = self.parsear_ubicacion(ruta)
        info = {
            "nombre": ruta.name,
            "ruta_completa": str(ruta),
            "existe": ruta.exists(),
            "tamaño_bytes": ruta.stat().st_size if ruta.exists() else None,
            "tamaño_mb": round(ruta.stat().st_size / (1024 * 1024), 2)
            if ruta.exists()
            else None,
            "hash": calcular_sha256(ruta) if ruta.exists() else None,
            "ubicacion": ubicacion,
        }
        return info


def obtener_ruta_pdf(
    dept_code: str,
    muni_code: str,
    zone_code: str,
    station_code: str,
    table_number: str,
    base_dir: Path = DATA_RAW_DIR,
) -> Path:
    return construir_ruta_pdf(
        base_dir, dept_code, muni_code, zone_code, station_code, table_number
    )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 PRUEBAS DE LOCAL STORAGE")
    print("=" * 60 + "\n")

    manager = LocalStorageManager()
    pdf_falso = b"%PDF-1.4\nEste es un PDF de prueba\n"

    try:
        ruta, hash_val = manager.guardar_pdf(
            contenido=pdf_falso,
            dept_code="05",
            muni_code="001",
            zone_code="001",
            station_code="01",
            table_number="031",
        )
        print(f"✅ Guardado: {ruta}")
        parsed = manager.parsear_ubicacion(ruta)
        print(f"✅ Parseado: {parsed['form_serial']}")
        ruta.unlink()
        print("✅ Archivo de prueba eliminado")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60 + "\n")
