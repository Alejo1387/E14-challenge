# =============================================================================
# playwright_inspect.py — Inspeccionar estructura HTML del portal
# =============================================================================
# OBJETIVO: Ver qué elementos REALMENTE existen en el portal
# para poder usar los selectores CSS correctos
# =============================================================================

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import json

BASE_URL = "https://e14_pres1v_2022.registraduria.gov.co"
OUTPUT_DIR = Path(__file__).parent / "debug_playwright"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

async def inspect_portal():
    """
    Inspecciona el portal y guarda información útil sobre su estructura.
    """
    
    print("\n" + "=" * 80)
    print("🔍 INSPECCIONANDO ESTRUCTURA DEL PORTAL")
    print("=" * 80 + "\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # headless=True = invisible
        context = await browser.new_context()
        page = await context.new_page()
        
        print("📥 Cargando portal...")
        await page.goto(BASE_URL, wait_until="networkidle")
        print("✅ Portal cargado\n")
        
        # Obtener HTML
        html_content = await page.content()
        
        # Guardar HTML completo
        html_file = OUTPUT_DIR / "portal_structure.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ HTML completo guardado: {html_file}\n")
        
        # Parsear con BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        # ====================================================================
        # BUSCAR SELECTORES IMPORTANTES
        # ====================================================================
        
        print("📋 ELEMENTOS ENCONTRADOS:")
        print("-" * 80)
        
        # Buscar TODOS los <select>
        selects = soup.find_all("select")
        print(f"\n🔹 SELECTORES <select> ({len(selects)} encontrados):")
        for i, select in enumerate(selects):
            select_id = select.get("id", "SIN ID")
            select_name = select.get("name", "SIN NAME")
            options_count = len(select.find_all("option"))
            print(f"   {i+1}. ID='{select_id}' | NAME='{select_name}' | Opciones: {options_count}")
        
        # Buscar TODOS los <button>
        buttons = soup.find_all("button")
        print(f"\n🔹 BOTONES <button> ({len(buttons)} encontrados):")
        for i, btn in enumerate(buttons[:10]):  # Mostrar primeros 10
            btn_id = btn.get("id", "SIN ID")
            btn_name = btn.get("name", "SIN NAME")
            btn_text = btn.get_text(strip=True)[:50]
            btn_type = btn.get("type", "SIN TYPE")
            print(f"   {i+1}. ID='{btn_id}' | NAME='{btn_name}' | TYPE='{btn_type}' | TEXT='{btn_text}'")
        
        # Buscar TODOS los <input>
        inputs = soup.find_all("input")
        print(f"\n🔹 INPUTS <input> ({len(inputs)} encontrados):")
        for i, inp in enumerate(inputs[:10]):
            inp_id = inp.get("id", "SIN ID")
            inp_name = inp.get("name", "SIN NAME")
            inp_type = inp.get("type", "SIN TYPE")
            print(f"   {i+1}. ID='{inp_id}' | NAME='{inp_name}' | TYPE='{inp_type}'")
        
        # Buscar FORMULARIOS
        forms = soup.find_all("form")
        print(f"\n🔹 FORMULARIOS <form> ({len(forms)} encontrados):")
        for i, form in enumerate(forms):
            form_id = form.get("id", "SIN ID")
            form_name = form.get("name", "SIN NAME")
            form_method = form.get("method", "SIN METHOD")
            form_action = form.get("action", "SIN ACTION")
            print(f"   {i+1}. ID='{form_id}' | NAME='{form_name}' | METHOD='{form_method}' | ACTION='{form_action}'")
        
        # Buscar scripts (a veces los nombres de API están aquí)
        scripts = soup.find_all("script", src=True)
        print(f"\n🔹 SCRIPTS EXTERNOS ({len(scripts)} encontrados):")
        for i, script in enumerate(scripts[:10]):
            src = script.get("src", "SIN SRC")
            print(f"   {i+1}. SRC='{src}'")
        
        # ====================================================================
        # GUARDA JSON CON LA ESTRUCTURA
        # ====================================================================
        
        structure = {
            "total_selects": len(selects),
            "selects": [
                {
                    "id": select.get("id", "SIN ID"),
                    "name": select.get("name", "SIN NAME"),
                    "options_count": len(select.find_all("option"))
                }
                for select in selects
            ],
            "total_buttons": len(buttons),
            "buttons": [
                {
                    "id": btn.get("id", "SIN ID"),
                    "name": btn.get("name", "SIN NAME"),
                    "type": btn.get("type", "SIN TYPE"),
                    "text": btn.get_text(strip=True)[:50]
                }
                for btn in buttons[:10]
            ]
        }
        
        json_file = OUTPUT_DIR / "portal_structure.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Estructura guardada en JSON: {json_file}")
        
        await context.close()
        await browser.close()
        
        print("\n" + "=" * 80)
        print("🎯 SIGUIENTES PASOS:")
        print("=" * 80)
        print("1. Abre 'portal_structure.html' en tu navegador para VER el formulario real")
        print("2. Usa F12 (DevTools) para inspeccionar los selectores correctos")
        print("3. Actualiza playwright_test.py con los selectores reales")
        print()

if __name__ == "__main__":
    asyncio.run(inspect_portal())
