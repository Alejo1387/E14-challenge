"""
crud.py - Funciones para Crear, Actualizar y Eliminar Datos

CRUD = Create, Read, Update, Delete

Este módulo contiene funciones para MODIFICAR la BD.

¿Por qué separar de queries.py?
    • queries.py = LEER (SELECT)
    • crud.py = ESCRIBIR (INSERT, UPDATE, DELETE)
    
    Así está más organizado y es más fácil de mantener.

¿Cómo usarlo?
    from src.database.crud import crear_formulario, actualizar_estado_formulario
    
    # Crear un nuevo formulario
    form_id = crear_formulario(
        form_serial="5036317",
        election_id="PRES_1V_2022",
        department_code="05",
        municipality_code="001",
        voting_table_id=1,
        local_path="backend/data/raw/...",
        file_hash="abc123..."
    )
    
    # Actualizar su estado
    actualizar_estado_formulario(form_id, "EXTRACTED")
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Importar
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import ELECTION_ID, ELECTION_YEAR
from src.database.schema import (
    Department,
    Municipality,
    Zone,
    Station,
    VotingTable,
    Form,
    Election,
    ProcessingStatus,
    FormQuality,
)
from src.database.connection import session_scope
from sqlalchemy.exc import IntegrityError

# ============================================================================
# JERARQUÍA ELECTORAL (zona → puesto → mesa)
# ============================================================================

def _variantes_codigo_zona(zone_number: str) -> list[str]:
    """Acepta '001' del scraper y '01' del seed."""
    z = str(zone_number).strip()
    variantes = [z]
    if z.isdigit():
        sin_ceros = z.lstrip("0") or "0"
        variantes.extend([sin_ceros, sin_ceros.zfill(2), sin_ceros.zfill(3)])
    vistos: list[str] = []
    for v in variantes:
        if v not in vistos:
            vistos.append(v)
    return vistos


def _buscar_zona(session, dept_code: str, muni_code: str, zone_number: str):
    for zn in _variantes_codigo_zona(zone_number):
        zona = session.query(Zone).filter_by(
            municipality_code=muni_code,
            municipality_department=dept_code,
            zone_number=zn,
        ).first()
        if zona:
            return zona
    return None


def resolver_voting_table(
    department_code: str,
    municipality_code: str,
    zone_number: str,
    station_number: str,
    table_number: str,
) -> Optional[dict]:
    """
    Obtiene o crea zona, puesto y mesa a partir del nombre del PDF (sin .pdf).

    Usado al registrar PDFs con ruta:
        data/raw/{depto}/{muni}/{zona}/{puesto}/{mesa}.pdf

    Returns:
        dict con id (PK en voting_tables), table_number (mesa del archivo),
        y códigos de zona/puesto normalizados.
    """
    from src.storage.pdf_paths import normalizar_ubicacion

    u = normalizar_ubicacion(
        department_code,
        municipality_code,
        zone_number,
        station_number,
        table_number,
    )

    try:
        with session_scope() as session:
            muni = session.query(Municipality).filter_by(
                code=u["muni_code"],
                department_code=u["dept_code"],
            ).first()
            if not muni:
                print(
                    f"❌ Municipio {u['muni_code']} (depto {u['dept_code']}) "
                    "no existe en BD. Ejecuta seed_data.py primero."
                )
                return None

            zona = _buscar_zona(
                session, u["dept_code"], u["muni_code"], u["zone_code"]
            )
            if not zona:
                zona = Zone(
                    municipality_code=u["muni_code"],
                    municipality_department=u["dept_code"],
                    zone_number=u["zone_code"],
                )
                session.add(zona)
                session.flush()

            estacion = session.query(Station).filter_by(
                zone_id=zona.id,
                station_number=u["station_code"],
            ).first()
            if not estacion:
                estacion = Station(
                    zone_id=zona.id,
                    station_number=u["station_code"],
                    name=f"Puesto {u['station_code']}",
                )
                session.add(estacion)
                session.flush()

            mesa = session.query(VotingTable).filter_by(
                station_id=estacion.id,
                table_number=u["table_number"],
            ).first()
            if not mesa:
                mesa = VotingTable(
                    station_id=estacion.id,
                    table_number=u["table_number"],
                )
                session.add(mesa)
                session.flush()

            session.commit()
            return {
                "id": mesa.id,
                "table_number": mesa.table_number,
                "station_number": estacion.station_number,
                "zone_number": zona.zone_number,
                "department_code": u["dept_code"],
                "municipality_code": u["muni_code"],
            }

    except Exception as e:
        print(f"❌ Error resolviendo mesa de votación: {e}")
        return None


def resolver_voting_table_id(
    department_code: str,
    municipality_code: str,
    zone_number: str,
    station_number: str,
    table_number: str,
) -> Optional[int]:
    """Atajo: devuelve solo voting_tables.id (FK que va en forms.voting_table_id)."""
    mesa = resolver_voting_table(
        department_code,
        municipality_code,
        zone_number,
        station_number,
        table_number,
    )
    return mesa["id"] if mesa else None


# ============================================================================
# FUNCIONES PARA DEPARTAMENTOS
# ============================================================================

def crear_departamento(dept_code: str, dept_name: str) -> Optional[dict]:
    """
    Crea un nuevo departamento.
    
    Args:
        dept_code: Código (ej: "05")
        dept_name: Nombre (ej: "Antioquia")
    
    Returns:
        dict con los datos creados, o None si error
    
    Ejemplo:
        >>> dept = crear_departamento("99", "Nuevo Departamento")
        >>> print(dept["code"])
        99
    """
    
    try:
        with session_scope() as session:
            # Verificar que no existe
            existe = session.query(Department).filter_by(code=dept_code).first()
            if existe:
                print(f"⚠️  Departamento {dept_code} ya existe")
                return None
            
            # Crear
            dept = Department(code=dept_code, name=dept_name)
            session.add(dept)
            session.commit()
            
            return {
                "code": dept.code,
                "name": dept.name,
                "created_at": dept.created_at
            }
    
    except Exception as e:
        print(f"❌ Error creando departamento: {e}")
        return None


# ============================================================================
# ELECCIÓN (requerida antes de insertar forms)
# ============================================================================

def asegurar_eleccion(
    election_id: Optional[str] = None,
    name: Optional[str] = None,
) -> bool:
    """
    Crea el registro en elections si no existe (FK de forms.election_id).

    Usa ELECTION_ID y ELECTION_YEAR de config.py por defecto.
    """
    eid = election_id or ELECTION_ID

    try:
        with session_scope() as session:
            if session.query(Election).filter_by(id=eid).first():
                return True

            session.add(
                Election(
                    id=eid,
                    name=name or f"Presidenciales 1ª Vuelta {ELECTION_YEAR}",
                    election_date=datetime(ELECTION_YEAR, 5, 29),
                    form_layout_version=str(ELECTION_YEAR),
                    candidate_count=8,
                    status="ACTIVE",
                )
            )
            session.commit()
            print(f"✅ Elección {eid} registrada en BD")
            return True

    except Exception as e:
        print(f"❌ Error asegurando elección: {e}")
        return False


def verificar_geografia_formulario(
    department_code: str,
    municipality_code: str,
) -> Optional[str]:
    """
    Comprueba que departamento y municipio existan antes de insertar un form.

    Returns:
        Mensaje de error si falta algo; None si la geografía es válida.
    """
    try:
        with session_scope() as session:
            dept = session.query(Department).filter_by(
                code=department_code
            ).first()
            if not dept:
                return (
                    f"Departamento {department_code} no está en BD. "
                    "Ejecuta: python scripts/seed_data.py"
                )

            muni = session.query(Municipality).filter_by(
                code=municipality_code,
                department_code=department_code,
            ).first()
            if not muni:
                return (
                    f"Municipio {municipality_code} (depto {department_code}) "
                    "no está en BD. Ejecuta: python scripts/seed_data.py"
                )
            return None

    except Exception as e:
        return f"Error verificando geografía: {e}"


# ============================================================================
# FUNCIONES PARA FORMULARIOS (LA MÁS IMPORTANTE)
# ============================================================================

def crear_formulario(
    form_serial: str,
    election_id: str,
    department_code: str,
    municipality_code: str,
    voting_table_id: int,
    local_path: str,
    file_hash: str,
) -> Optional[int]:
    """
    Crea un nuevo formulario E-14 en la BD.
    
    ESTO ES LO QUE HARÁS CUANDO PERSONA A DESCARGUE PDFs.
    
    Args:
        form_serial: Número único del formulario (ej: "5036317")
        election_id: ID de la elección (ej: "PRES_1V_2022")
        department_code: Código del departamento (ej: "05")
        municipality_code: Código del municipio (ej: "001")
        voting_table_id: ID de la mesa de votación
        local_path: Ruta local donde está guardado (ej: "backend/data/raw/...")
        file_hash: Hash SHA-256 del archivo
    
    Returns:
        int: ID del formulario creado, o None si error
    
    Ejemplo:
        >>> form_id = crear_formulario(
        ...     form_serial="5036317",
        ...     election_id="PRES_1V_2022",
        ...     department_code="05",
        ...     municipality_code="001",
        ...     voting_table_id=1,
        ...     local_path="backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf",
        ...     file_hash="a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9..."
        ... )
        >>> print(f"Formulario creado con ID: {form_id}")
    """
    
    if not asegurar_eleccion(election_id):
        return None

    error_geo = verificar_geografia_formulario(department_code, municipality_code)
    if error_geo:
        print(f"❌ {error_geo}")
        return None

    try:
        with session_scope() as session:
            # Verificar que no existe
            existe = session.query(Form).filter_by(form_serial=form_serial).first()
            if existe:
                print(f"⚠️  Formulario {form_serial} ya existe")
                return existe.id
            
            # Crear
            form = Form(
                form_serial=form_serial,
                election_id=election_id,
                department_code=department_code,
                municipality_code=municipality_code,
                voting_table_id=voting_table_id,
                local_path=local_path,
                file_hash=file_hash,
                download_timestamp=datetime.utcnow(),
                processing_status=ProcessingStatus.PENDING
            )
            
            session.add(form)
            session.commit()
            
            print(f"✅ Formulario {form_serial} creado con ID: {form.id}")
            return form.id
    
    except IntegrityError as e:
        orig = str(getattr(e, "orig", e))
        if "elections" in orig or "election_id" in orig.lower():
            hint = (
                "Falta la elección en tabla elections. "
                "Ejecuta seed_data o vuelve a registrar (asegurar_eleccion)."
            )
        elif "departments" in orig:
            hint = f"Departamento {department_code} no existe en BD (seed_data.py)."
        elif "municipalities" in orig:
            hint = (
                f"Municipio {municipality_code}/{department_code} "
                "no existe en BD (seed_data.py)."
            )
        elif "voting_tables" in orig:
            hint = f"Mesa voting_table_id={voting_table_id} no existe en BD."
        else:
            hint = "Revisa que existan elections, departments, municipalities y voting_tables."
        print(f"❌ Error creando formulario (FK): {orig}\n   💡 {hint}")
        return None

    except Exception as e:
        print(f"❌ Error creando formulario: {e}")
        return None


def actualizar_estado_formulario(
    form_id: int,
    nuevo_estado: str
) -> bool:
    """
    Actualiza el estado de un formulario.
    
    Args:
        form_id: ID del formulario
        nuevo_estado: Nuevo estado (PENDING, EXTRACTED, ANALYZED, FAILED)
    
    Returns:
        bool: True si se actualizó, False si error
    
    Ejemplo:
        >>> actualizar_estado_formulario(1, "EXTRACTED")
        ✅ Formulario 1 actualizado a EXTRACTED
        True
    """
    
    try:
        # Convertir string a enum
        try:
            estado_enum = ProcessingStatus[nuevo_estado]
        except KeyError:
            print(f"❌ Estado inválido: {nuevo_estado}")
            return False
        
        with session_scope() as session:
            # Obtener el formulario
            form = session.query(Form).filter_by(id=form_id).first()
            
            if not form:
                print(f"❌ Formulario {form_id} no existe")
                return False
            
            # Actualizar
            form.processing_status = estado_enum
            form.updated_at = datetime.utcnow()
            session.commit()
            
            print(f"✅ Formulario {form_id} actualizado a {nuevo_estado}")
            return True
    
    except Exception as e:
        print(f"❌ Error actualizando formulario: {e}")
        return False


def actualizar_calidad_formulario(
    form_id: int,
    calidad: str
) -> bool:
    """
    Actualiza la calidad de un formulario.
    
    Args:
        form_id: ID del formulario
        calidad: Calidad (CLEAN, HAS_ISSUES, UNREADABLE)
    
    Returns:
        bool: True si se actualizó, False si error
    
    Ejemplo:
        >>> actualizar_calidad_formulario(1, "HAS_ISSUES")
        ✅ Formulario 1: calidad actualizada a HAS_ISSUES
        True
    """
    
    try:
        try:
            calidad_enum = FormQuality[calidad]
        except KeyError:
            print(f"❌ Calidad inválida: {calidad}")
            return False
        
        with session_scope() as session:
            form = session.query(Form).filter_by(id=form_id).first()
            
            if not form:
                print(f"❌ Formulario {form_id} no existe")
                return False
            
            form.quality = calidad_enum
            form.updated_at = datetime.utcnow()
            session.commit()
            
            print(f"✅ Formulario {form_id}: calidad actualizada a {calidad}")
            return True
    
    except Exception as e:
        print(f"❌ Error actualizando calidad: {e}")
        return False


def actualizar_hash_formulario(
    form_id: int,
    nuevo_hash: str
) -> bool:
    """
    Actualiza el hash de un formulario.
    
    Args:
        form_id: ID del formulario
        nuevo_hash: Nuevo hash SHA-256
    
    Returns:
        bool: True si se actualizó
    """
    
    try:
        with session_scope() as session:
            form = session.query(Form).filter_by(id=form_id).first()
            
            if not form:
                print(f"❌ Formulario {form_id} no existe")
                return False
            
            form.file_hash = nuevo_hash
            form.updated_at = datetime.utcnow()
            session.commit()
            
            print(f"✅ Hash del formulario {form_id} actualizado")
            return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def registrar_error_formulario(
    form_id: int,
    mensaje_error: str
) -> bool:
    """
    Registra un error en un formulario.
    
    Args:
        form_id: ID del formulario
        mensaje_error: Descripción del error
    
    Returns:
        bool: True si se registró
    
    Ejemplo:
        >>> registrar_error_formulario(1, "PDF corrupto")
        ✅ Error registrado para formulario 1
        True
    """
    
    try:
        with session_scope() as session:
            form = session.query(Form).filter_by(id=form_id).first()
            
            if not form:
                return False
            
            form.error_message = mensaje_error
            form.processing_status = ProcessingStatus.FAILED
            form.updated_at = datetime.utcnow()
            session.commit()
            
            print(f"✅ Error registrado para formulario {form_id}")
            return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def eliminar_formulario(form_id: int) -> bool:
    """
    Elimina un formulario de la BD.
    
    CUIDADO: Esto es permanente.
    
    Args:
        form_id: ID del formulario
    
    Returns:
        bool: True si se eliminó
    """
    
    try:
        with session_scope() as session:
            form = session.query(Form).filter_by(id=form_id).first()
            
            if not form:
                print(f"❌ Formulario {form_id} no existe")
                return False
            
            session.delete(form)
            session.commit()
            
            print(f"✅ Formulario {form_id} eliminado")
            return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ============================================================================
# FUNCIONES PARA MUNICIPIOS
# ============================================================================

def crear_municipio(
    dept_code: str,
    muni_code: str,
    muni_name: str
) -> Optional[dict]:
    """
    Crea un nuevo municipio.
    
    Args:
        dept_code: Código del departamento
        muni_code: Código del municipio
        muni_name: Nombre del municipio
    
    Returns:
        dict con los datos, o None si error
    """
    
    try:
        with session_scope() as session:
            existe = session.query(Municipality).filter_by(
                code=muni_code,
                department_code=dept_code
            ).first()
            
            if existe:
                print(f"⚠️  Municipio {muni_code} ya existe en {dept_code}")
                return None
            
            muni = Municipality(
                code=muni_code,
                department_code=dept_code,
                name=muni_name
            )
            
            session.add(muni)
            session.commit()
            
            return {
                "code": muni.code,
                "department_code": muni.department_code,
                "name": muni.name
            }
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================================================
# FUNCIONES PARA ZONAS
# ============================================================================

def crear_zona(
    municipality_code: str,
    municipality_department: str,
    zone_number: str
) -> Optional[int]:
    """
    Crea una nueva zona.
    
    Args:
        municipality_code: Código del municipio
        municipality_department: Código del departamento
        zone_number: Número de zona (ej: "01")
    
    Returns:
        int: ID de la zona creada, o None si error
    """
    
    try:
        with session_scope() as session:
            zona = Zone(
                municipality_code=municipality_code,
                municipality_department=municipality_department,
                zone_number=zone_number
            )
            
            session.add(zona)
            session.commit()
            
            print(f"✅ Zona {zone_number} creada")
            return zona.id
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================================================
# FUNCIONES PARA ESTACIONES
# ============================================================================

def crear_estacion(
    zone_id: int,
    station_number: str,
    name: str,
    address: str = None,
    latitude: float = None,
    longitude: float = None
) -> Optional[int]:
    """
    Crea una nueva estación.
    
    Args:
        zone_id: ID de la zona
        station_number: Número de estación
        name: Nombre (ej: "Escuela XX")
        address: Dirección (opcional)
        latitude: Latitud (opcional, para mapas)
        longitude: Longitud (opcional, para mapas)
    
    Returns:
        int: ID de la estación, o None si error
    """
    
    try:
        with session_scope() as session:
            estacion = Station(
                zone_id=zone_id,
                station_number=station_number,
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude
            )
            
            session.add(estacion)
            session.commit()
            
            print(f"✅ Estación {station_number} creada")
            return estacion.id
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================================================
# FUNCIONES PARA MESAS
# ============================================================================

def crear_mesa(
    station_id: int,
    table_number: str,
    registered_voters: int = None
) -> Optional[int]:
    """
    Crea una nueva mesa de votación.
    
    Args:
        station_id: ID de la estación
        table_number: Número de mesa
        registered_voters: Votantes registrados
    
    Returns:
        int: ID de la mesa, o None si error
    """
    
    try:
        with session_scope() as session:
            mesa = VotingTable(
                station_id=station_id,
                table_number=table_number,
                registered_voters=registered_voters
            )
            
            session.add(mesa)
            session.commit()
            
            print(f"✅ Mesa {table_number} creada")
            return mesa.id
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================================================
# PRUEBAS
# ============================================================================

if __name__ == "__main__":
    """
    Para probar: python backend/src/database/crud.py
    """
    
    print("\n" + "="*70)
    print("🧪 PRUEBAS DE CRUD")
    print("="*70 + "\n")
    
    # PRUEBA 1: Crear un formulario
    print("Prueba 1️⃣: Crear formulario...")
    form_id = crear_formulario(
        form_serial="TEST_NEW_001",
        election_id="PRES_1V_2022",
        department_code="05",
        municipality_code="001",
        voting_table_id=1,
        local_path="backend/data/raw/test/TEST_NEW_001.pdf",
        file_hash="test_hash_123"
    )
    print()
    
    if form_id:
        # PRUEBA 2: Actualizar estado
        print("Prueba 2️⃣: Actualizar estado...")
        actualizar_estado_formulario(form_id, "EXTRACTED")
        print()
        
        # PRUEBA 3: Actualizar calidad
        print("Prueba 3️⃣: Actualizar calidad...")
        actualizar_calidad_formulario(form_id, "HAS_ISSUES")
        print()
        
        # PRUEBA 4: Registrar error
        print("Prueba 4️⃣: Registrar error...")
        registrar_error_formulario(form_id, "Error de prueba")
        print()
        
        # PRUEBA 5: Eliminar
        print("Prueba 5️⃣: Eliminar formulario...")
        eliminar_formulario(form_id)
        print()
    
    print("="*70 + "\n")