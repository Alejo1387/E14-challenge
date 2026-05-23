"""
pdf_paths.py — Rutas de PDFs alineadas con el scraper Playwright.

Estructura oficial:
    backend/data/raw/{depto}/{muni}/{zona}/{puesto}/{mesa}.pdf

Ejemplo:
    backend/data/raw/05/001/001/01/031.pdf
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config import BASE_DIR, DATA_RAW_DIR


def normalizar_codigo(valor: str, ancho: int) -> str:
    """Normaliza códigos numéricos con ceros a la izquierda."""
    v = str(valor).strip()
    if v.isdigit():
        return v.zfill(ancho)
    return v


def normalizar_ubicacion(
    dept_code: str,
    muni_code: str,
    zone_code: str,
    station_code: str,
    table_number: str,
) -> dict[str, str]:
    return {
        "dept_code": normalizar_codigo(dept_code, 2),
        "muni_code": normalizar_codigo(muni_code, 3),
        "zone_code": normalizar_codigo(zone_code, 3),
        "station_code": normalizar_codigo(station_code, 2),
        "table_number": normalizar_codigo(table_number, 3),
    }


def generar_form_serial(
    dept_code: str,
    muni_code: str,
    zone_code: str,
    station_code: str,
    table_number: str,
) -> str:
    """Serial único derivado de la ubicación electoral."""
    u = normalizar_ubicacion(
        dept_code, muni_code, zone_code, station_code, table_number
    )
    return (
        f"{u['dept_code']}-{u['muni_code']}-{u['zone_code']}-"
        f"{u['station_code']}-{u['table_number']}"
    )


def construir_ruta_pdf(
    base_dir: Path,
    dept_code: str,
    muni_code: str,
    zone_code: str,
    station_code: str,
    table_number: str,
) -> Path:
    u = normalizar_ubicacion(
        dept_code, muni_code, zone_code, station_code, table_number
    )
    return (
        Path(base_dir)
        / u["dept_code"]
        / u["muni_code"]
        / u["zone_code"]
        / u["station_code"]
        / f"{u['table_number']}.pdf"
    )


def ruta_sidecar(pdf_path: Path) -> Path:
    """Ruta del JSON generado por scrape_v2: 031.pdf.meta.json"""
    return pdf_path.with_suffix(pdf_path.suffix + ".meta.json")


def cargar_sidecar(pdf_path: Path) -> Optional[dict[str, Any]]:
    sidecar = ruta_sidecar(pdf_path)
    if not sidecar.is_file():
        return None
    try:
        with open(sidecar, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _ubicacion_desde_sidecar(meta: dict[str, Any]) -> Optional[dict[str, str]]:
    dept = meta.get("dept_code") or meta.get("depto")
    muni = meta.get("municipality_code") or meta.get("muni")
    zone = meta.get("zone_code") or meta.get("zona")
    station = meta.get("station_code") or meta.get("puesto")
    mesa = meta.get("table_number") or meta.get("mesa")
    if not all([dept, muni, zone, station, mesa]):
        return None
    return normalizar_ubicacion(dept, muni, zone, station, mesa)


def parsear_ruta_pdf(
    pdf_path: Path,
    raw_dir: Path | None = None,
) -> Optional[dict[str, Any]]:
    """
    Extrae departamento, municipio, zona, puesto y mesa desde la ruta del PDF.

    Returns:
        dict con códigos normalizados, form_serial, ruta_completa y sidecar (si hay)
    """
    raw = Path(raw_dir or DATA_RAW_DIR).resolve()
    path = Path(pdf_path).resolve()

    if path.suffix.lower() != ".pdf":
        return None

    try:
        rel = path.relative_to(raw)
    except ValueError:
        return None

    parts = rel.parts
    if len(parts) != 5:
        return None

    dept_code, muni_code, zone_code, station_code, filename = parts
    table_number = Path(filename).stem

    ubicacion = normalizar_ubicacion(
        dept_code, muni_code, zone_code, station_code, table_number
    )

    sidecar = cargar_sidecar(path)
    if sidecar:
        desde_meta = _ubicacion_desde_sidecar(sidecar)
        if desde_meta:
            ubicacion = desde_meta

    form_serial = generar_form_serial(
        ubicacion["dept_code"],
        ubicacion["muni_code"],
        ubicacion["zone_code"],
        ubicacion["station_code"],
        ubicacion["table_number"],
    )

    try:
        ruta_relativa = str(path.relative_to(BASE_DIR.resolve()))
    except ValueError:
        ruta_relativa = str(path)

    return {
        **ubicacion,
        "form_serial": form_serial,
        "ruta_completa": str(path),
        "ruta_relativa": ruta_relativa,
        "sidecar": sidecar,
    }
