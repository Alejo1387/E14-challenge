"""
seed_data.py - Llenar la Base de Datos con Datos de Prueba

Este script inserta datos REALES de Colombia:
- 33 Departamentos + Bogotá D.C.
- Municipios principales de las 6 ciudades (Bogotá, Medellín, etc.)
- Zonas, estaciones y mesas (ficticias pero realistas)

¿Cómo ejecutar?
    cd backend
    python scripts/seed_data.py

¿Qué hace?
    1. Se conecta a la BD
    2. Verifica si ya tiene datos
    3. Inserta departamentos
    4. Inserta municipios
    5. Inserta zonas, estaciones, mesas
    6. Reporta lo que insertó
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid
import random

# Agregar backend/ al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar
from config import DATABASE_URL, ELECTION_ID
from src.database.schema import create_engine_connection, create_all_tables, Base, Department, Municipality, Zone, Station, VotingTable, Form, ProcessingStatus
from sqlalchemy.orm import Session

# ============================================================================
# DATOS DE COLOMBIA (REALES)
# ============================================================================

# Lista de todos los departamentos de Colombia
DEPARTAMENTOS_COLOMBIA = [
    ("01", "Amazonas"),
    ("02", "Antioquia"),
    ("03", "Arauca"),
    ("04", "Atlántico"),
    ("05", "Bolívar"),
    ("06", "Boyacá"),
    ("07", "Caldas"),
    ("08", "Caquetá"),
    ("09", "Casanare"),
    ("10", "Cauca"),
    ("11", "Cesar"),
    ("12", "Chocó"),
    ("13", "Córdoba"),
    ("14", "Cundinamarca"),
    ("15", "Guainía"),
    ("16", "Guaviare"),
    ("17", "Huila"),
    ("18", "La Guajira"),
    ("19", "Magdalena"),
    ("20", "Meta"),
    ("21", "Nariño"),
    ("22", "Norte de Santander"),
    ("23", "Putumayo"),
    ("24", "Quindío"),
    ("25", "Risaralda"),
    ("26", "Santander"),
    ("27", "Sucre"),
    ("28", "Tolima"),
    ("29", "Valle del Cauca"),
    ("30", "Vaupés"),
    ("31", "Vichada"),
    ("32", "Bogotá D.C."),  # Bogotá es su propio departamento
]

# Municipios principales de las 6 ciudades objetivo
# Estructura: (dept_code, muni_code, muni_name)
MUNICIPIOS_OBJETIVO = [
    # Bogotá D.C. (dept 32)
    ("32", "001", "Bogotá"),
    
    # Antioquia (dept 02)
    ("02", "001", "Medellín"),
    ("02", "006", "Bello"),
    ("02", "088", "Itagüí"),
    
    # Atlántico (dept 04)
    ("04", "001", "Barranquilla"),
    ("04", "042", "Soledad"),
    
    # Bolívar (dept 05)
    ("05", "001", "Cartagena"),
    ("05", "109", "Turbaco"),
    
    # Valle del Cauca (dept 29)
    ("29", "001", "Cali"),
    ("29", "110", "Palmira"),
    
    # Santander (dept 26)
    ("26", "001", "Bucaramanga"),
    ("26", "224", "Floridablanca"),
]

# ============================================================================
# FUNCIÓN PARA INSERTAR DEPARTAMENTOS
# ============================================================================

def insertar_departamentos(session: Session) -> int:
    """
    Inserta todos los departamentos de Colombia.
    
    Args:
        session: Sesión de BD
    
    Returns:
        int: Cantidad de departamentos insertados
    """
    
    print("\n📍 Insertando departamentos de Colombia...")
    
    insertados = 0
    
    for dept_code, dept_name in DEPARTAMENTOS_COLOMBIA:
        # Verificar que no existe
        existe = session.query(Department).filter_by(code=dept_code).first()
        
        if not existe:
            # Crear nuevo departamento
            dept = Department(code=dept_code, name=dept_name)
            session.add(dept)
            insertados += 1
        else:
            print(f"   ⏭️  Departamento {dept_code} ({dept_name}) ya existe")
    
    session.commit()
    print(f"   ✅ {insertados} departamentos insertados\n")
    
    return insertados


# ============================================================================
# FUNCIÓN PARA INSERTAR MUNICIPIOS
# ============================================================================

def insertar_municipios(session: Session) -> int:
    """
    Inserta los municipios principales de las 6 ciudades objetivo.
    
    Args:
        session: Sesión de BD
    
    Returns:
        int: Cantidad de municipios insertados
    """
    
    print("🏙️  Insertando municipios objetivo...")
    
    insertados = 0
    
    for dept_code, muni_code, muni_name in MUNICIPIOS_OBJETIVO:
        # Verificar que no existe
        existe = session.query(Municipality).filter_by(
            code=muni_code,
            department_code=dept_code
        ).first()
        
        if not existe:
            # Crear nuevo municipio
            muni = Municipality(
                code=muni_code,
                department_code=dept_code,
                name=muni_name
            )
            session.add(muni)
            insertados += 1
        else:
            print(f"   ⏭️  Municipio {muni_code} ({muni_name}) ya existe")
    
    session.commit()
    print(f"   ✅ {insertados} municipios insertados\n")
    
    return insertados


# ============================================================================
# FUNCIÓN PARA INSERTAR ZONAS, ESTACIONES Y MESAS
# ============================================================================

def insertar_geografia_votacion(session: Session) -> dict:
    """
    Inserta zonas, estaciones y mesas ficticias pero realistas.
    
    Para cada municipio, crea:
    - 3 zonas
    - 5 estaciones por zona
    - 3-4 mesas por estación
    
    Args:
        session: Sesión de BD
    
    Returns:
        dict con cantidades insertadas
    """
    
    print("🗳️  Insertando zonas, estaciones y mesas...")
    
    stats = {
        "zonas": 0,
        "estaciones": 0,
        "mesas": 0,
    }
    
    # Para cada municipio objetivo
    municipios = session.query(Municipality).filter(
        Municipality.department_code.in_([dept for dept, _, _ in MUNICIPIOS_OBJETIVO])
    ).all()
    
    for muni in municipios:
        # Crear 3 zonas por municipio
        for zona_num in range(1, 4):
            zona = Zone(
                municipality_code=muni.code,
                municipality_department=muni.department_code,
                zone_number=f"{zona_num:02d}"
            )
            session.add(zona)
            stats["zonas"] += 1
        
        session.flush()  # Guardar las zonas para obtener sus IDs
        
        # Para cada zona, crear estaciones
        zonas = session.query(Zone).filter_by(municipality_code=muni.code).all()
        
        for zona in zonas:
            # 5 estaciones por zona
            for estacion_num in range(1, 6):
                estacion = Station(
                    zone_id=zona.id,
                    station_number=f"{estacion_num:03d}",
                    name=f"Escuela #{estacion_num * 100 + zona.id}",
                    address=f"Dirección ficticia {zona.zone_number}-{estacion_num}"
                )
                session.add(estacion)
                stats["estaciones"] += 1
            
            session.flush()
            
            # Para cada estación, crear mesas
            estaciones = session.query(Station).filter_by(zone_id=zona.id).all()
            
            for estacion in estaciones:
                # 3-4 mesas por estación
                mesas_count = 3 if estacion.id % 2 == 0 else 4
                
                for mesa_num in range(1, mesas_count + 1):
                    mesa = VotingTable(
                        station_id=estacion.id,
                        table_number=f"{(mesa_num + estacion.id) % 100:03d}",
                        registered_voters=300 + (estacion.id * mesa_num) % 200
                    )
                    session.add(mesa)
                    stats["mesas"] += 1
    
    session.commit()
    print(f"   ✅ {stats['zonas']} zonas insertadas")
    print(f"   ✅ {stats['estaciones']} estaciones insertadas")
    print(f"   ✅ {stats['mesas']} mesas insertadas\n")
    
    return stats


# ============================================================================
# FUNCIÓN PARA INSERTAR PDFs DE PRUEBA (OPCIONAL)
# ============================================================================

def insertar_pdfs_prueba(session: Session) -> int:
    """
    Inserta algunos formularios E-14 ficticios para pruebas.
    
    IMPORTANTE: Estos PDFs NO existen realmente en disk.
    Solo estamos probando que la BD funciona.
    
    Args:
        session: Sesión de BD
    
    Returns:
        int: Cantidad de PDFs insertados
    """
    
    print("📄 Insertando PDFs de prueba...")
    
    insertados = 0
    
    # Obtener algunas mesas de la BD
    mesas = session.query(VotingTable).limit(10).all()
    
    for i, mesa in enumerate(mesas):
        # Crear un formulario ficticio con serial único
        # Usamos timestamp + uuid para garantizar que sea único
        timestamp = int(datetime.utcnow().timestamp() * 1000)  # milliseconds
        random_suffix = random.randint(1000, 9999)
        form_serial = f"TEST_{timestamp}_{random_suffix}_{i:03d}"
        
        # Verificar que no existe ya
        existe = session.query(Form).filter_by(form_serial=form_serial).first()
        
        if existe:
            print(f"   ⏭️  Formulario {form_serial} ya existe")
            continue
        
        form = Form(
            form_serial=form_serial,
            election_id=ELECTION_ID,
            department_code=mesa.station.zone.municipality_department,
            municipality_code=mesa.station.zone.municipality_code,
            voting_table_id=mesa.id,
            local_path=f"data/raw/TEST/{form_serial}.pdf",
            file_hash="HASH_FICTICIO_" + form_serial,
            download_timestamp=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )
        
        session.add(form)
        insertados += 1
    
    session.commit()
    print(f"   ✅ {insertados} PDFs de prueba insertados\n")
    
    return insertados


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """
    Ejecuta la inserción de datos de prueba.
    """
    
    print("\n" + "="*70)
    print("🌱 LLENANDO BASE DE DATOS CON DATOS DE PRUEBA")
    print("="*70)
    
    # Conectar a la BD
    print(f"\n🔗 Conectando a: {DATABASE_URL}")
    
    try:
        engine = create_engine_connection(DATABASE_URL)
        session = Session(engine)
        print("   ✅ Conectado\n")
    except Exception as e:
        print(f"   ❌ Error conectando: {e}\n")
        return False
    
    try:
        # Crear todas las tablas si no existen
        Base.metadata.create_all(engine)
        
        # PASO 1: Insertar departamentos
        dept_insertados = insertar_departamentos(session)
        
        # PASO 2: Insertar municipios
        muni_insertados = insertar_municipios(session)
        
        # PASO 3: Insertar zonas, estaciones, mesas
        stats_geografia = insertar_geografia_votacion(session)
        
        # PASO 4: Insertar PDFs de prueba
        pdf_insertados = insertar_pdfs_prueba(session)
        
        # RESUMEN FINAL
        print("="*70)
        print("✅ DATOS INSERTADOS EXITOSAMENTE")
        print("="*70)
        print(f"\n📊 Resumen:")
        print(f"   • Departamentos: {dept_insertados}")
        print(f"   • Municipios: {muni_insertados}")
        print(f"   • Zonas: {stats_geografia['zonas']}")
        print(f"   • Estaciones: {stats_geografia['estaciones']}")
        print(f"   • Mesas: {stats_geografia['mesas']}")
        print(f"   • PDFs de prueba: {pdf_insertados}")
        print()
        
        total = (
            dept_insertados + 
            muni_insertados + 
            stats_geografia['zonas'] + 
            stats_geografia['estaciones'] + 
            stats_geografia['mesas'] + 
            pdf_insertados
        )
        print(f"   📈 TOTAL: {total} registros\n")
        
        print("📝 Próximos pasos:")
        print("   1. Verifica los datos en la BD:")
        print("      python scripts/inspect_db.py  (lo crearemos después)")
        print()
        print("   2. Cuando Persona A descargue PDFs reales, ejecuta:")
        print("      python scripts/register_downloaded_pdfs.py")
        print()
        
        session.close()
        return True
    
    except Exception as e:
        print(f"\n❌ Error insertando datos: {e}\n")
        import traceback
        traceback.print_exc()
        session.close()
        return False


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    """
    Se ejecuta cuando haces: python scripts/seed_data.py
    """
    
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)