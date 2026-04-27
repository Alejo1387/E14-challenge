# =============================================================================
# playwright_stealth.py — Playwright INVISIBLE para el WAF
# =============================================================================
# El portal tiene protección anti-bot (WAF). Usaremos técnicas de "stealth"
# para que Playwright parezca un navegador real (no bot).
# =============================================================================

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from pathlib import Path

BASE_URL = "https://e14_pres1v_2022.registraduria.gov.co"
OUTPUT_DEBUG_DIR = Path(__file__).parent / "debug_playwright"
OUTPUT_DEBUG_DIR.mkdir(exist_ok=True, parents=True)


async def test_playwright_stealth():
    """
    Test de Playwright con técnicas STEALTH para pasar el WAF
    """
    
    print("\n" + "=" * 80)
    print("🎬 INICIANDO TEST DE PLAYWRIGHT (STEALTH MODE)")
    print("=" * 80 + "\n")
    
    async with async_playwright() as p:
        # Paso 1: Abrir navegador con opciones anti-detección
        print("📍 PASO 1: Abrir navegador (modo stealth)")
        print("-" * 80)
        
        browser = await p.chromium.launch(
            headless=True,  # Invisible (modo background)
            args=[
                "--disable-blink-features=AutomationControlled",  # NO MOSTRAR que es automatizado
                "--disable-dev-shm-usage",  # Usar más memoria real
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-popup-blocking",
                "--disable-translate",
            ]
        )
        print("✅ Navegador abierto (stealth)\n")
        
        # Paso 2: Crear contexto con User-Agent real
        print("📍 PASO 2: Crear contexto con User-Agent real")
        print("-" * 80)
        
        context = await browser.new_context(
            # User-Agent de Chrome real (2026)
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="es-ES",
            timezone_id="America/Bogota",  # Timezone de Colombia
        )
        
        # Inyectar JavaScript para ocultar automation
        await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-ES', 'es'],
        });
        """)
        
        print("✅ Context creado con User-Agent y timezone correcto\n")
        
        # Paso 3: Crear página
        page = await context.new_page()
        
        # Step 4: Esperar y navegar
        print("📍 PASO 3: Navegar al portal")
        print("-" * 80)
        print(f"Yendo a: {BASE_URL}")
        
        try:
            response = await page.goto(BASE_URL, wait_until="domcontentloaded")
            status = response.status if response else "NO RESPONSE"
            print(f"✅ Respuesta del servidor: {status}\n")
        except Exception as e:
            print(f"❌ Error al navegar: {str(e)}\n")
        
        # Paso 5: Guardar HTML
        print("📍 PASO 4: Verificar si está bloqueado")
        print("-" * 80)
        
        html = await page.content()
        
        # Buscar palabras clave de bloqueo
        if "WAF" in html or "seguridad" in html.lower() or "evento de seguridad" in html.lower():
            print("⚠️  Portal detectó la conexión como bot (WAF)")
            print("📌 Posibles soluciones:")
            print("   1. Usar Puppeteer en lugar de Playwright (otro navegador)")
            print("   2. Agregar delays aleatorios entre acciones")
            print("   3. Usar proxies rotados")
            print("   4. Contactar a la Registraduría para permisos de scraping")
        else:
            print("✅ Portal no bloqueó la conexión")
        
        # Guardar HTML
        debug_file = OUTPUT_DEBUG_DIR / "stealth_response.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"📄 HTML guardado: {debug_file}\n")
        
        # Paso 6: Mostrar primeras líneas del HTML
        print("📍 PASO 5: Contenido del HTML")
        print("-" * 80)
        print(f"Primeros 500 caracteres:\n{html[:500]}\n")
        
        await context.close()
        await browser.close()
    
    print("=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_playwright_stealth())
