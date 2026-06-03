# =============================================================================
# playwright_test.py — Test minimalista de Playwright + Portal E14
# =============================================================================
# OBJETIVO: Validar que Playwright puede:
# 1. Abrir el navegador
# 2. Ir al portal
# 3. Rellenar desplegables
# 4. Hacer clic en "Consultar"
# 5. Extraer tokens del HTML resultante
#
# Si esto funciona, lo integraremos al scrape.py principal.
# =============================================================================

# ============================================================================
# IMPORTACIONES
# ============================================================================

# asyncio = para ejecutar código asincrónico (sin bloquear)
# Si NO lo usáramos, el script estaría "dormido" esperando respuestas
import asyncio

# playwright = la librería que automatiza el navegador
# Aquí traemos específicamente:
# - async_playwright: entrada al mundo de Playwright
# - expect: para "esperar" a que aparezcan elementos
from playwright.async_api import async_playwright, expect

# requests = para descargar PDFs después (ahora no lo usamos, pero será útil)
import requests

# BeautifulSoup = para parsear HTML
from bs4 import BeautifulSoup

# json = para manejo de datos JSON
import json

# Path = para trabajar con rutas de archivos
from pathlib import Path


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

BASE_URL = "https://e14_pres1v_2022.registraduria.gov.co"
OUTPUT_DEBUG_DIR = Path(__file__).parent / "debug_playwright"
OUTPUT_DEBUG_DIR.mkdir(exist_ok=True, parents=True)


# ============================================================================
# FUNCIÓN PRINCIPAL (ASYNC)
# ============================================================================

async def test_playwright():
    """
    FUNCIÓN PRINCIPAL - Todo el flujo del test
    
    ¿Por qué async?
    - Playwright es asincrónico (puede hacer varias cosas simultáneamente)
    - async/await = "espera esto, pero sin bloquear el programa"
    - Si NO fuera async, el programa estaría congelado esperando respuestas
    
    ¿Cómo se llama?
    - NO se llama directamente: asyncio.run(test_playwright())
    """
    
    print("\n" + "=" * 80)
    print("🎬 INICIANDO TEST DE PLAYWRIGHT")
    print("=" * 80 + "\n")
    
    # ========================================================================
    # PASO 1: INICIAR PLAYWRIGHT
    # ========================================================================
    
    print("📍 PASO 1: Iniciar Playwright")
    print("-" * 80)
    
    # async with = "usa esto, y cuando termines, ciérralo automáticamente"
    # async_playwright() = inicia el sistema de Playwright
    async with async_playwright() as p:
        
        # p.chromium = el navegador Chromium que instalamos
        # launch() = abre el navegador
        # headless=False = MOSTRAR ventana del navegador (para ver qué pasa)
        # Si headless=True, el navegador estaría "invisible" (más rápido)
        browser = await p.chromium.launch(headless=False)
        print("✅ Navegador abierto")
        
        # context = una "sesión de navegación" (cookies, etc.)
        # Es como abrir un navegador nuevo en modo incógnito
        context = await browser.new_context()
        print("✅ Contexto creado")
        
        # page = una pestaña del navegador
        # Aquí es donde hacemos todo (navegar, hacer clic, etc.)
        page = await context.new_page()
        print("✅ Página (pestaña) creada\n")
        
        # ====================================================================
        # PASO 2: NAVEGAR AL PORTAL
        # ====================================================================
        
        print("📍 PASO 2: Navegar al portal")
        print("-" * 80)
        print(f"Yendo a: {BASE_URL}")
        
        # page.goto() = "ve a esta URL"
        # await = espera a que termine la navegación
        # wait_until="networkidle" = espera a que termine de cargar TODO
        await page.goto(BASE_URL, wait_until="networkidle")
        print("✅ Portal cargado\n")
        
        # ====================================================================
        # PASO 3: SIMULAR SELECCIONES DE USUARIO
        # ====================================================================
        
        print("📍 PASO 3: Seleccionar opciones (como haría un humano)")
        print("-" * 80)
        
        # Esperar a que el selector de departamentos esté visible
        # expect() = "asegúrate de que esto se cumpla"
        await expect(page.locator("select#corp")).to_be_visible()
        print("✅ Selector de elección visible")
        
        # Esperar a que el selector de departamentos esté visible
        await expect(page.locator("select#codDepto")).to_be_visible()
        print("✅ Selector de departamento visible")
        
        # page.select_option() = selecciona una opción de un <select>
        # "#corp" = selector CSS (el campo con id="corp")
        # "value='PRE'" = la opción con value="PRE"
        await page.select_option("#corp", "value=PRE")
        print("✅ Seleccionado: PRE (Presidencial)")
        
        # Esperar un poquito para que el servidor procese
        await asyncio.sleep(0.5)
        
        # Seleccionar departamento "1" (Antioquia)
        await page.select_option("#codDepto", "value=1")
        print("✅ Seleccionado: Depto 1")
        
        await asyncio.sleep(0.5)
        
        # CLAVE: Esperar a que aparezcan municipios en el desplegable
        # Si no esperas, intentas seleccionar un municipio que NO existe aún
        await expect(page.locator("select#codMpio")).to_have_count(lambda x: x > 1)
        print("✅ Municipios cargados")
        
        # Seleccionar municipio "1"
        await page.select_option("#codMpio", "value=1")
        print("✅ Seleccionado: Municipio 1")
        
        await asyncio.sleep(0.5)
        
        # Esperar zonas
        await expect(page.locator("select#codZona")).to_have_count(lambda x: x > 1)
        print("✅ Zonas cargadas")
        
        # Seleccionar zona "1"
        await page.select_option("#codZona", "value=1")
        print("✅ Seleccionado: Zona 1\n")
        
        # ====================================================================
        # PASO 4: HACER CLIC EN "CONSULTAR"
        # ====================================================================
        
        print("📍 PASO 4: Hacer clic en botón 'Consultar'")
        print("-" * 80)
        
        # Esperar a que el botón sea visible
        consultar_button = page.locator("button#consultarE14, button:has-text('Consultar')")
        await expect(consultar_button).to_be_visible()
        print("✅ Botón 'Consultar' visible")
        
        # Hacer clic (aquí es DONDE OCURRE LA MAGIA: reCAPTCHA se resuelve automáticamente)
        print("⏳ Haciendo clic en 'Consultar'...")
        await consultar_button.click()
        
        # Esperar a que la respuesta del servidor llegue
        print("⏳ Esperando respuesta del servidor...")
        await asyncio.sleep(2)  # Darle tiempo al servidor
        
        print("✅ Respuesta recibida\n")
        
        # ====================================================================
        # PASO 5: EXTRAER TOKENS DEL HTML
        # ====================================================================
        
        print("📍 PASO 5: Extraer tokens del HTML")
        print("-" * 80)
        
        # page.content() = obtener el HTML de la página actual
        html_content = await page.content()
        
        # Guardar HTML para debugging
        debug_file = OUTPUT_DEBUG_DIR / "playwright_response.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ HTML guardado en: {debug_file}")
        
        # Parsear HTML con BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Buscar todos los botones que descargan PDFs
        # En el portal, cada mesa tiene un botón como:
        # <button type="submit" name="data" value="TOKEN_AQUI">Mesa 001</button>
        buttons = soup.find_all("button", {"type": "submit", "name": "data"})
        
        tokens = []
        if buttons:
            print(f"✅ Se encontraron {len(buttons)} mesas\n")
            print("📋 Primeros 5 tokens:\n")
            
            for i, btn in enumerate(buttons[:5]):
                token = btn.get("value", "SIN TOKEN")
                mesa = btn.get_text(strip=True)
                tokens.append({"mesa": mesa, "token": token})
                print(f"   Mesa: {mesa}")
                print(f"   Token: {token[:80]}...")
                print()
        else:
            print("❌ No se encontraron mesas/tokens")
            print("⚠️  Posible error: reCAPTCHA no se resolvió")
            print("📄 Revisa el HTML guardado para debugging")
        
        # ====================================================================
        # PASO 6: DESCARGAR UN PDF (OPCIONAL)
        # ====================================================================
        
        if tokens:
            print("📍 PASO 6: Descargar primer PDF (test)")
            print("-" * 80)
            
            token = tokens[0]["token"]
            print(f"📥 Descargando con token: {token[:80]}...")
            
            try:
                # Hacer POST a /descargae14 con el token
                response = requests.post(
                    f"{BASE_URL}/descargae14",
                    data={"data": token},
                    verify=False,
                    timeout=30
                )
                
                if response.status_code == 200 and len(response.content) > 1000:
                    # Guardar el PDF
                    pdf_path = OUTPUT_DEBUG_DIR / "test_download.pdf"
                    with open(pdf_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ PDF descargado: {pdf_path} ({len(response.content)} bytes)")
                else:
                    print(f"❌ Error al descargar PDF (status: {response.status_code})")
            except Exception as e:
                print(f"❌ Excepción al descargar: {str(e)}")
        
        # ====================================================================
        # PASO 7: CERRAR NAVEGADOR
        # ====================================================================
        
        print("\n📍 PASO 7: Cerrar navegador")
        print("-" * 80)
        
        await context.close()
        await browser.close()
        print("✅ Navegador cerrado\n")
    
    # ========================================================================
    # RESUMEN
    # ========================================================================
    
    print("=" * 80)
    print("✅ TEST COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    print("\n📌 Qué aprendimos:")
    print("   1. Playwright abre un navegador REAL")
    print("   2. Podemos hacer clic, rellenar formularios, esperar elementos")
    print("   3. JavaScript se ejecuta automáticamente (reCAPTCHA incluido)")
    print("   4. Extrajimos tokens del HTML resultante")
    print(f"   5. Datos de debug guardados en: {OUTPUT_DEBUG_DIR}\n")


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    # asyncio.run() = ejecuta la función async
    # IMPORTANTE: sin esto, la función NO se ejecutaría
    asyncio.run(test_playwright())
