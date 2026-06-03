"""
Fixtures compartidas para tests del backend.

Usa SQLite en memoria con foreign_keys=ON (igual que connection.py en producción).
No toca backend/data/e14_challenge.db.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar pytest desde backend/ o desde la raíz del repo (…/backend/tests/)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dataclasses import dataclass
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.database.schema import (
    Base,
    Department,
    Election,
    ElectionCandidate,
    Form,
    Municipality,
    ProcessingStatus,
    Station,
    VotingTable,
    Zone,
)

TABLAS_ESPERADAS = [
    "elections",
    "election_candidates",
    "departments",
    "municipalities",
    "zones",
    "stations",
    "voting_tables",
    "forms",
    "extraction_results",
    "candidate_votes",
    "field_tags",
    "anomalies",
]


def _sqlite_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture
def engine():
    eng = _sqlite_engine()
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def session(engine):
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dataclass
class DatosMinimosBD:
    """Referencias a filas mínimas válidas para pruebas de FK."""

    election_id: str
    department_code: str
    municipality_code: str
    zone_id: int
    station_id: int
    voting_table_id: int
    candidate_id: int


@pytest.fixture
def datos_minimos(session: Session) -> DatosMinimosBD:
    """
    Pila válida: elección → candidato → depto → muni → zona → puesto → mesa.
    """
    election_id = "PRES_1V_2022"

    session.add(
        Election(
            id=election_id,
            name="Presidenciales 1ª Vuelta 2022 (test)",
            election_date=datetime(2022, 5, 29),
            candidate_count=1,
            status="ACTIVE",
        )
    )
    session.add(
        ElectionCandidate(
            election_id=election_id,
            position=1,
            candidate_name="Candidato Test",
            party="Partido Test",
        )
    )
    session.add(Department(code="05", name="Bolívar"))
    session.add(
        Municipality(
            code="001",
            department_code="05",
            name="Cartagena",
        )
    )
    session.add(
        Zone(
            municipality_code="001",
            municipality_department="05",
            zone_number="001",
        )
    )
    session.flush()

    station = Station(
        zone_id=session.query(Zone).one().id,
        station_number="01",
        name="Puesto test",
    )
    session.add(station)
    session.flush()

    mesa = VotingTable(station_id=station.id, table_number="099")
    session.add(mesa)
    session.commit()

    candidate = session.query(ElectionCandidate).one()

    return DatosMinimosBD(
        election_id=election_id,
        department_code="05",
        municipality_code="001",
        zone_id=session.query(Zone).one().id,
        station_id=station.id,
        voting_table_id=mesa.id,
        candidate_id=candidate.id,
    )


@pytest.fixture
def formulario_valido(session: Session, datos_minimos: DatosMinimosBD) -> Form:
    """Un formulario E-14 insertado correctamente."""
    form = Form(
        form_serial="05-001-001-01-099",
        election_id=datos_minimos.election_id,
        department_code=datos_minimos.department_code,
        municipality_code=datos_minimos.municipality_code,
        voting_table_id=datos_minimos.voting_table_id,
        local_path="data/raw/05/001/001/01/099.pdf",
        file_hash="a" * 64,
        download_timestamp=datetime.utcnow(),
        processing_status=ProcessingStatus.PENDING,
    )
    session.add(form)
    session.commit()
    session.refresh(form)
    return form
