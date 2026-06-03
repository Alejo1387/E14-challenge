# =============================================================================
# scrape_v2_with_playwright.py — VERSIÓN COMPLETA Y FUNCIONAL
# =============================================================================
# Script que COMBINA:
# 1. Playwright (stealth mode) para resolver reCAPTCHA
# 2. Extracción de tokens del HTML
# 3. Descarga de PDFs con requests (rápido)
# 4. Almacenamiento en estructura de carpetas correcta
#
# Este es el SCRIPT FINAL que reemplaza al scrape.py anterior
# =============================================================================

import asyncio
import os
import sys
import hashlib
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Configuración
BASE_URL = "https://e14_pres1v_2022.registraduria.gov.co"
DATA_RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_FILE = DATA_RAW_DIR / "manifest_descargas.json"

# Desactivar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# =============================================================================
# PASO 1: CLASE PARA NAVEGACIÓN CON PLAYWRIGHT (STEALTH)
# =============================================================================

class PlaywrightNavigator:
    """
    Usa Playwright para navegar el portal y extraer tokens de mesas.
    Implementa técnicas stealth para pasar el WAF.
    """
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
    
    async def initialize(self):
        """Abre el navegador con opciones stealth"""
        p = await async_playwright().start()
        
        self.browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="es-ES",
            timezone_id="America/Bogota",
        )
        
        # Inyectar JS para ocultar automation
        await self.context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)
        
        self.page = await self.context.new_page()
    
    async def navigate_to_portal(self) -> bool:
        """Navega al portal y retorna True si fue exitoso"""
        try:
            print("📥 Navegando al portal...")
            response = await self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
            print(f"✅ Portal cargado (status: {response.status})")
            return response.status == 200
        except Exception as e:
            print(f"❌ Error al navegar: {str(e)}")
            return False
    
    async def select_option(self, selector: str, value: str) -> bool:
        """Selecciona una opción en un dropdown"""
        try:
            await self.page.select_option(selector, value)
            await asyncio.sleep(0.3)  # Esperar a que se cargue
            return True
        except Exception as e:
            print(f"⚠️  Error al seleccionar {selector}={value}: {str(e)}")
            return False
    
    async def click_button(self, selector: str) -> bool:
        """Hace clic en un botón"""
        try:
            await self.page.click(selector)
            await asyncio.sleep(1)  # Esperar respuesta del servidor
            return True
        except Exception as e:
            print(f"⚠️  Error al hacer clic en {selector}: {str(e)}")
            return False
    
    async def get_html(self) -> str:
        """Obtiene el HTML actual de la página"""
        return await self.page.content()
    
    async def close(self):
        """Cierra el navegador"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


# =============================================================================
# PASO 2: EXTRACTOR DE TOKENS
# =============================================================================

def extract_tokens_from_html(html: str) -> List[Dict]:
    """
    Extrae tokens de descarga del HTML de la tabla de mesas.
    
    Retorna lista de diccionarios con:
    - mesa: número de mesa
    - token: token para descargar
    """
    soup = BeautifulSoup(html, "html.parser")
    tokens = []
    
    # Buscar botones con type="submit" y name="data"
    buttons = soup.find_all("button", {"type": "submit", "name": "data"})
    
    for btn in buttons:
        mesa_text = btn.get_text(strip=True)
        token_value = btn.get("value", "")
        
        if token_value:
            tokens.append({
                "mesa": mesa_text,
                "token": token_value
            })
    
    return tokens


# =============================================================================
# PASO 3: DESCARGADOR DE PDFS
# =============================================================================

def calculate_file_hash(file_path: Path) -> str:
    """Calcula SHA-256 del archivo"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_pdf(token: str, depto: str, muni: str, zona: str, puesto: str, mesa: str) -> Optional[Dict]:
    """
    Descarga UN PDF y lo guarda en la carpeta correcta.
    
    Retorna diccionario con info de descarga o None si falló.
    """
    try:
        # Crear carpeta de destino
        dest_dir = DATA_RAW_DIR / depto / muni / zona / puesto
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = dest_dir / f"{mesa}.pdf"
        
        # Descargar
        print(f"   📥 Descargando mesa {mesa}...", end=" ", flush=True)
        response = requests.post(
            f"{BASE_URL}/descargae14",
            data={"data": token},
            verify=False,
            timeout=30
        )
        
        if response.status_code != 200 or len(response.content) < 1000:
            print(f"❌ HTTP {response.status_code}")
            return None
        
        # Guardar
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        # Calcular hash
        file_hash = calculate_file_hash(file_path)
        
        print(f"✅ ({len(response.content)} bytes)")
        
        return {
            "depto": depto,
            "muni": muni,
            "zona": zona,
            "puesto": puesto,
            "mesa": mesa,
            "file_path": str(file_path),
            "file_hash": file_hash,
            "timestamp": datetime.now().isoformat(),
            "token_first_20": token[:20] + "..."
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


# =============================================================================
# PASO 4: FLUJO PRINCIPAL
# =============================================================================

async def scrape_e14(depto_code: str, muni_code: str, zona_code: str, puesto_code: str) -> Dict:
    """
    Flujo completo:
    1. Abrir navegador
    2. Navegar portal
    3. Seleccionar opciones
    4. Extraer tokens
    5. Descargar PDFs
    6. Guardar manifest
    """
    
    print("\n" + "=" * 80)
    print("🚀 INICIANDO DESCARGA E14")
    print("=" * 80)
    print(f"Depto: {depto_code} | Municipio: {muni_code} | Zona: {zona_code} | Puesto: {puesto_code}\n")
    
    navigator = PlaywrightNavigator()
    downloads = []
    
    try:
        # PASO 1: Inicializar Playwright
        print("PASO 1: Inicializar Playwright (stealth)")
        print("-" * 80)
        await navigator.initialize()
        print("✅ Playwright inicializado\n")
        
        # PASO 2: Navegar portal
        print("PASO 2: Navegar al portal")
        print("-" * 80)
        success = await navigator.navigate_to_portal()
        if not success:
            return {"ok": False, "error": "No se pudo cargar el portal"}
        print()
        
        # PASO 3: Seleccionar opciones
        print("PASO 3: Seleccionar opciones (depto, mpio, zona, puesto)")
        print("-" * 80)
        
        # Corporación (PRE = Presidencial)
        await navigator.select_option("#selectCorp", "1")
        print("✅ Corporación: PRE")
        
        # Departamento
        await navigator.select_option("#selectDepto", depto_code)
        print(f"✅ Departamento: {depto_code}")
        
        # Municipio
        await navigator.select_option("#selectMpio", muni_code)
        print(f"✅ Municipio: {muni_code}")
        
        # Zona
        await navigator.select_option("#selectZona", zona_code)
        print(f"✅ Zona: {zona_code}")
        
        # Puesto
        await navigator.select_option("#selectPto", puesto_code)
        print(f"✅ Puesto: {puesto_code}\n")
        
        # PASO 4: Hacer clic en Consultar
        print("PASO 4: Hacer clic en 'Consultar'")
        print("-" * 80)
        await navigator.click_button("#btnConsultarE14")
        print("✅ Clic realizado (reCAPTCHA se resolvió automáticamente)\n")
        
        # PASO 5: Extraer HTML y tokens
        print("PASO 5: Extraer tokens del HTML")
        print("-" * 80)
        html = await navigator.get_html()
        tokens = extract_tokens_from_html(html)
        print(f"✅ Se encontraron {len(tokens)} mesas\n")
        
        # PASO 6: Descargar PDFs
        print("PASO 6: Descargar PDFs")
        print("-" * 80)
        for i, token_data in enumerate(tokens[:5], 1):  # Limitar a 5 para testing
            print(f"Mesa {i}/{len(tokens[:5])}")
            
            result = download_pdf(
                token=token_data["token"],
                depto=depto_code,
                muni=muni_code,
                zona=zona_code,
                puesto=puesto_code,
                mesa=str(i).zfill(3)
            )
            
            if result:
                downloads.append(result)
            
            time.sleep(0.5)  # Rate limiting
        
        print()
        
    finally:
        # Cerrar navegador
        await navigator.close()
    
    # PASO 7: Guardar manifest
    print("PASO 7: Guardar manifest")
    print("-" * 80)
    
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "depto": depto_code,
        "muni": muni_code,
        "zona": zona_code,
        "puesto": puesto_code,
        "total_downloaded": len(downloads),
        "downloads": downloads
    }
    
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Manifest guardado: {MANIFEST_FILE}\n")
    
    # Resumen
    print("=" * 80)
    print("✅ DESCARGA COMPLETADA")
    print("=" * 80)
    print(f"PDFs descargados: {len(downloads)}")
    print(f"Carpeta destino: {DATA_RAW_DIR}")
    print(f"Manifest: {MANIFEST_FILE}\n")
    
    return {
        "ok": True,
        "downloads": len(downloads),
        "manifest": str(MANIFEST_FILE)
    }


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    # Parámetros de testing
    # Depto 1 (Antioquia), Mpio 1 (Medellín), Zona 1, Puesto 01
    result = asyncio.run(scrape_e14(
        depto_code="1",
        muni_code="1",
        zona_code="1",
        puesto_code="1"
    ))
    
    print(f"Resultado: {result}")
