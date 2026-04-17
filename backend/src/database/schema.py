"""
schema.py - Estructura de la Base de Datos E14 Challenge

Este archivo define CÓMO se ven las tablas en la BD.

Analogía: Es como el "plano arquitectónico" de la BD.
Si quieres saber qué datos guarda cada tabla, lo buscas aquí.

Usamos SQLAlchemy, que es un "intermediario" entre Python y la BD.
Permite escribir código Python en lugar de SQL directo.
"""

from sqlalchemy import (
    create_engine,           # Conecta a la BD
    Column,                  # Define columnas en tablas
    Integer, String, Text, DateTime, Float, Enum,  # Tipos de datos
    ForeignKey,              # Referencia a otra tabla
    and_,                    # Para join conditions complejas
    func,                    # Funciones SQL
    ForeignKeyConstraint,    # Constraints complejos de foreign keys
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session, foreign
from datetime import datetime
import enum
from pathlib import Path

# Importar configuración
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DATABASE_URL

# ============================================================================
# Base para todos los modelos
# ============================================================================

Base = declarative_base()

# ============================================================================
# ENUMERACIONES (Tipos especiales de datos)
# ============================================================================

class ProcessingStatus(enum.Enum):
    """Estados posibles de un formulario"""
    PENDING = "PENDING"           # Descargado, esperando procesar
    EXTRACTED = "EXTRACTED"       # OCR completado
    ANALYZED = "ANALYZED"         # Anomalías detectadas
    FAILED = "FAILED"             # Error en el proceso


class FormQuality(enum.Enum):
    """Calidad de la extracción OCR"""
    CLEAN = "CLEAN"               # Sin problemas
    HAS_ISSUES = "HAS_ISSUES"     # Tiene algunos problemas
    UNREADABLE = "UNREADABLE"     # No se pudo leer

# ============================================================================
# TABLA 1: DEPARTAMENTOS
# ============================================================================

class Department(Base):
    """
    Representación de los 33 departamentos + Bogotá D.C. de Colombia.
    
    Ejemplo de fila:
    ┌─────────────────────────┐
    │ code │ name              │
    ├──────┼───────────────────┤
    │ "05" │ "Antioquia"       │
    │ "11" │ "Bogotá D.C."     │
    │ "76" │ "Valle del Cauca" │
    └─────────────────────────┘
    """
    
    __tablename__ = "departments"  # Nombre de la tabla en la BD
    
    # Columnas
    code = Column(String(2), primary_key=True)  # "05", "11", "76", etc.
    name = Column(String(100), nullable=False, unique=True)  # "Antioquia"
    created_at = Column(DateTime, default=datetime.utcnow)  # Cuándo se creó
    
    # Relaciones (para acceso desde código Python)
    municipalities = relationship("Municipality", back_populates="department")
    forms = relationship("Form", back_populates="department")
    
    def __repr__(self):
        """Cómo se ve cuando lo imprimes"""
        return f"<Department {self.code}: {self.name}>"


# ============================================================================
# TABLA 2: MUNICIPIOS
# ============================================================================

class Municipality(Base):
    """
    Municipios dentro de cada departamento.
    
    Ejemplo de filas:
    ┌──────┬──────────────────────┬──────────────┐
    │ code │ department_code      │ name         │
    ├──────┼──────────────────────┼──────────────┤
    │ "001"│ "05"                 │ "Medellín"   │
    │ "002"│ "05"                 │ "Bello"      │
    │ "001"│ "11"                 │ "Bogotá"     │
    └──────┴──────────────────────┴──────────────┘
    
    Nota: El code "001" aparece en varios departments.
    Por eso usamos COMPOSITE KEY: (code, department_code)
    """
    
    __tablename__ = "municipalities"
    
    code = Column(String(3), primary_key=True)
    department_code = Column(
        String(2),
        ForeignKey("departments.code"),  # Referencia a departments
        primary_key=True
    )
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    department = relationship("Department", back_populates="municipalities")
    zones = relationship(
        "Zone",
        back_populates="municipality",
        foreign_keys="[Zone.municipality_code, Zone.municipality_department]",
        primaryjoin="and_(Zone.municipality_code==Municipality.code, Zone.municipality_department==Municipality.department_code)"
    )
    forms = relationship(
        "Form",
        back_populates="municipality",
        foreign_keys="[Form.municipality_code, Form.department_code]",
        primaryjoin="and_(Form.municipality_code==Municipality.code, Form.department_code==Municipality.department_code)",
        overlaps="department,forms"
    )
    
    def __repr__(self):
        return f"<Municipality {self.code} ({self.department_code}): {self.name}>"


# ============================================================================
# TABLA 3: ZONAS
# ============================================================================

class Zone(Base):
    """
    Zona de votación dentro de un municipio.
    
    Una zona es una subdivisión geográfica dentro de un municipio.
    Por ejemplo, Bogotá puede tener 20 zonas.
    
    Ejemplo:
    ┌────┬──────────────────────────┬──────────┐
    │ id │ municipality_code        │ zone_num │
    ├────┼──────────────────────────┼──────────┤
    │ 1  │ "001" (Bogotá, dept 11) │ "01"     │
    │ 2  │ "001" (Bogotá, dept 11) │ "02"     │
    └────┴──────────────────────────┴──────────┘
    """
    
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    municipality_code = Column(
        String(3),
        ForeignKey("municipalities.code"),
        nullable=False
    )
    municipality_department = Column(
        String(2),
        ForeignKey("municipalities.department_code"),
        nullable=False
    )
    zone_number = Column(String(3), nullable=False)  # "01", "02", etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    municipality = relationship(
        "Municipality",
        back_populates="zones",
        foreign_keys="[Zone.municipality_code, Zone.municipality_department]",
        primaryjoin="and_(Zone.municipality_code==Municipality.code, Zone.municipality_department==Municipality.department_code)"
    )
    stations = relationship("Station", back_populates="zone")
    
    def __repr__(self):
        return f"<Zone {self.zone_number} in {self.municipality_code}>"


# ============================================================================
# TABLA 4: PUESTOS (Estaciones de votación)
# ============================================================================

class Station(Base):
    """
    Puesto de votación (estación).
    Es un lugar físico donde se vota: una escuela, centro comunitario, etc.
    
    Una estación tiene múltiples mesas.
    
    Ejemplo:
    ┌────┬─────────┬──────────────────────────┐
    │ id │ zone_id │ name                     │
    ├────┼─────────┼──────────────────────────┤
    │ 1  │ 1       │ "Escuela La Esperanza"   │
    │ 2  │ 1       │ "Centro Comunitario #5"  │
    └────┴─────────┴──────────────────────────┘
    """
    
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    station_number = Column(String(3), nullable=False)  # "001", "002"
    name = Column(String(200))  # Nombre de la escuela o lugar
    address = Column(String(300))  # Dirección
    latitude = Column(Float)  # Para hacer mapas después
    longitude = Column(Float)  # Para hacer mapas después
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    zone = relationship("Zone", back_populates="stations")
    tables = relationship("VotingTable", back_populates="station")
    
    def __repr__(self):
        return f"<Station {self.station_number}: {self.name}>"


# ============================================================================
# TABLA 5: MESAS (Tablas de votación)
# ============================================================================

class VotingTable(Base):
    """
    Una mesa de votación dentro de un puesto.
    
    Cada mesa tiene un formulario E-14 asociado.
    Una estación puede tener 3-5 mesas.
    
    Ejemplo:
    ┌────┬────────────┬──────────┬──────────────────┐
    │ id │ station_id │ table_no │ registered_voters│
    ├────┼────────────┼──────────┼──────────────────┤
    │ 1  │ 1          │ "031"    │ 400              │
    │ 2  │ 1          │ "032"    │ 380              │
    └────┴────────────┴──────────┴──────────────────┘
    """
    
    __tablename__ = "voting_tables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    table_number = Column(String(3), nullable=False)  # "031", "032"
    registered_voters = Column(Integer)  # Cuánta gente podía votar en esa mesa
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    station = relationship("Station", back_populates="tables")
    forms = relationship("Form", back_populates="voting_table")
    
    def __repr__(self):
        return f"<VotingTable {self.table_number} in Station {self.station_id}>"


# ============================================================================
# TABLA 6: FORMULARIOS E-14 (LA MÁS IMPORTANTE PARA TI)
# ============================================================================

class Form(Base):
    """
    Formulario E-14 descargado.
    
    Esta es LA tabla central. Representa cada PDF descargado.
    
    Ejemplo de fila:
    ┌─────────────┬──────────────┬──────────────┬─────────────────┬──────────┐
    │ form_serial │ election_id  │ local_path   │ file_hash       │ status   │
    ├─────────────┼──────────────┼──────────────┼─────────────────┼──────────┤
    │ "5036317"   │ "PRES_1V_22" │ "backend/... │ "a3c5f7e2d..."  │ PENDING  │
    │ "5036318"   │ "PRES_1V_22" │ "backend/... │ "b4d6e8f2e..."  │ PENDING  │
    └─────────────┴──────────────┴──────────────┴─────────────────┴──────────┘
    """
    
    __tablename__ = "forms"
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    form_serial = Column(String(50), unique=True, nullable=False, index=True)
    election_id = Column(String(20), nullable=False, index=True)
    
    # Ubicación geográfica
    department_code = Column(String(2), ForeignKey("departments.code"), nullable=False, index=True)
    municipality_code = Column(String(3), nullable=False, index=True)
    voting_table_id = Column(Integer, ForeignKey("voting_tables.id"), nullable=False)
    
    __table_args__ = (
        # ForeignKey constraint para municipality (composite key)
        # Form.municipality_code y Form.department_code -> Municipality.(code, department_code)
        ForeignKeyConstraint(['municipality_code', 'department_code'], 
                             ['municipalities.code', 'municipalities.department_code']),
    )
    
    # Almacenamiento (IMPORTANTÍSIMO para ti)
    local_path = Column(String(500), nullable=False)  # Dónde está el PDF en tu disco
    file_hash = Column(String(64))  # SHA-256 del archivo
    
    # Procesamiento
    download_timestamp = Column(DateTime, nullable=False)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    quality = Column(Enum(FormQuality), default=None, nullable=True)
    
    # Metadatos
    error_message = Column(Text)  # Si falla, qué error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    department = relationship("Department", back_populates="forms")
    municipality = relationship(
        "Municipality",
        back_populates="forms",
        foreign_keys="[Form.municipality_code, Form.department_code]",
        primaryjoin="and_(Form.municipality_code==Municipality.code, Form.department_code==Municipality.department_code)",
        overlaps="department,forms"
    )
    voting_table = relationship("VotingTable", back_populates="forms")
    
    def __repr__(self):
        return f"<Form {self.form_serial} - {self.processing_status.value}>"


# ============================================================================
# FUNCIONES PARA CREAR Y CONECTAR
# ============================================================================

def create_engine_connection(database_url: str):
    """
    Crea la conexión a la BD.
    
    Args:
        database_url: URL de la BD (ej: "sqlite:///data/e14.db")
        
    Returns:
        Engine (objeto de conexión)
    """
    engine = create_engine(database_url, echo=False)
    return engine


def create_all_tables(database_url: str):
    """
    Crea todas las tablas en la BD.
    
    IMPORTANTE: Solo ejecuta esto UNA VEZ al principio.
    
    Args:
        database_url: URL de la BD
    """
    engine = create_engine_connection(database_url)
    Base.metadata.create_all(engine)
    print(f"✅ Tablas creadas en: {database_url}")
    return engine


# ============================================================================
# PRUEBAS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 VERIFICANDO SCHEMA")
    print("="*60)
    print(f"\nURL de BD: {DATABASE_URL}")
    print("\nTablas definidas:")
    for table in Base.metadata.tables.keys():
        print(f"  ✅ {table}")
    print("\n" + "="*60 + "\n")