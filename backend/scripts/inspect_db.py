"""
inspect_db.py — Inspección y validación de la base de datos E14 Challenge

Muestra conteos por tabla, revisa integridad (FKs, elección, candidatos)
y comprueba que los PDFs registrados existan en disco.

Uso:
    cd backend
    python scripts/inspect_db.py
    python scripts/inspect_db.py --verbose
    python scripts/inspect_db.py --json

Docker:
    docker compose exec backend python scripts/inspect_db.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BASE_DIR, DATABASE_PATH, DATA_RAW_DIR, ELECTION_ID
from sqlalchemy import text

from src.database.connection import session_scope, verificar_conexion
from src.database.schema import Base
from src.database.queries import obtener_estadisticas_generales

TABLAS_ORDEN = [
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

CANDIDATOS_ESPERADOS_2022 = 8


def _contar_tablas(session) -> dict[str, int]:
    counts = {}
    for nombre in TABLAS_ORDEN:
        if nombre in Base.metadata.tables:
            n = session.execute(
                text(f"SELECT COUNT(*) FROM {nombre}")
            ).scalar()
            counts[nombre] = int(n or 0)
    return counts


def _validar_eleccion_y_candidatos(session) -> list[dict]:
    """Comprueba elección configurada y 8 candidatos presidenciales 2022."""
    hallazgos = []

    eleccion = session.execute(
        text("SELECT id, name, candidate_count, portal_url FROM elections WHERE id = :eid"),
        {"eid": ELECTION_ID},
    ).fetchone()

    if not eleccion:
        hallazgos.append({
            "nivel": "error",
            "codigo": "ELECTION_MISSING",
            "mensaje": f"No existe la elección {ELECTION_ID}. Ejecuta seed_data.py",
        })
        return hallazgos

    n_candidatos = session.execute(
        text(
            "SELECT COUNT(*) FROM election_candidates WHERE election_id = :eid"
        ),
        {"eid": ELECTION_ID},
    ).scalar()

    if n_candidatos != CANDIDATOS_ESPERADOS_2022:
        hallazgos.append({
            "nivel": "error",
            "codigo": "CANDIDATES_COUNT",
            "mensaje": (
                f"Se esperaban {CANDIDATOS_ESPERADOS_2022} candidatos para "
                f"{ELECTION_ID}, hay {n_candidatos}"
            ),
        })
    elif eleccion.candidate_count != CANDIDATOS_ESPERADOS_2022:
        hallazgos.append({
            "nivel": "warning",
            "codigo": "CANDIDATES_COUNT_FIELD",
            "mensaje": (
                f"elections.candidate_count={eleccion.candidate_count} "
                f"pero hay {n_candidatos} filas en election_candidates"
            ),
        })

    if not eleccion.portal_url:
        hallazgos.append({
            "nivel": "warning",
            "codigo": "PORTAL_URL_EMPTY",
            "mensaje": f"La elección {ELECTION_ID} no tiene portal_url",
        })

    return hallazgos


def _validar_forms_fk(session) -> list[dict]:
    """Formularios con referencias rotas (depto, muni, elección, mesa)."""
    hallazgos = []
    checks = [
        (
            "FORMS_ELECTION_FK",
            "error",
            """
            SELECT f.id, f.form_serial, f.election_id
            FROM forms f
            LEFT JOIN elections e ON f.election_id = e.id
            WHERE e.id IS NULL
            """,
            "formularios con election_id inválido",
        ),
        (
            "FORMS_DEPARTMENT_FK",
            "error",
            """
            SELECT f.id, f.form_serial, f.department_code
            FROM forms f
            LEFT JOIN departments d ON f.department_code = d.code
            WHERE d.code IS NULL
            """,
            "formularios con department_code inválido",
        ),
        (
            "FORMS_MUNICIPALITY_FK",
            "error",
            """
            SELECT f.id, f.form_serial, f.municipality_code, f.department_code
            FROM forms f
            LEFT JOIN municipalities m
              ON f.municipality_code = m.code
             AND f.department_code = m.department_code
            WHERE m.code IS NULL
            """,
            "formularios con municipio inválido",
        ),
        (
            "FORMS_VOTING_TABLE_FK",
            "error",
            """
            SELECT f.id, f.form_serial, f.voting_table_id
            FROM forms f
            LEFT JOIN voting_tables vt ON f.voting_table_id = vt.id
            WHERE vt.id IS NULL
            """,
            "formularios con voting_table_id inválido",
        ),
    ]

    for codigo, nivel, sql, descripcion in checks:
        filas = session.execute(text(sql)).fetchall()
        if filas:
            hallazgos.append({
                "nivel": nivel,
                "codigo": codigo,
                "mensaje": f"{len(filas)} {descripcion}",
                "detalle": [
                    dict(row._mapping) for row in filas[:10]
                ],
            })

    return hallazgos


def _validar_pdfs_en_disco(session) -> list[dict]:
    """Formularios cuyo local_path no apunta a un PDF existente."""
    hallazgos = []
    forms = session.execute(
        text("SELECT id, form_serial, local_path FROM forms ORDER BY id")
    ).fetchall()

    faltantes = []
    for row in forms:
        ruta = BASE_DIR / row.local_path
        if not ruta.is_file():
            faltantes.append({
                "id": row.id,
                "form_serial": row.form_serial,
                "local_path": row.local_path,
                "ruta_absoluta": str(ruta),
            })

    if faltantes:
        hallazgos.append({
            "nivel": "warning",
            "codigo": "PDF_FILE_MISSING",
            "mensaje": f"{len(faltantes)} formulario(s) sin PDF en disco",
            "detalle": faltantes[:15],
        })

    return hallazgos


def _validar_huerfanos_ocr(session) -> list[dict]:
    """Registros OCR/anomalías sin formulario padre."""
    hallazgos = []
    checks = [
        (
            "ORPHAN_EXTRACTION",
            """
            SELECT er.id, er.form_id FROM extraction_results er
            LEFT JOIN forms f ON er.form_id = f.id
            WHERE f.id IS NULL
            """,
        ),
        (
            "ORPHAN_ANOMALY",
            """
            SELECT a.id, a.form_id FROM anomalies a
            LEFT JOIN forms f ON a.form_id = f.id
            WHERE f.id IS NULL
            """,
        ),
    ]
    for codigo, sql in checks:
        filas = session.execute(text(sql)).fetchall()
        if filas:
            hallazgos.append({
                "nivel": "error",
                "codigo": codigo,
                "mensaje": f"{len(filas)} registro(s) huérfano(s)",
                "detalle": [dict(r._mapping) for r in filas[:10]],
            })
    return hallazgos


def _listar_candidatos(session, verbose: bool) -> list[dict]:
    if not verbose:
        return []
    rows = session.execute(
        text(
            """
            SELECT position, candidate_name, party
            FROM election_candidates
            WHERE election_id = :eid
            ORDER BY position
            """
        ),
        {"eid": ELECTION_ID},
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def _listar_forms_muestra(session, verbose: bool) -> list[dict]:
    if not verbose:
        return []
    rows = session.execute(
        text(
            """
            SELECT
                f.id,
                f.form_serial,
                f.processing_status,
                f.voting_table_id,
                vt.table_number AS mesa_pdf,
                f.local_path
            FROM forms f
            JOIN voting_tables vt ON f.voting_table_id = vt.id
            ORDER BY f.id
            LIMIT 20
            """
        )
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def ejecutar_inspeccion(verbose: bool = False) -> dict:
    resultado = {
        "ok": True,
        "database_path": str(DATABASE_PATH),
        "database_exists": DATABASE_PATH.is_file(),
        "conexion_ok": False,
        "conteos": {},
        "estadisticas": {},
        "hallazgos": [],
        "candidatos": [],
        "forms_muestra": [],
    }

    print("\n" + "=" * 70)
    print("🔍 INSPECCIÓN DE BASE DE DATOS — E14 Challenge")
    print("=" * 70 + "\n")

    if not DATABASE_PATH.is_file():
        resultado["ok"] = False
        resultado["hallazgos"].append({
            "nivel": "error",
            "codigo": "DB_FILE_MISSING",
            "mensaje": f"No existe el archivo: {DATABASE_PATH}",
        })
        print(f"❌ No existe la BD: {DATABASE_PATH}")
        print("   Ejecuta: python scripts/setup_db.py\n")
        return resultado

    print(f"📂 Archivo BD: {DATABASE_PATH}")
    print(f"📂 PDFs raw:   {DATA_RAW_DIR}\n")

    if not verificar_conexion():
        resultado["ok"] = False
        resultado["hallazgos"].append({
            "nivel": "error",
            "codigo": "CONNECTION_FAILED",
            "mensaje": "No se pudo conectar a la base de datos",
        })
        print("❌ Conexión a la BD fallida\n")
        return resultado

    resultado["conexion_ok"] = True
    print("✅ Conexión OK\n")

    with session_scope() as session:
        resultado["conteos"] = _contar_tablas(session)
        resultado["estadisticas"] = obtener_estadisticas_generales()

        print("📊 Conteo por tabla:\n")
        for tabla in TABLAS_ORDEN:
            n = resultado["conteos"].get(tabla, 0)
            print(f"   {tabla:24} {n:>6}")

        print("\n📈 Resumen operativo:\n")
        stats = resultado["estadisticas"]
        labels = {
            "total_departamentos": "Departamentos",
            "total_municipios": "Municipios",
            "total_zonas": "Zonas",
            "total_estaciones": "Puestos",
            "total_mesas": "Mesas",
            "total_formularios": "Formularios (forms)",
            "formularios_pendientes": "  → PENDING",
            "formularios_extraidos": "  → EXTRACTED",
            "formularios_analizados": "  → ANALYZED",
            "formularios_fallidos": "  → FAILED",
        }
        for key, label in labels.items():
            print(f"   {label:28} {stats.get(key, 0):>6}")

        print("\n🔎 Validaciones:\n")

        todas_validaciones = []
        todas_validaciones.extend(_validar_eleccion_y_candidatos(session))
        todas_validaciones.extend(_validar_forms_fk(session))
        todas_validaciones.extend(_validar_pdfs_en_disco(session))
        todas_validaciones.extend(_validar_huerfanos_ocr(session))

        resultado["hallazgos"] = todas_validaciones
        resultado["candidatos"] = _listar_candidatos(session, verbose)
        resultado["forms_muestra"] = _listar_forms_muestra(session, verbose)

        errores = 0
        advertencias = 0
        for h in todas_validaciones:
            icono = "❌" if h["nivel"] == "error" else "⚠️ "
            print(f"   {icono} [{h['codigo']}] {h['mensaje']}")
            if verbose and h.get("detalle"):
                for item in h["detalle"]:
                    print(f"        {item}")
            if h["nivel"] == "error":
                errores += 1
                resultado["ok"] = False
            elif h["nivel"] == "warning":
                advertencias += 1

        if not todas_validaciones:
            print("   ✅ Sin problemas detectados")

        if verbose and resultado["candidatos"]:
            print(f"\n👤 Candidatos ({ELECTION_ID}):\n")
            for c in resultado["candidatos"]:
                print(
                    f"   {c['position']:>2}. {c['candidate_name']} "
                    f"({c['party']})"
                )

        if verbose and resultado["forms_muestra"]:
            print("\n📄 Formularios (muestra, mesa = voting_tables.table_number):\n")
            for f in resultado["forms_muestra"]:
                print(
                    f"   id={f['id']} {f['form_serial']} | "
                    f"mesa={f['mesa_pdf']} | {f['processing_status']} | "
                    f"{f['local_path']}"
                )

        print("\n" + "=" * 70)
        if resultado["ok"]:
            if advertencias:
                print(f"✅ BD válida con {advertencias} advertencia(s)")
            else:
                print("✅ BD válida — todo en orden")
        else:
            print(f"❌ BD con {errores} error(es) y {advertencias} advertencia(s)")
        print("=" * 70 + "\n")

    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspecciona y valida la base de datos E14 Challenge"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Muestra candidatos, formularios y detalle de hallazgos",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime el resultado completo en JSON (útil para CI)",
    )
    args = parser.parse_args()

    resultado = ejecutar_inspeccion(verbose=args.verbose)

    if args.json:
        print(json.dumps(resultado, indent=2, default=str))

    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido")
        sys.exit(1)
