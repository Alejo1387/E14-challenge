"""
Tests automáticos de esquema y foreign keys (SQLite + SQLAlchemy).

Ejecutar desde backend/:
    uv run pytest tests/test_database.py -v
    uv run pytest tests/ -v
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from src.database.schema import (
    Anomaly,
    AnomalySeverity,
    AnomalyType,
    CandidateVotes,
    Department,
    Election,
    ElectionCandidate,
    ExtractionResult,
    FieldIssueTag,
    FieldTag,
    Form,
    Municipality,
    ProcessingStatus,
    Station,
    VotingTable,
    Zone,
)

from tests.conftest import TABLAS_ESPERADAS


# ---------------------------------------------------------------------------
# Esquema: tablas existen
# ---------------------------------------------------------------------------


def test_todas_las_tablas_del_esquema_existen(engine):
    nombres = inspect(engine).get_table_names()
    for tabla in TABLAS_ESPERADAS:
        assert tabla in nombres, f"Falta la tabla {tabla}"


def test_foreign_keys_activadas_en_sqlite(engine):
    with engine.connect() as conn:
        valor = conn.execute(text("PRAGMA foreign_keys")).scalar()
    assert valor == 1


# ---------------------------------------------------------------------------
# FK: geografía electoral
# ---------------------------------------------------------------------------


def test_municipio_requiere_departamento_existente(session):
    session.add(
        Municipality(code="999", department_code="99", name="Muni huérfano")
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_zona_requiere_municipio_compuesto(session):
    session.add(Department(code="05", name="Bolívar"))
    session.commit()
    session.add(
        Zone(
            municipality_code="001",
            municipality_department="05",
            zone_number="001",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_puesto_requiere_zona(session):
    with pytest.raises(IntegrityError):
        session.add(Station(zone_id=99999, station_number="01", name="X"))
        session.commit()
    session.rollback()


def test_mesa_requiere_puesto(session):
    with pytest.raises(IntegrityError):
        session.add(VotingTable(station_id=99999, table_number="001"))
        session.commit()
    session.rollback()


# ---------------------------------------------------------------------------
# FK: elección y candidatos
# ---------------------------------------------------------------------------


def test_candidato_requiere_eleccion(session):
    session.add(
        ElectionCandidate(
            election_id="NO_EXISTE",
            position=1,
            candidate_name="Fantasma",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# ---------------------------------------------------------------------------
# FK: forms
# ---------------------------------------------------------------------------


def test_form_rechaza_election_id_invalido(session, datos_minimos):
    session.add(
        Form(
            form_serial="TEST-FK-ELECTION",
            election_id="ELECCION_INVENTADA",
            department_code=datos_minimos.department_code,
            municipality_code=datos_minimos.municipality_code,
            voting_table_id=datos_minimos.voting_table_id,
            local_path="data/raw/test.pdf",
            file_hash="b" * 64,
            download_timestamp=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_form_rechaza_department_code_invalido(session, datos_minimos):
    session.add(
        Form(
            form_serial="TEST-FK-DEPT",
            election_id=datos_minimos.election_id,
            department_code="99",
            municipality_code=datos_minimos.municipality_code,
            voting_table_id=datos_minimos.voting_table_id,
            local_path="data/raw/test.pdf",
            file_hash="c" * 64,
            download_timestamp=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_form_rechaza_municipio_no_pertenece_al_departamento(session, datos_minimos):
    """Municipio 001 existe bajo 05, no bajo 01."""
    session.add(Department(code="01", name="Otro depto"))
    session.commit()

    session.add(
        Form(
            form_serial="TEST-FK-MUNI",
            election_id=datos_minimos.election_id,
            department_code="01",
            municipality_code=datos_minimos.municipality_code,
            voting_table_id=datos_minimos.voting_table_id,
            local_path="data/raw/test.pdf",
            file_hash="d" * 64,
            download_timestamp=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_form_rechaza_voting_table_id_invalido(session, datos_minimos):
    session.add(
        Form(
            form_serial="TEST-FK-MESA",
            election_id=datos_minimos.election_id,
            department_code=datos_minimos.department_code,
            municipality_code=datos_minimos.municipality_code,
            voting_table_id=99999,
            local_path="data/raw/test.pdf",
            file_hash="e" * 64,
            download_timestamp=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_form_serial_debe_ser_unico(session, datos_minimos, formulario_valido):
    duplicado = Form(
        form_serial=formulario_valido.form_serial,
        election_id=datos_minimos.election_id,
        department_code=datos_minimos.department_code,
        municipality_code=datos_minimos.municipality_code,
        voting_table_id=datos_minimos.voting_table_id,
        local_path="data/raw/otro.pdf",
        file_hash="f" * 64,
        download_timestamp=datetime.utcnow(),
        processing_status=ProcessingStatus.PENDING,
    )
    session.add(duplicado)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_form_insert_valido(session, datos_minimos, formulario_valido):
    assert formulario_valido.id is not None
    assert formulario_valido.form_serial == "05-001-001-01-099"
    assert formulario_valido.voting_table_id == datos_minimos.voting_table_id


# ---------------------------------------------------------------------------
# FK: OCR y anomalías
# ---------------------------------------------------------------------------


def test_extraction_result_requiere_form(session):
    session.add(
        ExtractionResult(
            form_id=99999,
            raw_json={"test": True},
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_candidate_votes_requiere_extraction_y_candidato(session, datos_minimos):
    with pytest.raises(IntegrityError):
        session.add(
            CandidateVotes(
                extraction_id=99999,
                election_candidate_id=datos_minimos.candidate_id,
                votes=10,
            )
        )
        session.commit()
    session.rollback()

    with pytest.raises(IntegrityError):
        session.add(
            CandidateVotes(
                extraction_id=1,
                election_candidate_id=99999,
                votes=10,
            )
        )
        session.commit()
    session.rollback()


def test_field_tags_requiere_extraction(session):
    session.add(
        FieldTag(
            extraction_id=99999,
            field_name="votos_petro",
            tag=FieldIssueTag.CLEAN,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_anomaly_requiere_form(session):
    session.add(
        Anomaly(
            form_id=99999,
            anomaly_type=AnomalyType.ARITHMETIC_MISMATCH,
            severity=AnomalySeverity.WARNING,
            description="test",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_cadena_ocr_valida(session, formulario_valido, datos_minimos):
    """Inserción válida: form → extraction → candidate_votes + field_tags."""
    extraction = ExtractionResult(
        form_id=formulario_valido.id,
        raw_json={"candidates": []},
        total_votos_mesa=100,
    )
    session.add(extraction)
    session.flush()

    session.add(
        CandidateVotes(
            extraction_id=extraction.id,
            election_candidate_id=datos_minimos.candidate_id,
            votes=50,
            confidence=0.95,
        )
    )
    session.add(
        FieldTag(
            extraction_id=extraction.id,
            field_name="votos_test",
            tag=FieldIssueTag.CLEAN,
            confidence=0.99,
        )
    )
    session.add(
        Anomaly(
            form_id=formulario_valido.id,
            anomaly_type=AnomalyType.ARITHMETIC_MISMATCH,
            severity=AnomalySeverity.INFO,
            description="OK en test",
        )
    )
    session.commit()

    assert session.query(ExtractionResult).count() == 1
    assert session.query(CandidateVotes).count() == 1
    assert session.query(FieldTag).count() == 1
    assert session.query(Anomaly).count() == 1


def test_extraction_result_un_solo_por_form(session, formulario_valido):
    session.add(
        ExtractionResult(form_id=formulario_valido.id, raw_json={"a": 1})
    )
    session.commit()
    session.add(
        ExtractionResult(form_id=formulario_valido.id, raw_json={"b": 2})
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
