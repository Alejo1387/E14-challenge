"""
setup_db.py - Inicializar la Base de Datos E14 Challenge

Crea el archivo SQLite y todas las tablas definidas en src/database/schema.py.

Uso:
    cd backend
    python scripts/setup_db.py           # crea tablas que falten
    python scripts/setup_db.py --reset   # borra TODO y recrea (solo desarrollo)

Orden de tablas (dependencias):
    elections → election_candidates
    departments → municipalities → zones → stations → voting_tables
    forms → extraction_results → candidate_votes, field_tags, anomalies
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_URL, DATABASE_PATH, BACKEND_DATA_DIR
from src.database.schema import Base, create_all_tables, drop_all_tables
from src.database.connection import verificar_conexion

# Resumen del esquema actual (alineado con schema.py)
TABLAS_POR_GRUPO = {
    "Elección": [
        ("elections", "Configuración de cada elección (PRES_1V_2022, etc.)"),
        ("election_candidates", "Candidatos por elección"),
    ],
    "Geografía electoral": [
        ("departments", "Departamentos"),
        ("municipalities", "Municipios"),
        ("zones", "Zonas"),
        ("stations", "Puestos de votación"),
        ("voting_tables", "Mesas"),
    ],
    "Formularios E-14": [
        ("forms", "PDFs descargados y metadatos"),
    ],
    "OCR y análisis": [
        ("extraction_results", "Resultados de Gemini"),
        ("candidate_votes", "Votos por candidato"),
        ("field_tags", "Problemas en campos del formulario"),
        ("anomalies", "Anomalías detectadas"),
    ],
}


def _crear_carpetas() -> bool:
    print("📁 Verificando carpetas de datos...")
    try:
        BACKEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {BACKEND_DATA_DIR}\n")
        return True
    except OSError as e:
        print(f"   ❌ Error: {e}\n")
        return False


def _mostrar_tablas_creadas() -> None:
    print("📋 Tablas en el esquema:\n")
    for grupo, tablas in TABLAS_POR_GRUPO.items():
        print(f"   [{grupo}]")
        for nombre, descripcion in tablas:
            if nombre in Base.metadata.tables:
                cols = len(Base.metadata.tables[nombre].columns)
                print(f"      ✅ {nombre:22} ({cols} cols) — {descripcion}")
            else:
                print(f"      ❌ {nombre:22} — no definida en schema.py")
        print()


def _verificar_sqlite() -> bool:
    """Comprueba que el archivo .db existe y responde."""
    if not DATABASE_PATH.exists():
        print(f"   ❌ No se creó el archivo: {DATABASE_PATH}\n")
        return False

    if verificar_conexion():
        print(f"   ✅ Archivo: {DATABASE_PATH}")
        print("   ✅ Conexión OK\n")
        return True

    print("   ❌ No se pudo verificar la conexión\n")
    return False


def main(reset: bool = False) -> bool:
    print("\n" + "=" * 70)
    print("🔧 INICIALIZANDO BASE DE DATOS E14 CHALLENGE")
    print("=" * 70 + "\n")

    if not _crear_carpetas():
        return False

    print("🗄️  Base de datos:")
    print(f"   Ruta: {DATABASE_PATH}")
    print(f"   URL:  {DATABASE_URL}\n")

    if reset:
        print("⚠️  Modo --reset: eliminando todas las tablas existentes...")
        try:
            drop_all_tables(DATABASE_URL)
        except Exception as e:
            print(f"   ❌ Error al eliminar tablas: {e}\n")
            return False

    try:
        create_all_tables(DATABASE_URL)
    except Exception as e:
        print(f"   ❌ Error creando tablas: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    print("   ✅ Tablas creadas/actualizadas\n")

    _mostrar_tablas_creadas()

    if not _verificar_sqlite():
        return False

    print("=" * 70)
    print("✅ INICIALIZACIÓN COMPLETADA")
    print("=" * 70)
    print()
    print("📝 Próximos pasos:")
    print("   1. Poblar datos base:")
    print("      python scripts/seed_data.py")
    print()
    print("   2. Registrar PDFs descargados:")
    print("      python scripts/register_downloaded_pdfs.py")
    print()
    if not reset:
        print("   Si cambiaste columnas/tablas y hay conflictos, usa:")
        print("      python scripts/setup_db.py --reset")
        print()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear BD y tablas E14 Challenge")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Borra todas las tablas y las vuelve a crear (pierde datos)",
    )
    args = parser.parse_args()

    try:
        sys.exit(0 if main(reset=args.reset) else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
