"""
schema.py - Estructura de la Base de Datos E14 Challenge

Este archivo define CÓMO se ven las tablas en la BD.

Analogía: Es como el "plano arquitectónico" de la BD.
Si quieres saber qué datos guarda cada tabla, lo buscas aquí.

Usamos SQLAlchemy, que es un "intermediario" entre Python y la BD.
Permite escribir código Python en lugar de SQL directo.
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
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
    """Estados del formulario durante el pipeline"""
    PENDING = "PENDING"           # Descargado, esperando OCR
    EXTRACTED = "EXTRACTED"       # OCR completado
    ANALYZED = "ANALYZED"         # Anomalías detectadas
    FAILED = "FAILED"             # Error en el proceso
 
 
class FormQuality(enum.Enum):
    """Calidad de la extracción OCR"""
    CLEAN = "CLEAN"               # Sin problemas (confianza > 85%)
    HAS_ISSUES = "HAS_ISSUES"     # Tiene problemas menores
    UNREADABLE = "UNREADABLE"     # No se pudo leer
 
 
class FieldIssueTag(enum.Enum):
    """Tipos de problemas encontrados en campos"""
    CLEAN = "CLEAN"
    SCRATCH = "SCRATCH"
    OVERWRITTEN = "OVERWRITTEN"
    ILLEGIBLE = "ILLEGIBLE"
    AMBIGUOUS = "AMBIGUOUS"
    SMUDGED = "SMUDGED"
    ASTERISK_NOTATION = "ASTERISK_NOTATION"
    EMPTY_FIELD = "EMPTY_FIELD"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    MULTIPLE_VALUES = "MULTIPLE_VALUES"
 
 
class AnomalyType(enum.Enum):
    """Tipos de anomalías detectadas"""
    ARITHMETIC_MISMATCH = "ARITHMETIC_MISMATCH"           # Suma no cuadra
    NIVELACION_MISMATCH = "NIVELACION_MISMATCH"           # Sufragantes ≠ Votos
    HIGH_ISSUE_DENSITY = "HIGH_ISSUE_DENSITY"             # 3+ campos con problemas
    ILLEGIBLE_CRITICAL = "ILLEGIBLE_CRITICAL"             # Campos ilegibles críticos
    ZERO_VOTE_ANOMALY = "ZERO_VOTE_ANOMALY"               # Candidato sin votos en tabla grande
    OVER_PARTICIPATION = "OVER_PARTICIPATION"              # Votos > sufragantes
    DISTRIBUTION_SHIFT = "DISTRIBUTION_SHIFT"             # Diferente a otras mesas
    PARTICIPATION_OUTLIER = "PARTICIPATION_OUTLIER"        # Participación anormal
    BENFORD_DEVIATION = "BENFORD_DEVIATION"               # Viola Ley de Benford
    PRECONTEO_DISCREPANCY = "PRECONTEO_DISCREPANCY"       # Diferencia con oficial
 
 
class AnomalySeverity(enum.Enum):
    """Niveles de severidad de anomalías"""
    INFO = "INFO"                 # 🔵 Información, sin acción necesaria
    WARNING = "WARNING"           # 🟡 Notable, vale la pena investigar
    ALERT = "ALERT"               # 🟠 Significativo, requiere atención
    CRITICAL = "CRITICAL"         # 🔴 Severo, acción urgente
 
 
# ============================================================================
# TABLA 1: ELECTIONS (Configuración de elecciones)
# ============================================================================
 
class Election(Base):
    """
    Cada elección es una configuración independiente.
    Ejemplo: PRES_1V_2022, PRES_1V_2026, CONGRESS_2026, etc.
    
    Esto permite tener MÚLTIPLES ELECCIONES en la misma BD.
    
    Ejemplo:
    ┌─────────────────┬──────────────────┬─────────────────┐
    │ id              │ name             │ election_date   │
    ├─────────────────┼──────────────────┼─────────────────┤
    │ "PRES_1V_2022"  │ "Presidenciales" │ "2022-05-29"    │
    │ "PRES_1V_2026"  │ "Presidenciales" │ "2026-05-31"    │
    └─────────────────┴──────────────────┴─────────────────┘
    """
    
    __tablename__ = "elections"
    
    id = Column(String(30), primary_key=True)  # "PRES_1V_2022", "CONGRESS_2026"
    name = Column(String(100), nullable=False)  # "Presidenciales 1ª Vuelta 2022"
    election_date = Column(DateTime, nullable=False)
    portal_url = Column(String(500))  # URL del portal de descarga
    form_layout_version = Column(String(20))  # "2022", "2026"
    candidate_count = Column(Integer)  # Cuántos candidatos (8 para 2022)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, ARCHIVED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    candidates = relationship("ElectionCandidate", back_populates="election", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="election")
    
    def __repr__(self):
        return f"<Election {self.id}: {self.name}>"
 
 
# ============================================================================
# TABLA 2: ELECTION_CANDIDATES (Candidatos por elección)
# ============================================================================
 
class ElectionCandidate(Base):
    """
    Los candidatos VARÍAN por elección.
    2022 tenía 8 candidatos presidenciales.
    2026 tendrá otros.
    
    Esto permite que el prompt de Gemini sea dinámico.
    
    Ejemplo:
    ┌────┬─────────────────┬──────────┬────────────────────┐
    │ id │ election_id     │ position │ name               │
    ├────┼─────────────────┼──────────┼────────────────────┤
    │ 1  │ "PRES_1V_2022"  │ 1        │ "Rodolfo Hernández"│
    │ 2  │ "PRES_1V_2022"  │ 2        │ "John Milton..."   │
    │ 3  │ "PRES_1V_2026"  │ 1        │ "Candidato X"      │
    └────┴─────────────────┴──────────┴────────────────────┘
    """
    
    __tablename__ = "election_candidates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    election_id = Column(String(30), ForeignKey("elections.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)  # Orden en la papeleta: 1, 2, 3...
    candidate_name = Column(String(200), nullable=False)
    party = Column(String(100))
    coalition = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    election = relationship("Election", back_populates="candidates")
    candidate_votes = relationship("CandidateVotes", back_populates="election_candidate")
    
    def __repr__(self):
        return f"<ElectionCandidate {self.position}: {self.candidate_name}>"
 
 
# ============================================================================
# TABLA 3: DEPARTMENTS (Departamentos de Colombia)
# ============================================================================
 
class Department(Base):
    """
    Los 33 departamentos + Bogotá D.C.
    
    Ejemplo:
    ┌──────┬─────────────────────┐
    │ code │ name                │
    ├──────┼─────────────────────┤
    │ "05" │ "Antioquia"         │
    │ "11" │ "Bogotá D.C."       │
    │ "76" │ "Valle del Cauca"   │
    └──────┴─────────────────────┘
    """
    
    __tablename__ = "departments"
    
    code = Column(String(2), primary_key=True)  # DANE code
    name = Column(String(100), nullable=False, unique=True)
    geojson = Column(Text)  # Para mapas (opcional, por ahora)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    municipalities = relationship("Municipality", back_populates="department", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="department")
    
    def __repr__(self):
        return f"<Department {self.code}: {self.name}>"
 
 
# ============================================================================
# TABLA 4: MUNICIPALITIES (Municipios)
# ============================================================================
 
class Municipality(Base):
    """
    Municipios dentro de departamentos.
    
    NOTA: El code "001" aparece en VARIOS departamentos.
    Por eso usamos COMPOSITE PRIMARY KEY: (code, department_code)
    
    Ejemplo:
    ┌──────┬──────────────────┬────────────┐
    │ code │ department_code  │ name       │
    ├──────┼──────────────────┼────────────┤
    │ "001"│ "05"             │ "Medellín" │
    │ "001"│ "11"             │ "Bogotá"   │
    └──────┴──────────────────┴────────────┘
    """
    
    __tablename__ = "municipalities"
    
    code = Column(String(3), primary_key=True)
    department_code = Column(
        String(2),
        ForeignKey("departments.code"),
        primary_key=True,
        index=True
    )
    name = Column(String(100), nullable=False)
    geojson = Column(Text)  # Para mapas (opcional)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    department = relationship("Department", back_populates="municipalities")
    zones = relationship("Zone", back_populates="municipality", cascade="all, delete-orphan")
    forms = relationship(
        "Form",
        back_populates="municipality",
        foreign_keys="[Form.municipality_code, Form.department_code]",
        overlaps="department,forms"
    )
    
    def __repr__(self):
        return f"<Municipality {self.code} ({self.department_code}): {self.name}>"
 
 
# ============================================================================
# TABLA 5: ZONES (Zonas de votación)
# ============================================================================
 
class Zone(Base):
    """
    Una zona es una subdivisión dentro de un municipio.
    Por ejemplo, Bogotá está dividida en zonas.
    
    Ejemplo:
    ┌────┬──────────────────────────┬──────────┐
    │ id │ municipality_code        │ zone_num │
    ├────┼──────────────────────────┼──────────┤
    │ 1  │ "001" (Bogotá, Bogotá)   │ "01"     │
    │ 2  │ "001" (Bogotá, Bogotá)   │ "02"     │
    └────┴──────────────────────────┴──────────┘
    """
    
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    municipality_code = Column(String(3), nullable=False, index=True)
    municipality_department = Column(String(2), nullable=False, index=True)
    zone_number = Column(String(3), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ["municipality_code", "municipality_department"],
            ["municipalities.code", "municipalities.department_code"],
        ),
        Index("idx_zone_muni", "municipality_code", "municipality_department"),
    )
    
    # Relaciones
    municipality = relationship("Municipality", back_populates="zones")
    stations = relationship("Station", back_populates="zone", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Zone {self.zone_number} in {self.municipality_code}>"
 
 
# ============================================================================
# TABLA 6: STATIONS (Puestos de votación)
# ============================================================================
 
class Station(Base):
    """
    Un puesto es un lugar físico donde se vota.
    Ejemplo: "Escuela La Esperanza", "Centro Comunitario #5"
    
    Una estación puede tener 3-5 mesas.
    
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
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    station_number = Column(String(3), nullable=False)  # "001", "002"
    name = Column(String(200))  # Nombre del lugar
    address = Column(String(300))  # Dirección
    latitude = Column(Float)  # Para mapas
    longitude = Column(Float)  # Para mapas
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    zone = relationship("Zone", back_populates="stations")
    voting_tables = relationship("VotingTable", back_populates="station", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Station {self.station_number}: {self.name}>"
 
 
# ============================================================================
# TABLA 7: VOTING_TABLES (Mesas de votación)
# ============================================================================
 
class VotingTable(Base):
    """
    Una mesa es donde votan los ciudadanos.
    Cada mesa tiene un formulario E-14.
    
    Una estación puede tener múltiples mesas (por ej: 031, 032, 033)
    
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
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    table_number = Column(String(3), nullable=False)  # "031", "032"
    registered_voters = Column(Integer)  # Cuánta gente está registrada
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    station = relationship("Station", back_populates="voting_tables")
    forms = relationship("Form", back_populates="voting_table")
    
    def __repr__(self):
        return f"<VotingTable {self.table_number} in Station {self.station_id}>"
 
 
# ============================================================================
# TABLA 8: FORMS (¡LA TABLA MÁS IMPORTANTE PARA TI!)
# ============================================================================
 
class Form(Base):
    """
    ESTA ES LA TABLA DONDE TU AMIGO REGISTRA LOS PDFS DESCARGADOS.
    
    Estructura de carpetas que tu amigo crea:
    data/raw/01/001/1/01/001.pdf
    ↓
    Form(
        form_serial="...código único...",
        election_id="PRES_1V_2022",
        department_code="01",
        municipality_code="001",
        voting_table_id=123,
        local_path="data/raw/01/001/1/01/001.pdf",
        file_hash="a3c5f7e2d...",
        processing_status=ProcessingStatus.PENDING
    )
    
    FLUJO:
    1. Tu amigo descarga: status = PENDING
    2. Tú procesas con Gemini: status = EXTRACTED (agrega extraction_results)
    3. Tú detectas anomalías: status = ANALYZED (agrega anomalies)
    
    Ejemplo:
    ┌─────────────┬──────────────┬──────────────┬──────────┐
    │ form_serial │ election_id  │ local_path   │ status   │
    ├─────────────┼──────────────┼──────────────┼──────────┤
    │ "5036317"   │ "PRES_1V_22" │ "data/raw/..│ PENDING  │
    │ "5036318"   │ "PRES_1V_22" │ "data/raw/..│ PENDING  │
    └─────────────┴──────────────┴──────────────┴──────────┘
    """
    
    __tablename__ = "forms"
    
    # Identificación única
    id = Column(Integer, primary_key=True, autoincrement=True)
    form_serial = Column(String(100), unique=True, nullable=False, index=True)
    
    # Elección
    election_id = Column(String(30), ForeignKey("elections.id"), nullable=False, index=True)
    
    # Geografía
    department_code = Column(String(2), ForeignKey("departments.code"), nullable=False, index=True)
    municipality_code = Column(String(3), nullable=False, index=True)
    voting_table_id = Column(Integer, ForeignKey("voting_tables.id"), nullable=False, index=True)
    
    # Almacenamiento local (CRÍTICO PARA TI)
    local_path = Column(String(500), nullable=False)  # "data/raw/01/001/1/01/001.pdf"
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash del PDF
    
    # Procesamiento
    download_timestamp = Column(DateTime, nullable=False)
    processing_status = Column(
        Enum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Calidad (se llena DESPUÉS de procesar)
    quality = Column(Enum(FormQuality), nullable=True)
    
    # Errores (si algo sale mal)
    error_message = Column(Text, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # Foreign key compuesto para municipality
        ForeignKeyConstraint(
            ["municipality_code", "department_code"],
            ["municipalities.code", "municipalities.department_code"],
        ),
        # Índices para búsquedas rápidas
        Index("idx_form_election_status", "election_id", "processing_status"),
        Index("idx_form_geography", "department_code", "municipality_code"),
    )
    
    # Relaciones
    election = relationship("Election", back_populates="forms")
    department = relationship("Department", back_populates="forms")
    municipality = relationship(
        "Municipality",
        back_populates="forms",
        foreign_keys="[Form.municipality_code, Form.department_code]",
        overlaps="department,forms"
    )
    voting_table = relationship("VotingTable", back_populates="forms")
    extraction_result = relationship("ExtractionResult", back_populates="form", uselist=False, cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="form", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Form {self.form_serial} - {self.processing_status.value}>"
 
 
# ============================================================================
# TABLA 9: EXTRACTION_RESULTS (Resultados de OCR)
# ============================================================================
 
class ExtractionResult(Base):
    """
    AQUÍ GUARDAS LOS RESULTADOS DE GEMINI 3 FLASH.
    
    Después de procesar un PDF con OCR, guardas:
    - Los números extraídos (votos por candidato, sufragantes, etc.)
    - Cuánta confianza tiene Gemini en cada número
    - El JSON completo de respuesta de Gemini
    - Tokens gastados (para calcular costo)
    
    Ejemplo:
    ┌─────────┬──────────────┬──────────────────────┬────────────┐
    │ form_id │ total_votes  │ raw_json             │ tokens_out │
    ├─────────┼──────────────┼──────────────────────┼────────────┤
    │ 1       │ 380          │ {"candidates": [...]}│ 820        │
    │ 2       │ 395          │ {"candidates": [...]}│ 815        │
    └─────────┴──────────────┴──────────────────────┴────────────┘
    """
    
    __tablename__ = "extraction_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False, unique=True, index=True)
    
    # Respuesta completa de Gemini (guardar TODO por auditoría)
    raw_json = Column(JSON, nullable=False)  # Toda la respuesta de Gemini
    
    # Metadatos del modelo
    model_used = Column(String(50), default="gemini-3-flash")
    api_used = Column(String(50), default="vertex-ai")
    tokens_in = Column(Integer)  # Tokens de entrada (imagen + prompt)
    tokens_out = Column(Integer)  # Tokens de salida (respuesta JSON)
    processing_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Números extraídos (de la sección "Nivelación de la mesa")
    total_sufragantes = Column(Integer)  # Total de personas que votaron
    total_votos_urna = Column(Integer)  # Total de votos en la urna
    total_votos_incinerados = Column(Integer)  # Votos quemados/inválidos
    
    # Totales
    total_votos_mesa = Column(Integer)  # Suma de todos los votos
    votos_blanco = Column(Integer)  # Votos en blanco
    votos_nulos = Column(Integer)  # Votos nulos
    votos_no_marcados = Column(Integer)  # Votos sin marcar
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    form = relationship("Form", back_populates="extraction_result")
    candidate_votes = relationship("CandidateVotes", back_populates="extraction_result", cascade="all, delete-orphan")
    field_tags = relationship("FieldTag", back_populates="extraction_result", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExtractionResult form_id={self.form_id}>"
 
 
# ============================================================================
# TABLA 10: CANDIDATE_VOTES (Votos por candidato)
# ============================================================================
 
class CandidateVotes(Base):
    """
    Los votos que recibió CADA CANDIDATO en cada mesa.
    
    Ejemplo:
    ┌─────────────────┬──────────┬──────────────┬────────────┐
    │ extraction_id   │ cand_id  │ votes        │ confidence │
    ├─────────────────┼──────────┼──────────────┼────────────┤
    │ 1 (mesa 001)    │ 5 (Petro)│ 120          │ 0.98       │
    │ 1 (mesa 001)    │ 3 (Fico) │ 85           │ 0.95       │
    │ 2 (mesa 002)    │ 5 (Petro)│ 140          │ 0.99       │
    └─────────────────┴──────────┴──────────────┴────────────┘
    """
    
    __tablename__ = "candidate_votes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    extraction_id = Column(Integer, ForeignKey("extraction_results.id"), nullable=False, index=True)
    election_candidate_id = Column(Integer, ForeignKey("election_candidates.id"), nullable=False, index=True)
    
    # Los datos
    votes = Column(Integer, nullable=False)  # Cuántos votos
    confidence = Column(Float)  # Confianza de Gemini (0.0 - 1.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    extraction_result = relationship("ExtractionResult", back_populates="candidate_votes")
    election_candidate = relationship("ElectionCandidate", back_populates="candidate_votes")
    
    def __repr__(self):
        return f"<CandidateVotes {self.votes} votes>"
 
 
# ============================================================================
# TABLA 11: FIELD_TAGS (Problemas en campos)
# ============================================================================
 
class FieldTag(Base):
    """
    Problemas encontrados en cada CAMPO del formulario.
    
    Gemini puede marcar una cifra con MÚLTIPLES TAGS.
    Por ejemplo: una cifra puede estar SCRATCH Y AMBIGUOUS.
    
    Ejemplo:
    ┌─────────────────┬──────────────┬────────────────┬───────────────┐
    │ extraction_id   │ field_name   │ tag            │ confidence    │
    ├─────────────────┼──────────────┼────────────────┼───────────────┤
    │ 1               │ "votos_petro"│ "SCRATCH"      │ 0.92          │
    │ 1               │ "votos_petro"│ "OVERWRITTEN"  │ 0.88          │
    │ 2               │ "total_votos"│ "CLEAN"        │ 0.99          │
    └─────────────────┴──────────────┴────────────────┴───────────────┘
    """
    
    __tablename__ = "field_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    extraction_id = Column(Integer, ForeignKey("extraction_results.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)  # "votos_petro", "total_sufragantes", etc.
    tag = Column(Enum(FieldIssueTag), nullable=False)  # SCRATCH, OVERWRITTEN, etc.
    confidence = Column(Float)  # Confianza en que este tag es correcto
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    extraction_result = relationship("ExtractionResult", back_populates="field_tags")
    
    def __repr__(self):
        return f"<FieldTag {self.field_name}: {self.tag.value}>"
 
 
# ============================================================================
# TABLA 12: ANOMALIES (Anomalías detectadas)
# ============================================================================
 
class Anomaly(Base):
    """
    ANOMALÍAS DETECTADAS en cada formulario.
    
    Después de extraer, ejecutas tu script analyze.py que detecta problemas:
    - La suma de votos no cuadra
    - Hay demasiados campos borrados
    - El patrón de votos es sospechoso
    - Etc.
    
    Ejemplo:
    ┌─────────┬─────────────────────┬──────────┬──────────┐
    │ form_id │ type                │ severity │ desc     │
    ├─────────┼─────────────────────┼──────────┼──────────┤
    │ 1       │ "ARITHMETIC_MISMATCH"│ "WARNING"│ "Suma... │
    │ 2       │ "HIGH_ISSUE_DENSITY"│ "ALERT"  │ "3+ ... │
    └─────────┴─────────────────────┴──────────┴──────────┘
    """
    
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False, index=True)
    
    # Tipo y severidad
    anomaly_type = Column(Enum(AnomalyType), nullable=False, index=True)
    severity = Column(Enum(AnomalySeverity), nullable=False, index=True)
    
    # Descripción
    description = Column(Text)  # "Suma de candidatos (300) ≠ total (305)"
    details = Column(JSON)  # Datos extra en JSON
    
    # Auditoría
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    form = relationship("Form", back_populates="anomalies")
    
    def __repr__(self):
        return f"<Anomaly {self.anomaly_type.value} - {self.severity.value}>"
 
 
# ============================================================================
# FUNCIONES HELPER
# ============================================================================
 
def create_engine_connection(database_url: str):
    """
    Crea conexión a la BD.
    
    Args:
        database_url: Ej: "sqlite:///data/e14.db"
                      o "postgresql://user:pass@localhost/e14db"
    
    Returns:
        Engine
    """
    engine = create_engine(database_url, echo=False)
    return engine
 
 
def create_all_tables(database_url: str):
    """
    CREA TODAS LAS TABLAS EN LA BD.
    
    ⚠️ Ejecuta SOLO UNA VEZ al inicio.
    ⚠️ No elimina datos si la BD ya existe (usa ALTER TABLE internamente).
    
    Args:
        database_url: URL de la BD
    
    Returns:
        Engine
    """
    engine = create_engine_connection(database_url)
    Base.metadata.create_all(engine)
    print(f"\n✅ Tablas creadas/actualizadas en: {database_url}\n")
    return engine
 
 
def drop_all_tables(database_url: str):
    """
    ELIMINA TODAS LAS TABLAS.
    
    ⚠️ CUIDADO: Esto borra TODO. Solo para desarrollo.
    
    Args:
        database_url: URL de la BD
    """
    engine = create_engine_connection(database_url)
    Base.metadata.drop_all(engine)
    print(f"\n🗑️  Todas las tablas eliminadas de: {database_url}\n")
 
 
# ============================================================================
# VERIFICACIÓN Y TESTING
# ============================================================================
 
if __name__ == "__main__":
    print("\n" + "="*70)
    print("📊 ESQUEMA COMPLETO DE E14 CHALLENGE")
    print("="*70)
    
    print("\n🔹 TABLAS DEFINIDAS:")
    tables_info = {
        "elections": "Configuración de cada elección",
        "election_candidates": "Candidatos por elección",
        "departments": "Departamentos de Colombia",
        "municipalities": "Municipios dentro de departamentos",
        "zones": "Zonas dentro de municipios",
        "stations": "Puestos de votación",
        "voting_tables": "Mesas dentro de puestos",
        "forms": "⭐ PDFs DESCARGADOS (tabla central)",
        "extraction_results": "🤖 Resultados de OCR con Gemini",
        "candidate_votes": "Votos por candidato",
        "field_tags": "Problemas en campos",
        "anomalies": "Anomalías detectadas",
    }
    
    for table, desc in tables_info.items():
        print(f"  ✅ {table:25} → {desc}")
    
    print("\n" + "="*70)
    print("FLUJO RECOMENDADO:")
    print("="*70)
    print("""
    1️⃣  Tu amigo (Persona A) descarga PDFs:
        data/raw/01/001/1/01/001.pdf
        ↓ Crea entrada en BD:
        INSERT INTO forms (form_serial, election_id, local_path, status=PENDING)
    
    2️⃣  Tú (Persona B) procesas:
        - Lee forms WHERE status=PENDING
        - Procesa cada PDF con Gemini 3 Flash
        - Guarda en extraction_results, candidate_votes, field_tags
        - UPDATE forms SET status=EXTRACTED
    
    3️⃣  Tú (Persona B) analizas:
        - Lee extraction_results
        - Ejecuta algoritmos de detección
        - Guarda en anomalies
        - UPDATE forms SET status=ANALYZED
    
    4️⃣  Dashboard (FastAPI + React):
        - Lee forms, extraction_results, anomalies
        - Sirve JSON al frontend
        - Usuario ve resultados
    """)
    
    print("="*70 + "\n")
