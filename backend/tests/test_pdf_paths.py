"""Pruebas de rutas PDF (estructura scraper Playwright)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_RAW_DIR
from src.storage.pdf_paths import (
    construir_ruta_pdf,
    generar_form_serial,
    parsear_ruta_pdf,
)


def test_construir_y_parsear_ruta():
    ruta = construir_ruta_pdf(DATA_RAW_DIR, "5", "1", "1", "1", "31")
    assert ruta == DATA_RAW_DIR / "05" / "001" / "001" / "01" / "031.pdf"

    info = parsear_ruta_pdf(ruta, DATA_RAW_DIR)
    assert info is not None
    assert info["dept_code"] == "05"
    assert info["muni_code"] == "001"
    assert info["zone_code"] == "001"
    assert info["station_code"] == "01"
    assert info["table_number"] == "031"
    assert info["form_serial"] == generar_form_serial("05", "001", "001", "01", "031")


def test_ruta_invalida():
    assert parsear_ruta_pdf(DATA_RAW_DIR / "solo.pdf", DATA_RAW_DIR) is None


if __name__ == "__main__":
    test_construir_y_parsear_ruta()
    test_ruta_invalida()
    print("✅ test_pdf_paths OK")
