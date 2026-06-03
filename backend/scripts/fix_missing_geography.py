#!/usr/bin/env python3
"""
fix_missing_geography.py — Agregar municipios y mesas faltantes para los 30 PDFs.

Patrón: seguir la estructura de seed_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_URL
from src.database.schema import (
    create_engine_connection,
    Base,
    Department,
    Municipality,
    Zone,
    Station,
    VotingTable,
)
from sqlalchemy.orm import sessionmaker

# Configuración: (depto, muni, nombre) necesarios para los 30 PDFs
MUNICIPIOS_FALTANTES = [
    ("05", "002", "BELLO"),
    ("05", "045", "ENVIGADO"),
    ("08", "001", "BARRANQUILLA"),
    ("19", "001", "POPAYAN"),
    ("23", "001", "MONTERIA"),
    ("25", "098", "ZIPAQUIRA"),
    ("41", "001", "NEIVA"),
    ("47", "001", "SANTA MARTA"),
    ("50", "001", "VILLAVICENCIO"),
    ("52", "001", "PASTO"),
    ("63", "001", "ARMENIA"),
    ("66", "001", "PEREIRA"),
    ("68", "001", "BUCARAMANGA"),
    ("70", "001", "SINCELEJO"),
    ("73", "001", "IBAGUE"),
    ("76", "001", "CALI"),
    ("76", "361", "YUMBO"),
    ("99", "001", "MOCOA"),
]

def normalizar(valor: str, ancho: int) -> str:
    """Normalizar código."""
    v = str(valor).strip()
    return v.zfill(ancho) if v.isdigit() else v


def fix_geography():
    """Agrega municipios, zonas, puestos y mesas."""
    
    print("\n" + "=" * 80)
    print("🔧 CORRIGIENDO GEOGRAFÍA ELECTORAL FALTANTE")
    print("=" * 80 + "\n")
    
    engine = create_engine_connection(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Paso 1: Municipios
        print("📍 Paso 1: Agregando municipios...")
        municipios_agregados = 0
        for dept_code, muni_code, muni_name in MUNICIPIOS_FALTANTES:
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
                municipios_agregados += 1
                print(f"   ✅ {dept_code}-{muni_code}: {muni_name}")
        
        session.commit()
        print(f"✅ {municipios_agregados} municipios agregados\n")
        
        # Paso 2: Zonas
        print("🗳️  Paso 2: Agregando zonas...")
        zonas_map = {}
        zonas_agregadas = 0
        
        for dept_code, muni_code, _ in MUNICIPIOS_FALTANTES:
            dept = normalizar(dept_code, 2)
            muni = normalizar(muni_code, 3)
            zona_num = "001"
            
            key = (dept, muni, zona_num)
            if key in zonas_map:
                continue
            
            existe = session.query(Zone).filter_by(
                municipality_code=muni,
                municipality_department=dept,
                zone_number=zona_num
            ).first()
            
            if existe:
                zonas_map[key] = existe
                print(f"   ⏭️  Zona {zona_num} ({dept}-{muni}): existe")
            else:
                zona = Zone(
                    municipality_code=muni,
                    municipality_department=dept,
                    zone_number=zona_num
                )
                session.add(zona)
                session.flush()
                zonas_map[key] = zona
                zonas_agregadas += 1
                print(f"   ✅ Zona {zona_num} ({dept}-{muni}): creada")
        
        session.commit()
        print(f"✅ {zonas_agregadas} zonas agregadas\n")
        
        # Paso 3: Puestos
        print("🏢 Paso 3: Agregando puestos...")
        puestos_map = {}
        puestos_agregados = 0
        
        for dept_code, muni_code, muni_name in MUNICIPIOS_FALTANTES:
            dept = normalizar(dept_code, 2)
            muni = normalizar(muni_code, 3)
            zona_num = "001"
            puesto = "01"
            
            zona_key = (dept, muni, zona_num)
            zona = zonas_map.get(zona_key)
            
            if not zona:
                print(f"   ⚠️  Zona no encontrada: {dept}-{muni}")
                continue
            
            key = (dept, muni, zona_num, puesto)
            if key in puestos_map:
                continue
            
            existe = session.query(Station).filter_by(
                zone_id=zona.id,
                station_number=puesto
            ).first()
            
            if existe:
                puestos_map[key] = existe
                print(f"   ⏭️  Puesto {puesto}: existe")
            else:
                estacion = Station(
                    zone_id=zona.id,
                    station_number=puesto,
                    name=f"Puesto 01 - {muni_name}",
                    address=None,
                    latitude=None,
                    longitude=None
                )
                session.add(estacion)
                session.flush()
                puestos_map[key] = estacion
                puestos_agregados += 1
                print(f"   ✅ Puesto {puesto} ({dept}-{muni}): creado")
        
        session.commit()
        print(f"✅ {puestos_agregados} puestos agregados\n")
        
        # Paso 4: Mesas
        print("📋 Paso 4: Agregando mesas...")
        mesas_agregadas = 0
        
        for dept_code, muni_code, _ in MUNICIPIOS_FALTANTES:
            dept = normalizar(dept_code, 2)
            muni = normalizar(muni_code, 3)
            zona_num = "001"
            puesto = "01"
            mesa_num = "001"
            
            puesto_key = (dept, muni, zona_num, puesto)
            estacion = puestos_map.get(puesto_key)
            
            if not estacion:
                print(f"   ⚠️  Puesto no encontrado: {dept}-{muni}")
                continue
            
            existe = session.query(VotingTable).filter_by(
                station_id=estacion.id,
                table_number=mesa_num
            ).first()
            
            if not existe:
                mesa = VotingTable(
                    station_id=estacion.id,
                    table_number=mesa_num,
                    registered_voters=None
                )
                session.add(mesa)
                mesas_agregadas += 1
                print(f"   ✅ Mesa {mesa_num} ({dept}-{muni}): creada")
        
        session.commit()
        print(f"✅ {mesas_agregadas} mesas agregadas\n")
        
        # Verificar
        print("📊 Estado final de la BD:")
        print(f"   Municipios: {session.query(Municipality).count()}")
        print(f"   Zonas: {session.query(Zone).count()}")
        print(f"   Puestos: {session.query(Station).count()}")
        print(f"   Mesas: {session.query(VotingTable).count()}\n")
        
        print("=" * 80)
        print("✅ GEOGRAFÍA CORREGIDA")
        print("=" * 80 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(fix_geography())
