"""
register_downloaded_pdfs.py - Registrar PDFs descargados (scraper Playwright)

Estructura esperada bajo backend/data/raw/:
    {depto}/{muni}/{zona}/{puesto}/{mesa}.pdf

El número de mesa es el nombre del archivo sin .pdf (ej. 001.pdf → mesa "001").

Importante — columna forms.voting_table_id:
    NO guarda "001" ni "099". Es la clave foránea (entero autoincremental)
    hacia voting_tables.id. El código de mesa del PDF vive en
    voting_tables.table_number (mismo valor que el nombre del archivo).

Ejemplo:
    backend/data/raw/05/001/001/01/099.pdf  →  mesa "099", voting_tables.id puede ser 3

Opcional: sidecar scrape_v2 → 031.pdf.meta.json

¿Cómo ejecutar?
    cd backend
    python scripts/register_downloaded_pdfs.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BASE_DIR, DATA_RAW_DIR, ELECTION_ID
from src.database.crud import (
    asegurar_eleccion,
    crear_formulario,
    resolver_voting_table,
    verificar_geografia_formulario,
)
from src.database.queries import obtener_formulario_por_serial
from src.storage.local_storage import LocalStorageManager
from src.utils.hashing import calcular_sha256


class RegistradorPDFs:
    """Registra PDFs del scraper en la base de datos."""

    def __init__(self):
        self.storage_manager = LocalStorageManager()
        self.stats = {
            "total_encontrados": 0,
            "registrados": 0,
            "ya_existentes": 0,
            "errores": 0,
            "detalles_errores": [],
        }

    def detectar_pdfs(self) -> list:
        print(f"🔍 Buscando PDFs en {DATA_RAW_DIR}...\n")
        pdfs = self.storage_manager.listar_pdfs()
        print(f"   Total de PDFs encontrados: {len(pdfs)}\n")
        return pdfs

    def validar_pdf(self, ruta_pdf: Path) -> tuple:
        if not ruta_pdf.exists():
            return False, "Archivo no existe"
        if not ruta_pdf.is_file():
            return False, "No es un archivo"
        try:
            with open(ruta_pdf, "rb") as f:
                if f.read(4) != b"%PDF":
                    return False, "No es un PDF válido"
        except OSError as e:
            return False, f"Error leyendo archivo: {e}"
        return True, None

    def registrar_pdf(self, info: dict) -> bool:
        form_serial = info["form_serial"]
        ruta_completa = Path(info["ruta_completa"])

        try:
            es_valido, error_msg = self.validar_pdf(ruta_completa)
            if not es_valido:
                self._registrar_error(form_serial, error_msg)
                return False

            existente = obtener_formulario_por_serial(form_serial)
            if existente:
                self.stats["ya_existentes"] += 1
                print(f"   ⏭️  {form_serial}: ya registrado")
                return False

            mesa = resolver_voting_table(
                department_code=info["dept_code"],
                municipality_code=info["muni_code"],
                zone_number=info["zone_code"],
                station_number=info["station_code"],
                table_number=info["table_number"],
            )
            if not mesa:
                self._registrar_error(
                    form_serial,
                    "No se pudo resolver zona/puesto/mesa (¿seed_data ejecutado?)",
                )
                return False

            if mesa["table_number"] != info["table_number"]:
                self._registrar_error(
                    form_serial,
                    (
                        f"Mesa en BD ({mesa['table_number']}) no coincide con el PDF "
                        f"({info['table_number']})"
                    ),
                )
                return False

            voting_table_id = mesa["id"]

            error_geo = verificar_geografia_formulario(
                info["dept_code"],
                info["muni_code"],
            )
            if error_geo:
                self._registrar_error(form_serial, error_geo)
                return False

            hash_sha256 = calcular_sha256(ruta_completa)
            try:
                local_path = str(ruta_completa.resolve().relative_to(BASE_DIR.resolve()))
            except ValueError:
                local_path = info.get("ruta_relativa") or str(ruta_completa)

            form_id = crear_formulario(
                form_serial=form_serial,
                election_id=ELECTION_ID,
                department_code=info["dept_code"],
                municipality_code=info["muni_code"],
                voting_table_id=voting_table_id,
                local_path=local_path,
                file_hash=hash_sha256,
            )

            if form_id:
                self.stats["registrados"] += 1
                print(
                    f"   ✅ {form_serial}: depto {info['dept_code']} | "
                    f"muni {info['muni_code']} | zona {info['zone_code']} | "
                    f"puesto {info['station_code']} | mesa {info['table_number']} "
                    f"(archivo {info['table_number']}.pdf → "
                    f"voting_tables.table_number={mesa['table_number']}, "
                    f"forms.voting_table_id={voting_table_id})"
                )
                return True

            self._registrar_error(form_serial, "Error al insertar en BD")
            return False

        except Exception as e:
            self._registrar_error(form_serial, str(e))
            print(f"   ❌ {form_serial}: {e}")
            return False

    def _registrar_error(self, form_serial: str, error: str) -> None:
        self.stats["errores"] += 1
        self.stats["detalles_errores"].append(
            {"form_serial": form_serial, "error": error}
        )
        print(f"   ❌ {form_serial}: {error}")

    def ejecutar(self) -> dict:
        print("\n" + "=" * 70)
        print("📝 REGISTRANDO PDFs (ruta scraper: depto/muni/zona/puesto/mesa)")
        print("=" * 70 + "\n")

        print(f"🗳️  Elección configurada: {ELECTION_ID}")
        if not asegurar_eleccion(ELECTION_ID):
            print("❌ No se pudo preparar la elección en BD. Abortando.\n")
            return self.stats
        print()

        pdfs = self.detectar_pdfs()
        self.stats["total_encontrados"] = len(pdfs)

        if not pdfs:
            print("✅ No hay PDFs para registrar\n")
            return self.stats

        print("📥 Registrando PDFs...\n")

        for ruta_pdf in pdfs:
            info = self.storage_manager.parsear_ubicacion(ruta_pdf)
            if not info:
                self.stats["errores"] += 1
                self.stats["detalles_errores"].append({
                    "form_serial": ruta_pdf.name,
                    "error": (
                        "Ruta inválida; se espera "
                        "backend/data/raw/{depto}/{muni}/{zona}/{puesto}/{mesa}.pdf"
                    ),
                })
                print(f"   ❌ {ruta_pdf.name}: ruta no válida")
                continue

            self.registrar_pdf(info)

        self.mostrar_resumen()
        return self.stats

    def mostrar_resumen(self):
        print("\n" + "=" * 70)
        print("📊 RESUMEN")
        print("=" * 70 + "\n")
        print(f"Total encontrados:        {self.stats['total_encontrados']}")
        print(f"Registrados exitosamente: {self.stats['registrados']}")
        print(f"Ya existentes:            {self.stats['ya_existentes']}")
        print(f"Errores:                  {self.stats['errores']}")
        print()

        if self.stats["detalles_errores"]:
            print("Errores detectados:")
            for error in self.stats["detalles_errores"]:
                print(f"  • {error['form_serial']}: {error['error']}")
            print()

        print("=" * 70 + "\n")


def main():
    registrador = RegistradorPDFs()
    stats = registrador.ejecutar()
    return 0 if stats["errores"] == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
