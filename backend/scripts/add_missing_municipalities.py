#!/usr/bin/env python3
"""
add_missing_municipalities.py — Agregar los 5 municipios que faltan para registrar los 30 PDFs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_URL
from src.database.schema import (
    create_engine_connection,
    Municipality,
    Zone,
    Station,
    VotingTable,
)
from sqlalchemy.orm import sessionmaker

# Los 5 municipios faltantes
FALTANTES = [
    ("01", "002", "BELLO"),
    ("01", "045", "ENVIGADO"),
    ("15", "001", "BOGOTA"),  # Bogotá está en Cundinamarca (depto 15)
    ("15", "098", "ZIPAQUIRA"),
    ("31", "361", "YUMBO"),
]


def add_municipalities():
    print("\n" + "=" * 80)
    print("🏙️  AGREGANDO 5 MUNICIPIOS FALTANTES")
    print("=" * 80 + "\n")
    
    engine = create_engine_connection(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        agregados = 0
        for dept_code, muni_code, muni_name in FALTANTES:
            existe = session.query(Municipality).filter_by(
                code=muni_code,
                department_code=dept_code
            ).first()
            
            if not existe:
                muni = Municipality(
                    code=muni_code,
                    department_code=dept_code,
                    name=muni_name
                )
                session.add(muni)
                agregados += 1
                print(f"   ✅ {dept_code}-{muni_code}: {muni_name}")
            else:
                print(f"   ⏭️  {dept_code}-{muni_code}: ya existe")
        
        session.commit()
        print(f"\n✅ {agregados} municipios agregados\n")
        
        # Ahora agregar geografía (zonas, puestos, mesas) para estos municipios
        print("🗳️  Agregando geografía electoral...")
        zonas_map = {}
        
        for dept_code, muni_code, muni_name in FALTANTES:
            # Zona
            zona_key = (dept_code, muni_code, "001")
            zona = session.query(Zone).filter_by(
                municipality_code=muni_code,
                municipality_department=dept_code,
                zone_number="001"
            ).first()
            
            if not zona:
                zona = Zone(
                    municipality_code=muni_code,
                    municipality_department=dept_code,
                    zone_number="001"
                )
                session.add(zona)
                session.flush()
                print(f"   ✅ Zona creada: {dept_code}-{muni_code}-001")
            
            zonas_map[zona_key] = zona
            
            # Puesto
            puesto = session.query(Station).filter_by(
                zone_id=zona.id,
                station_number="01"
            ).first()
            
            if not puesto:
                puesto = Station(
                    zone_id=zona.id,
                    station_number="01",
                    name=f"Puesto 01 - {muni_name}",
                    address=None,
                    latitude=None,
                    longitude=None
                )
                session.add(puesto)
                session.flush()
                print(f"   ✅ Puesto creado: {dept_code}-{muni_code}-001-01")
            
            # Mesa
            mesa = session.query(VotingTable).filter_by(
                station_id=puesto.id,
                table_number="001"
            ).first()
            
            if not mesa:
                mesa = VotingTable(
                    station_id=puesto.id,
                    table_number="001",
                    registered_voters=None
                )
                session.add(mesa)
                print(f"   ✅ Mesa creada: {dept_code}-{muni_code}-001-01-001")
        
        session.commit()
        print(f"\n✅ Geografía agregada\n")
        
        print("=" * 80)
        print("✅ COMPLETADO")
        print("=" * 80)
        print(f"\n💡 Próximo paso: registrar PDFs nuevamente:")
        print(f"   cd backend && python scripts/register_downloaded_pdfs.py\n")
        
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(add_municipalities())
