#!/usr/bin/env python3
"""
add_all_departments.py — Agregar todos los departamentos de Colombia a la BD.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_URL
from src.database.schema import (
    create_engine_connection,
    Department,
)
from sqlalchemy.orm import sessionmaker

# Todos los departamentos de Colombia
ALL_DEPARTMENTS = [
    ("01", "Antioquia"),
    ("03", "Atlántico"),
    ("05", "Bolívar"),
    ("07", "Boyacá"),
    ("09", "Caldas"),
    ("11", "Cauca"),
    ("12", "Cesar"),
    ("13", "Córdoba"),
    ("15", "Cundinamarca"),
    ("16", "Bogotá D.C."),
    ("17", "Chocó"),
    ("19", "Huila"),
    ("21", "Magdalena"),
    ("23", "Nariño"),
    ("24", "Risaralda"),
    ("25", "Norte de Santander"),
    ("26", "Quindío"),
    ("27", "Santander"),
    ("28", "Sucre"),
    ("29", "Tolima"),
    ("31", "Valle"),
    ("40", "Arauca"),
    ("44", "Caquetá"),
    ("46", "Casanare"),
    ("48", "La Guajira"),
    ("50", "Guainía"),
    ("52", "Meta"),
    ("54", "Guaviare"),
    ("56", "San Ándres"),
    ("60", "Amazonas"),
    ("64", "Putumayo"),
    ("68", "Vaupés"),
    ("72", "Vichada"),
    ("88", "Consulados")
]


def add_departments():
    print("\n" + "=" * 80)
    print("🌍 AGREGANDO TODOS LOS DEPARTAMENTOS DE COLOMBIA")
    print("=" * 80 + "\n")
    
    engine = create_engine_connection(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        agregados = 0
        for code, name in ALL_DEPARTMENTS:
            existe = session.query(Department).filter_by(code=code).first()
            if not existe:
                dept = Department(code=code, name=name)
                session.add(dept)
                agregados += 1
                print(f"   ✅ {code}: {name}")
            else:
                print(f"   ⏭️  {code}: {name} (ya existe)")
        
        session.commit()
        print(f"\n✅ {agregados} departamentos agregados")
        print(f"Total en BD: {session.query(Department).count()}\n")
        
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(add_departments())
