"""
queries.py - Funciones para Consultar la Base de Datos

Este módulo contiene TODAS las funciones para LEER datos de la BD.

¿Por qué?
    En lugar de escribir SQL en cada script, tienes funciones reutilizables.
    
    Ejemplo SIN este módulo:
        session = get_session()
        depts = session.query(Department).filter_by(code="05").all()
        
    Ejemplo CON este módulo:
        depts = obtener_departamento_por_codigo("05")
    
    Mucho más limpio y reutilizable.

¿Cómo usarlo?
    from src.database.queries import *
    from src.database.connection import session_scope
    
    # Obtener un departamento
    dept = obtener_departamento_por_codigo("05")
    print(dept.name)  # "Antioquia"
"""

import sys
from pathlib import Path
from typing import List, Optional

# Importar
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.schema import (
    Department,
    Municipality,
    Zone,
    Station,
    VotingTable,
    Form,
    ProcessingStatus,
    FormQuality,
)
from src.database.connection import session_scope

# ============================================================================
# FUNCIONES DE DEPARTAMENTOS
# ============================================================================

def obtener_todos_departamentos() -> List[Department]:
    """
    Obtiene TODOS los departamentos.
    
    Returns:
        List[Department]: Lista de todos los departamentos
    
    Ejemplo:
        >>> depts = obtener_todos_departamentos()
        >>> for dept in depts:
        ...     print(f"{dept.code}: {dept.name}")
        01: Amazonas
        02: Antioquia
        ...
    """
    with session_scope() as session:
        depts = session.query(Department).order_by(Department.code).all()
        # Convertir a diccionarios para que no pierdan datos fuera de sesión
        return [
            {
                "code": d.code,
                "name": d.name,
                "created_at": d.created_at
            }
            for d in depts
        ]


def obtener_departamento_por_codigo(dept_code: str) -> Optional[dict]:
    """
    Obtiene UN departamento por su código.
    
    Args:
        dept_code: Código del departamento (ej: "05")
    
    Returns:
        dict o None: Datos del departamento o None si no existe
    
    Ejemplo:
        >>> dept = obtener_departamento_por_codigo("05")
        >>> print(dept["name"])
        Antioquia
    """
    with session_scope() as session:
        dept = session.query(Department).filter_by(code=dept_code).first()
        
        if not dept:
            return None
        
        return {
            "code": dept.code,
            "name": dept.name,
            "created_at": dept.created_at
        }


def obtener_departamento_por_nombre(nombre: str) -> Optional[dict]:
    """
    Obtiene UN departamento por su nombre.
    
    Args:
        nombre: Nombre del departamento (ej: "Antioquia")
    
    Returns:
        dict o None: Datos del departamento o None si no existe
    
    Ejemplo:
        >>> dept = obtener_departamento_por_nombre("Antioquia")
        >>> print(dept["code"])
        05
    """
    with session_scope() as session:
        dept = session.query(Department).filter_by(name=nombre).first()
        
        if not dept:
            return None
        
        return {
            "code": dept.code,
            "name": dept.name,
            "created_at": dept.created_at
        }


def contar_departamentos() -> int:
    """
    Cuenta cuántos departamentos hay.
    
    Returns:
        int: Cantidad de departamentos
    
    Ejemplo:
        >>> cantidad = contar_departamentos()
        >>> print(cantidad)
        32
    """
    with session_scope() as session:
        return session.query(Department).count()


# ============================================================================
# FUNCIONES DE MUNICIPIOS
# ============================================================================

def obtener_municipios_por_departamento(dept_code: str) -> List[dict]:
    """
    Obtiene TODOS los municipios de un departamento.
    
    Args:
        dept_code: Código del departamento (ej: "05")
    
    Returns:
        List[dict]: Lista de municipios
    
    Ejemplo:
        >>> munis = obtener_municipios_por_departamento("05")
        >>> for m in munis:
        ...     print(f"{m['code']}: {m['name']}")
        001: Cartagena
        109: Turbaco
    """
    with session_scope() as session:
        munis = session.query(Municipality).filter_by(
            department_code=dept_code
        ).order_by(Municipality.code).all()
        
        return [
            {
                "code": m.code,
                "department_code": m.department_code,
                "name": m.name,
                "created_at": m.created_at
            }
            for m in munis
        ]


def obtener_municipio(dept_code: str, muni_code: str) -> Optional[dict]:
    """
    Obtiene UN municipio específico.
    
    Args:
        dept_code: Código del departamento
        muni_code: Código del municipio
    
    Returns:
        dict o None: Datos del municipio o None si no existe
    
    Ejemplo:
        >>> muni = obtener_municipio("05", "001")
        >>> print(muni["name"])
        Cartagena
    """
    with session_scope() as session:
        muni = session.query(Municipality).filter_by(
            code=muni_code,
            department_code=dept_code
        ).first()
        
        if not muni:
            return None
        
        return {
            "code": muni.code,
            "department_code": muni.department_code,
            "name": muni.name,
            "created_at": muni.created_at
        }


def contar_municipios() -> int:
    """
    Cuenta cuántos municipios hay en total.
    
    Returns:
        int: Cantidad de municipios
    """
    with session_scope() as session:
        return session.query(Municipality).count()


# ============================================================================
# FUNCIONES DE ZONAS
# ============================================================================

def obtener_zonas_por_municipio(dept_code: str, muni_code: str) -> List[dict]:
    """
    Obtiene todas las zonas de un municipio.
    
    Args:
        dept_code: Código del departamento
        muni_code: Código del municipio
    
    Returns:
        List[dict]: Lista de zonas
    
    Ejemplo:
        >>> zonas = obtener_zonas_por_municipio("05", "001")
        >>> for z in zonas:
        ...     print(f"Zona {z['zone_number']}")
    """
    with session_scope() as session:
        zonas = session.query(Zone).filter_by(
            municipality_code=muni_code,
            municipality_department=dept_code
        ).order_by(Zone.zone_number).all()
        
        return [
            {
                "id": z.id,
                "zone_number": z.zone_number,
                "municipality_code": z.municipality_code,
                "created_at": z.created_at
            }
            for z in zonas
        ]


def contar_zonas() -> int:
    """Cuenta cuántas zonas hay."""
    with session_scope() as session:
        return session.query(Zone).count()


# ============================================================================
# FUNCIONES DE ESTACIONES
# ============================================================================

def obtener_estaciones_por_zona(zone_id: int) -> List[dict]:
    """
    Obtiene todas las estaciones de una zona.
    
    Args:
        zone_id: ID de la zona
    
    Returns:
        List[dict]: Lista de estaciones
    """
    with session_scope() as session:
        estaciones = session.query(Station).filter_by(zone_id=zone_id).all()
        
        return [
            {
                "id": s.id,
                "station_number": s.station_number,
                "name": s.name,
                "address": s.address,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "created_at": s.created_at
            }
            for s in estaciones
        ]


def obtener_estacion(station_id: int) -> Optional[dict]:
    """
    Obtiene UNA estación específica.
    
    Args:
        station_id: ID de la estación
    
    Returns:
        dict o None: Datos de la estación
    """
    with session_scope() as session:
        estacion = session.query(Station).filter_by(id=station_id).first()
        
        if not estacion:
            return None
        
        return {
            "id": estacion.id,
            "station_number": estacion.station_number,
            "name": estacion.name,
            "address": estacion.address,
            "latitude": estacion.latitude,
            "longitude": estacion.longitude,
            "created_at": estacion.created_at
        }


def contar_estaciones() -> int:
    """Cuenta cuántas estaciones hay."""
    with session_scope() as session:
        return session.query(Station).count()


# ============================================================================
# FUNCIONES DE MESAS
# ============================================================================

def obtener_mesas_por_estacion(station_id: int) -> List[dict]:
    """
    Obtiene todas las mesas de una estación.
    
    Args:
        station_id: ID de la estación
    
    Returns:
        List[dict]: Lista de mesas
    
    Ejemplo:
        >>> mesas = obtener_mesas_por_estacion(1)
        >>> for m in mesas:
        ...     print(f"Mesa {m['table_number']}: {m['registered_voters']} votantes")
    """
    with session_scope() as session:
        mesas = session.query(VotingTable).filter_by(station_id=station_id).all()
        
        return [
            {
                "id": m.id,
                "table_number": m.table_number,
                "station_id": m.station_id,
                "registered_voters": m.registered_voters,
                "created_at": m.created_at
            }
            for m in mesas
        ]


def obtener_mesa(table_id: int) -> Optional[dict]:
    """
    Obtiene UNA mesa específica.
    
    Args:
        table_id: ID de la mesa
    
    Returns:
        dict o None: Datos de la mesa
    """
    with session_scope() as session:
        mesa = session.query(VotingTable).filter_by(id=table_id).first()
        
        if not mesa:
            return None
        
        return {
            "id": mesa.id,
            "table_number": mesa.table_number,
            "station_id": mesa.station_id,
            "registered_voters": mesa.registered_voters,
            "created_at": mesa.created_at
        }


def contar_mesas() -> int:
    """Cuenta cuántas mesas hay."""
    with session_scope() as session:
        return session.query(VotingTable).count()


# ============================================================================
# FUNCIONES DE FORMULARIOS (FORMS)
# ============================================================================

def obtener_todos_formularios(limite: int = 100) -> List[dict]:
    """
    Obtiene los primeros N formularios.
    
    Args:
        limite: Cuántos formularios traer (default: 100)
    
    Returns:
        List[dict]: Lista de formularios
    
    Ejemplo:
        >>> forms = obtener_todos_formularios(10)
        >>> for f in forms:
        ...     print(f"{f['form_serial']}: {f['processing_status']}")
    """
    with session_scope() as session:
        forms = session.query(Form).limit(limite).all()
        
        return [
            {
                "id": f.id,
                "form_serial": f.form_serial,
                "election_id": f.election_id,
                "department_code": f.department_code,
                "municipality_code": f.municipality_code,
                "local_path": f.local_path,
                "file_hash": f.file_hash,
                "processing_status": f.processing_status.value if f.processing_status else None,
                "quality": f.quality.value if f.quality else None,
                "created_at": f.created_at
            }
            for f in forms
        ]


def obtener_formulario_por_serial(form_serial: str) -> Optional[dict]:
    """
    Obtiene UN formulario por su número serial.
    
    Args:
        form_serial: Número único del formulario (ej: "5036317")
    
    Returns:
        dict o None: Datos del formulario
    
    Ejemplo:
        >>> form = obtener_formulario_por_serial("5036317")
        >>> print(form["local_path"])
        backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf
    """
    with session_scope() as session:
        form = session.query(Form).filter_by(form_serial=form_serial).first()
        
        if not form:
            return None
        
        return {
            "id": form.id,
            "form_serial": form.form_serial,
            "election_id": form.election_id,
            "department_code": form.department_code,
            "municipality_code": form.municipality_code,
            "local_path": form.local_path,
            "file_hash": form.file_hash,
            "processing_status": form.processing_status.value if form.processing_status else None,
            "quality": form.quality.value if form.quality else None,
            "error_message": form.error_message,
            "created_at": form.created_at,
            "updated_at": form.updated_at
        }


def obtener_formularios_por_estado(estado: str) -> List[dict]:
    """
    Obtiene TODOS los formularios en un estado específico.
    
    Args:
        estado: Estado (PENDING, EXTRACTED, ANALYZED, FAILED)
    
    Returns:
        List[dict]: Lista de formularios
    
    Ejemplo:
        >>> pending = obtener_formularios_por_estado("PENDING")
        >>> print(f"Hay {len(pending)} pendientes de procesar")
    """
    try:
        # Convertir string a enum
        estado_enum = ProcessingStatus[estado]
    except KeyError:
        return []
    
    with session_scope() as session:
        forms = session.query(Form).filter_by(processing_status=estado_enum).all()
        
        return [
            {
                "id": f.id,
                "form_serial": f.form_serial,
                "local_path": f.local_path,
                "processing_status": f.processing_status.value,
                "created_at": f.created_at
            }
            for f in forms
        ]


def contar_formularios() -> int:
    """Cuenta cuántos formularios hay."""
    with session_scope() as session:
        return session.query(Form).count()


def contar_formularios_por_estado(estado: str) -> int:
    """
    Cuenta formularios en un estado específico.
    
    Args:
        estado: Estado (PENDING, EXTRACTED, ANALYZED, FAILED)
    
    Returns:
        int: Cantidad
    
    Ejemplo:
        >>> pending = contar_formularios_por_estado("PENDING")
        >>> print(f"Pendientes: {pending}")
    """
    try:
        estado_enum = ProcessingStatus[estado]
    except KeyError:
        return 0
    
    with session_scope() as session:
        return session.query(Form).filter_by(processing_status=estado_enum).count()


# ============================================================================
# FUNCIONES ESTADÍSTICAS
# ============================================================================

def obtener_estadisticas_generales() -> dict:
    """
    Obtiene estadísticas generales de la BD.
    
    Returns:
        dict con todas las cantidades
    
    Ejemplo:
        >>> stats = obtener_estadisticas_generales()
        >>> print(f"Departamentos: {stats['total_departamentos']}")
        >>> print(f"PDFs pendientes: {stats['formularios_pendientes']}")
    """
    return {
        "total_departamentos": contar_departamentos(),
        "total_municipios": contar_municipios(),
        "total_zonas": contar_zonas(),
        "total_estaciones": contar_estaciones(),
        "total_mesas": contar_mesas(),
        "total_formularios": contar_formularios(),
        "formularios_pendientes": contar_formularios_por_estado("PENDING"),
        "formularios_extraidos": contar_formularios_por_estado("EXTRACTED"),
        "formularios_analizados": contar_formularios_por_estado("ANALYZED"),
        "formularios_fallidos": contar_formularios_por_estado("FAILED"),
    }


# ============================================================================
# PRUEBAS
# ============================================================================

if __name__ == "__main__":
    """
    Para probar este módulo:
    python backend/src/database/queries.py
    """
    
    print("\n" + "="*70)
    print("🧪 PRUEBAS DE QUERIES")
    print("="*70 + "\n")
    
    # PRUEBA 1: Obtener departamentos
    print("Prueba 1️⃣: Obtener departamentos...")
    depts = obtener_todos_departamentos()
    print(f"   ✅ Total: {len(depts)}")
    print(f"   Primeros 3:")
    for d in depts[:3]:
        print(f"      • {d['code']}: {d['name']}")
    print()
    
    # PRUEBA 2: Obtener un departamento
    print("Prueba 2️⃣: Obtener departamento específico...")
    dept = obtener_departamento_por_codigo("05")
    print(f"   ✅ {dept['code']}: {dept['name']}\n")
    
    # PRUEBA 3: Obtener municipios de un depto
    print("Prueba 3️⃣: Obtener municipios de Antioquia...")
    munis = obtener_municipios_por_departamento("05")
    print(f"   ✅ Total: {len(munis)}")
    for m in munis:
        print(f"      • {m['code']}: {m['name']}")
    print()
    
    # PRUEBA 4: Estadísticas
    print("Prueba 4️⃣: Estadísticas generales...")
    stats = obtener_estadisticas_generales()
    print(f"   ✅ Estadísticas:")
    for key, value in stats.items():
        print(f"      • {key}: {value}")
    print()
    
    print("="*70 + "\n")