# ========================================
# SCRAPER E-14 MEJORADO
# Proyecto para auditar elecciones en Colombia
# ========================================
# Este script descarga PDFs de manera INTELIGENTE:
# - Recorre la cadena de selectores del portal (varios POST HTML)
# - Saca tokens por mesa del HTML devuelto por /consultarE14
# - Descarga cada PDF por POST /descargae14
#
# --- MAPA "niño de 5 años" de los desplegables reales del API (importante) ---
# El menú lateral dice "Departamentos" pero el primer POST /selectDepto devuelve
# opciones como "001 - MEDELLÍN": en la práctica son MUNICIPIOS (valor interno).
# El segundo POST /selectMpio devuelve "ZONA 01", "ZONA 02"... (zonas).
# El tercer POST /selectZona devuelve puestos de votación ("01 - ESCUELA...").
# Luego /consultarE14 debe devolver el HTML con botones por mesa.
#
# --- BLOQUEO CONOCIDO: reCAPTCHA ---
# Al pulsar "Consultar" el navegador manda g-recaptcha-response. Sin eso el
# servidor suele responder 500 en /consultarE14. Para pruebas puedes copiar el
# token del navegador (vida corta) a la variable E14_RECAPTCHA_TOKEN.
# Solución de producción: Playwright/Puppeteer o integración de resolución de captcha.
#
# --- Dónde guardamos los PDF ---
# Ver config.py: DATA_RAW_DIR = E14-challenge/data/raw/...
# Ruta objetivo: dept/muni/zona/puesto/mesa.pdf; si falta nombre oficial, puesto "00".

# ============================================================================
# IMPORTACIONES
# ============================================================================

import os  # Leer variables de entorno (por ejemplo token de reCAPTCHA copiado desde el navegador)
import sys  # Para ajustar la codificación de la consola en Windows (evitar errores con emojis)

import requests  # Para hacer peticiones HTTP (POST, GET)
import urllib3  # Para manejar conexiones HTTPS
from bs4 import BeautifulSoup  # Para PARSEAR (leer) HTML
import re  # Para EXPRESIONES REGULARES (buscar patrones en texto)
import time  # Para esperar entre peticiones (no sobrecargar servidor)
import json  # Para manejar JSON
import argparse
from typing import List, Dict, Optional, Tuple  # Tipos para listas, dicts, opcionales y tuplas
from pathlib import Path  # Para trabajar con rutas
from urllib.parse import unquote  # Decodifica nombres de archivo raros que vienen en cabeceras HTTP

# En Windows la consola a veces usa cp1252 y revienta al imprimir emojis (UnicodeEncodeError).
# Forzamos UTF-8 cuando el terminal lo permite.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Importar configuración
from config import (
    BASE_URL,  # URL base del servidor
    HOME_URL,  # URL de la página principal
    AVANCE_DEPTO_URL,  # URL para obtener departamentos
    SELECT_MPIO_URL,  # URL para obtener municipios
    SELECT_ZONA_URL,  # URL para obtener zonas
    CONSULTAR_E14_URL,  # URL para obtener mesas + tokens
    DESCARGA_URL,  # URL para descargar PDF
    OUTPUT_DIR,  # Carpeta donde guardar PDFs
    TIMEOUT,  # Tiempo máximo de espera (segundos)
    VERIFY_SSL,  # Si verificar certificado SSL
    REQUEST_DELAY_SECONDS,
    MAX_RETRIES,
)

# ============================================================================
# DESACTIVAR ADVERTENCIAS DE SSL
# ============================================================================
# Python nos avisa cuando usamos verify=False (por seguridad)
# Esta línea dice: "Está bien, lo sabemos, no avises"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# =============================================================================
# PATRÓN DEL NOMBRE OFICIAL DEL PDF (lo explicó tu enunciado del proyecto)
# =============================================================================
# Ejemplo real: 5036317_E14_PRE_X_01_001_001_XX_01_031_X_XXX.pdf
#              [kit] _E14_ [corp]_[ronda]_[depto2]_[muni3]_[zona3]_[res]_[puesto]_[mesa3]...
# Con esto podemos guardar en: data/raw/01/001/001/01/031.pdf
# Si NO tuviéramos esta regex, solo podríamos adivinar carpetas y tu compañero
# no encontraría los archivos donde espera.
E14_FILENAME_RE = re.compile(
    r"^(\d+)_E14_([A-Z]{3})_([^_]+)_(\d{2})_(\d{3})_(\d{3})_([A-Z0-9]+)_(\d+)_(\d{3})"
)


def _filename_from_content_disposition(header_value: str) -> Optional[str]:
    """
    El servidor a veces dice: "te mando un archivo y se llama así".
    Eso viene en la cabecera Content-Disposition. Esta función saca solo el nombre.

    Si NO existiera, guardaríamos siempre con un nombre inventado y perderíamos
    el número de kit (form_serial) y la ruta correcta de puesto/mesa.
    """
    if not header_value:
        return None
    # Forma moderna: filename*=UTF-8''nombre%20con%20espacios.pdf
    m_star = re.search(r"filename\*\s*=\s*([^;]+)", header_value, re.IGNORECASE)
    if m_star:
        value = m_star.group(1).strip()
        if "''" in value:
            value = value.split("''", 1)[1]
        return unquote(value.strip().strip('"'))
    # Forma clásica: filename="archivo.pdf"
    m_quot = re.search(r'filename\s*=\s*"([^"]+)"', header_value, re.IGNORECASE)
    if m_quot:
        return m_quot.group(1)
    # Forma simple: filename=archivo.pdf
    m_plain = re.search(r"filename\s*=\s*([^;]+)", header_value, re.IGNORECASE)
    if m_plain:
        return unquote(m_plain.group(1).strip().strip('"'))
    return None


def _ruta_relativa_desde_nombre_oficial(nombre_limpio: str) -> Optional[Tuple[Path, str]]:
    """
    Convierte el nombre oficial del PDF en (ruta_relatica, form_serial).

    ruta_relatica = Path(depto, muni, zona, puesto, mesa.pdf) — todo relativo a data/raw/

    Devuelve None si el nombre no encaja en el patrón (no podemos confiar).
    """
    solo_nombre = Path(nombre_limpio).name
    m = E14_FILENAME_RE.match(solo_nombre)
    if not m:
        return None
    form_serial = m.group(1)
    dept, muni, zona, _res, puesto, mesa = (
        m.group(4),
        m.group(5),
        m.group(6),
        m.group(7),
        m.group(8),
        m.group(9),
    )
    puesto_norm = f"{int(puesto):02d}"
    mesa_norm = f"{int(mesa):03d}"
    rel = Path(dept) / muni / zona / puesto_norm / f"{mesa_norm}.pdf"
    return rel, form_serial


# ============================================================================
# CLASE PRINCIPAL: SCRAPER E14
# ============================================================================

class ScraperE14:
    """
    Scraper profesional para descargar formularios E-14 de la Registraduría.
    
    FLUJO GENERAL:
    1. Obtiene lista de departamentos
    2. Para cada departamento:
       - Obtiene municipios
       - Para cada municipio:
         - Obtiene zonas
         - Para cada zona:
           - Obtiene mesas (HTML)
           - Extrae tokens del HTML
           - Descarga PDFs usando tokens
    
    EJEMPLO DE USO:
        scraper = ScraperE14()
        scraper.obtener_departamentos()
    """
    
    def __init__(self):
        """
        PASO 0: INICIALIZAR EL SCRAPER
        ================================
        
        Aquí preparamos:
        - La sesión HTTP (para mantener conexión abierta)
        - Headers (información que le enviamos al servidor)
        - JWT Token (para autenticación)
        """
        
        # Session = mantiene la conexión abierta + guarda cookies
        # Es como "mantener la llamada telefónica abierta" en lugar de colgar y volver a llamar
        self.session = requests.Session()
        
        # Headers = información que le enviamos al servidor
        # Decimos: "Hola, soy un navegador Chrome descargando esto"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            # Muchas rutas del portal responden JSON si parecen AJAX (como jQuery $.ajax).
            "X-Requested-With": "XMLHttpRequest",
            "Referer": BASE_URL + "/",
            "Origin": BASE_URL,
        }
        
        # Asignamos headers a la sesión (se usan en todas las peticiones)
        self.session.headers.update(self.headers)
        
        # Variable para almacenar el JWT token del servidor
        # El servidor lo genera cuando cargas la página
        # Es OBLIGATORIO para los requests a /avanceDepto, /selectMpio, etc
        self.jwt_token = None
        
        # Variable para contar cuántos PDFs descargamos
        self.pdf_count = 0
        
        # Variable para contar errores
        self.error_count = 0
        
        print("✅ ScraperE14 inicializado correctamente")
        print(f"📁 Carpeta de salida: {OUTPUT_DIR}")
        
        # PASO CRÍTICO: Obtener el JWT token desde la página principal
        print("\n🔐 Obteniendo JWT token del servidor...")
        self.obtener_jwt_token()
        
        if not self.jwt_token:
            print("⚠️  Advertencia: No se pudo obtener JWT token")
        else:
            print(f"✅ JWT token obtenido correctamente")
        
        print()
    
    # ========================================================================
    # MÉTODO 0: OBTENER JWT TOKEN DEL SERVIDOR
    # ========================================================================
    
    def obtener_jwt_token(self):
        """
        PASO CRÍTICO: OBTENER JWT TOKEN
        ================================
        
        El servidor REQUIERE un JWT token para autenticación en:
        - /avanceDepto
        - /selectMpio
        - /selectZona
        - /consultarE14
        
        El token se obtiene desde el ENDPOINT: /auth/csrf
        Este endpoint devuelve un JSON con el token
        
        CÓMO FUNCIONA:
        1. Hago GET a /auth/csrf
        2. El servidor devuelve: {"token": "eyJ0eXAi...", ...}
        3. Extraigo el token
        4. Lo guardo en self.jwt_token
        5. Lo uso en todos los requests posteriores
        """
        
        try:
            # PASO 1: Hacer GET al endpoint /auth/csrf
            # Este endpoint genera y devuelve un nuevo JWT token
            
            print("   📥 Solicitando JWT token del endpoint /auth/csrf...")
            
            csrf_url = BASE_URL + "/auth/csrf"
            
            response = self.session.get(
                csrf_url,
                verify=VERIFY_SSL,
                timeout=TIMEOUT
            )
            
            # Verificar que la carga fue exitosa
            if response.status_code != 200:
                print(f"   ❌ Error al cargar /auth/csrf (código {response.status_code})")
                return
            
            # PASO 2: Parsear la respuesta JSON
            # El servidor devuelve algo como:
            # {"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", ...}
            
            try:
                import json
                data = json.loads(response.text)
                
                # Extraer el token del JSON
                if 'token' in data:
                    self.jwt_token = data['token']
                    print(f"   ✅ Token obtenido: {self.jwt_token[:50]}...")
                else:
                    print(f"   ⚠️  Respuesta no contiene 'token'")
                    print(f"   Contenido: {response.text[:200]}")
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ Error al parsear JSON: {e}")
                print(f"   Respuesta: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT al obtener token")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ ERROR DE CONEXIÓN al obtener token")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    # ========================================================================
    # ========================================================================
    
    def hacer_peticion(self, url: str, data: Optional[Dict] = None) -> Optional[str]:
        """
        PASO 1A: FUNCIÓN AUXILIAR - Hacer petición HTTP
        ================================================
        
        Esta es una función que reutilizaremos varias veces.
        Simplifica hacer peticiones POST y maneja errores.
        
        IMPORTANTE: Automáticamente agrega el JWT token a los datos
        
        Args:
            url (str): URL a donde enviar la petición (ej: AVANCE_DEPTO_URL)
            data (Dict): Datos a enviar (ej: {"corp": "PRE", "codDepto": 3})
        
        Returns:
            str: El contenido HTML/JSON que el servidor nos devuelve
                 O None si hay error
        
        EJEMPLO:
            html = scraper.hacer_peticion(AVANCE_DEPTO_URL, data={...})
            # Retorna: "<div>Antioquia</div>..."
        """
        
        try:
            # PASO 1: Preparar los datos
            # Si no hay data, crear diccionario vacío
            if not data:
                data = {}
            
            # PASO 2: AGREGAR JWT TOKEN A LOS DATOS
            # El servidor REQUIERE esto en TODOS los requests
            if self.jwt_token:
                data['token'] = self.jwt_token
            
            # Hacer la petición POST al servidor
            # url = dónde enviar
            # data = qué datos enviar (AHORA INCLUYE TOKEN)
            # verify = verificar certificado SSL (False = no verificar, solo desarrollo)
            # timeout = máximo tiempo de espera en segundos
            
            response = self.session.post(
                url=url,
                data=data,  # INCLUYE TOKEN AUTOMÁTICAMENTE
                verify=VERIFY_SSL,
                timeout=TIMEOUT
            )
            
            # Verificar código de respuesta
            if response.status_code == 200:
                # 200 = éxito ✅
                return response.text  # Retornar el contenido (HTML/JSON)
            else:
                # Otro código = error
                print(f"❌ Error en petición a {url}")
                print(f"   Código: {response.status_code}")
                if response.status_code == 500:
                    print(f"   ERROR 500 - Respuesta del servidor:")
                    # Guardar la respuesta completa en un archivo de debug
                    with open("debug_error_500.html", 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"   [Respuesta guardada en debug_error_500.html]")
                    # Mostrar primeros 200 caracteres
                    print(f"   {response.text[:200]}")
                if response.status_code == 401:
                    print(f"   Warning: Token puede ser inválido o expirado")
                self.error_count += 1
                return None
        
        except requests.exceptions.Timeout:
            # El servidor tardó demasiado
            print(f"❌ TIMEOUT: El servidor tardó más de {TIMEOUT} segundos")
            self.error_count += 1
            return None
        
        except requests.exceptions.ConnectionError:
            # No hay conexión (sin internet, URL mal, etc)
            print(f"❌ ERROR DE CONEXIÓN: No pudimos conectar a {url}")
            self.error_count += 1
            return None
        
        except Exception as e:
            # Cualquier otro error
            print(f"❌ ERROR INESPERADO: {str(e)}")
            self.error_count += 1
            return None
    
    # ========================================================================
    # MÉTODO 2: OBTENER DEPARTAMENTOS
    # ========================================================================
    
    def obtener_departamentos(self) -> List[Dict]:
        """
        PASO 1B: OBTENER LISTA DE DEPARTAMENTOS
        =======================================
        
        Intenta MÚLTIPLES estrategias para obtener los departamentos:
        1. GET a la página principal (para activar sesión)
        2. POST a /selectDepto (o /getCorp) para obtener el HTML con opciones
        
        Retorna:
            Una LISTA de diccionarios con:
            [
                {'code': '05', 'name': 'Antioquia'},
                {'code': '11', 'name': 'Bogotá D.C.'},
                ...
            ]
        """
        
        print("🔍 Obteniendo lista de departamentos...")
        
        # ESTRATEGIA 1: Hacer GET a la página principal para activar la sesión
        try:
            response = self.session.get(
                HOME_URL,
                verify=VERIFY_SSL,
                timeout=TIMEOUT
            )
            print(f"✅ GET a / completado (status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  GET a / falló: {str(e)}")
        
        # ESTRATEGIA 2: Intentar POST a /selectDepto para obtener los departamentos
        print("📡 Intentando POST a /selectDepto...")
        
        # Intentar con parámetros estándar
        data = {
            'corp': 'PRE',
            'codCorp': 1,
            'token': self.jwt_token if self.jwt_token else ''
        }
        
        html = self.hacer_peticion("https://e14_pres1v_2022.registraduria.gov.co/selectDepto", data)
        
        if not html:
            print("❌ POST a /selectDepto falló")
            return []
        
        print(f"\n📄 DEBUG - Respuesta de /selectDepto (primeros 2000 caracteres):")
        print("=" * 80)
        print(html[:2000])
        print("=" * 80 + "\n")
        
        # PASO 2: Parsear HTML con BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # PASO 3: Buscar opciones <option>
        options = soup.find_all('option')
        
        if not options:
            print("❌ No se encontraron opciones en la respuesta")
            return []
        
        # PASO 4: Extraer cada opción
        departamentos = []
        
        for option in options:
            # Obtener el atributo "value"
            code = option.get('value')
            
            # Obtener el texto dentro
            name = option.get_text().strip()
            
            # VALIDACIÓN
            if code and name and code != "" and name != "Seleccionar":
                departamentos.append({
                    'code': code,
                    'name': name
                })
        
        print(f"✅ Se encontraron {len(departamentos)} departamentos")
        return departamentos
    
    # ========================================================================
    # MÉTODO 3: OBTENER MUNICIPIOS (por departamento)
    # ========================================================================
    
    def obtener_municipios(self, depto_code: str) -> List[Dict]:
        """
        PASO 2B: OBTENER MUNICIPIOS DE UN DEPARTAMENTO
        ===============================================
        
        Ahora que tenemos los departamentos, pedimos sus municipios.
        
        FLUJO:
        1. Enviamos POST a /selectMpio
        2. Decimos: "Dame municipios del departamento 05 (Atlantico)"
        3. El servidor responde HTML con opciones: Barranquilla, Soledad, etc
        4. Extraemos los códigos de cada municipio
        
        Args:
            depto_code (str): Código del departamento (ej: "05")
        
        Returns:
            List[Dict]: Lista de municipios
            Ejemplo: [
                {'code': '001', 'name': 'Medellín'},
                {'code': '002', 'name': 'Abejorral'},
            ]
        """
        
        print(f"   📍 Obteniendo municipios para depto: {depto_code}")
        
        # PASO 1: Preparar datos para enviar al servidor
        # ESTRUCTURA CORRECTA (basada en Network tab):
        # - corp: "PRE" = tipo de elección (Presidencial)
        # - codDepto: código del departamento (ej: 05)
        # - codCorp: 1 = siempre 1 (significado interno del sistema)
        # - token: se agrega AUTOMÁTICAMENTE en hacer_peticion()
        
        data = {
            'corp': 'PRE',           # Siempre "PRE" para elecciones presidenciales
            'codDepto': depto_code,  # Código del departamento
            'codCorp': 1,            # Siempre 1 (constante del sistema)
            # 'token' se agrega automáticamente en hacer_peticion()
        }
        
        # PASO 2: Hacer petición al servidor
        # Llamamos a nuestro método auxiliar hacer_peticion()
        # Le pasamos la URL y los datos
        # hacer_peticion() AUTOMÁTICAMENTE agrega el JWT token
        # El servidor nos devuelve HTML con municipios
        
        html = self.hacer_peticion(SELECT_MPIO_URL, data=data)
        
        if not html:
            # Si html es None o vacío, significa que hubo un error
            print(f"   ❌ No se pudieron obtener municipios para {depto_code}")
            return []  # Retornar lista vacía
        
        # DEBUG: Guardar HTML a archivo para inspección
        debug_file = "debug_selectMpio.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"   📝 HTML guardado en {debug_file}")
        
        # PASO 3: Parsear HTML con BeautifulSoup
        # Convertir el HTML crudo en un diccionario que podemos navegar
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # PASO 4: Buscar todas las opciones <option>
        # El HTML devuelve algo como:
        # <option value="001">Medellín</option>
        # <option value="002">Abejorral</option>
        # Buscamos TODAS las <option> del HTML
        
        options = soup.find_all('option')
        
        # PASO 5: Extraer cada opción
        municipios = []
        
        for option in options:
            # Obtener el atributo "value" (ej: "001")
            code = option.get('value')
            
            # Obtener el texto dentro (ej: "Medellín")
            # .strip() elimina espacios en blanco
            name = option.get_text().strip()
            
            # VALIDACIÓN: Solo guardar si es válido
            # - code debe existir y no ser ""
            # - name debe existir y no ser "Seleccionar"
            if code and name and code != "" and name != "Seleccionar":
                municipios.append({
                    'code': code,
                    'name': name
                })
        
        # PASO 6: Retornar la lista de municipios
        print(f"   ✅ Se encontraron {len(municipios)} municipios")
        return municipios
    
    # ========================================================================
    # MÉTODO 4: OBTENER ZONAS (por municipio)
    # ========================================================================
    
    def obtener_zonas(self, depto_code: str, muni_code: str) -> List[Dict]:
        """
        PASO 3: OBTENER ZONAS DE UN MUNICIPIO
        ======================================
        
        Mismo proceso que municipios, pero para zonas electorales.
        
        Args:
            depto_code (str): Código del departamento (ej: "05")
            muni_code (str): Código del municipio (ej: "001")
        
        Returns:
            List[Dict]: Lista de zonas
            [
                {'code': '001', 'name': 'Zona 1'},
                {'code': '002', 'name': 'Zona 2'},
            ]
        """
        
        print(f"      🗺️  Obteniendo zonas para municipio: {muni_code}")
        
        # PASO 1: Preparar datos para enviar al servidor
        # ESTRUCTURA CORRECTA (basada en Network tab):
        # - corp: "PRE" = tipo de elección (Presidencial)
        # - codDepto: código del departamento
        # - codMunicipio: código del municipio
        # - codCorp: 1 = siempre 1
        # - token: se agrega AUTOMÁTICAMENTE
        
        data = {
            'corp': 'PRE',           # Siempre "PRE"
            'codDepto': depto_code,  # Código del departamento
            'codMunicipio': muni_code,  # Código del municipio
            'codCorp': 1,            # Siempre 1
            # 'token' se agrega automáticamente en hacer_peticion()
        }
        
        # PASO 2: Hacer petición
        # hacer_peticion() AUTOMÁTICAMENTE agrega el JWT token
        html = self.hacer_peticion(SELECT_ZONA_URL, data=data)
        
        if not html:
            print(f"      ❌ No se pudieron obtener zonas")
            return []
        
        # PASO 3: Parsear HTML (idéntico a municipios)
        soup = BeautifulSoup(html, 'html.parser')
        
        # PASO 4: Buscar todas las opciones <option>
        options = soup.find_all('option')
        
        # PASO 5: Extraer zonas
        zonas = []
        
        for option in options:
            # Obtener código
            code = option.get('value')
            
            # Obtener nombre
            name = option.get_text().strip()
            
            # Validación (igual que antes)
            if code and name and code != "" and name != "Seleccionar":
                zonas.append({
                    'code': code,
                    'name': name
                })
        
        # PASO 6: Retornar
        print(f"      ✅ Se encontraron {len(zonas)} zonas")
        return zonas
    
    # ========================================================================
    # MÉTODO 5: OBTENER MESAS + EXTRAER TOKENS (REGEX)
    # ========================================================================
    
    def obtener_mesas_y_tokens(self, depto_code: str, muni_code: str, zona_code: str) -> List[Dict]:
        """
        PASO 4: OBTENER MESAS + EXTRAER TOKENS USANDO REGEX
        ===================================================
        
        Este es el método MÁS IMPORTANTE del scraper.
        
        Lo que hace:
        1. POST a /consultarE14 con depto/municipio/zona
        2. Recibe HTML con botones de mesas
        3. EXTRAE los tokens del HTML usando EXPRESIONES REGULARES (REGEX)
        4. Combina números de mesa con tokens
        5. Retorna lista de mesas con sus tokens
        
        HTML que recibimos:
        ───────────────────
        <button onclick="descargarE14('rI7370uqOC7xrhtfX3r98oMtTxufy...')">
            Mesa 001
        </button>
        <button onclick="descargarE14('rI7370uqOC7xrhtfX3r98i3xTIs0Lk...')">
            Mesa 002
        </button>
        
        Lo que extraemos:
        ────────────────
        [
            {'num_mesa': '001', 'token': 'rI7370uqOC7xrhtfX3r98oMtTxufy...'},
            {'num_mesa': '002', 'token': 'rI7370uqOC7xrhtfX3r98i3xTIs0Lk...'},
        ]
        
        Args:
            depto_code (str): Código del departamento (ej: "05")
            muni_code (str): Código del municipio (ej: "001")
            zona_code (str): Código de la zona (ej: "001")
        
        Returns:
            List[Dict]: Lista de mesas con tokens
        """
        
        # PASO 1: Preparar datos a enviar al servidor
        # ESTRUCTURA CORRECTA (basada en Network tab):
        # - corp: "PRE" = tipo de elección
        # - codDepto: código del departamento
        # - codMpio: código del municipio (cambié de codMunicipio a codMpio)
        # - codZona: código de la zona
        # - codCorp: 1 = siempre 1
        # - token: se agrega AUTOMÁTICAMENTE en hacer_peticion()
        
        data = {
            'corp': 'PRE',           # Siempre "PRE"
            'codDepto': depto_code,  # Código del departamento
            'codMpio': muni_code,    # Código del municipio (CAMBIO: era codMunicipio)
            'codZona': zona_code,    # Código de la zona
            'codCorp': 1,            # Siempre 1
            # 'token' se agrega automáticamente en hacer_peticion()
        }
        # El sitio usa reCAPTCHA invisible antes de consultar mesas. Sin este campo el
        # servidor suele responder 500. Para pruebas: copia "g-recaptcha-response" desde
        # DevTools (petición consultarE14) y exporta E14_RECAPTCHA_TOKEN=...
        # En producción robusta: Playwright u otro navegador automatizado.
        _recaptcha = os.environ.get("E14_RECAPTCHA_TOKEN", "").strip()
        if _recaptcha:
            data["g-recaptcha-response"] = _recaptcha
        
        print(f"         🔍 Extrayendo mesas y tokens de zona: {zona_code}")
        
        # DEBUG: Mostrar parámetros a enviar
        print(f"         📋 DEBUG - Parámetros a enviar:")
        print(f"            - corp: PRE")
        print(f"            - codDepto: {depto_code}")
        print(f"            - codMpio: {muni_code}")
        print(f"            - codZona: {zona_code}")
        print(f"            - codCorp: 1")
        
        # PASO 2: Hacer petición al servidor
        # Le decimos: "Dame las mesas de esta zona"
        # hacer_peticion() AUTOMÁTICAMENTE agrega el JWT token
        
        html = self.hacer_peticion(CONSULTAR_E14_URL, data=data)
        
        if not html:
            # Si no recibimos HTML, hubo un error
            print(f"         ❌ No se pudieron obtener mesas")
            return []
        
        # DEBUG: Mostrar respuesta
        print(f"\n         📄 DEBUG - Respuesta (primeros 1000 caracteres):")
        print("         " + "=" * 80)
        print(html[:1000])
        print("         " + "=" * 80 + "\n")
        
        # PASO 3: EXTRAER TOKENS USANDO REGEX (EXPRESIONES REGULARES)
        # ============================================================
        # 
        # El HTML tiene botones así:
        # <button onclick="descargarE14('TOKEN_AQUI_MUY_LARGO')">Mesa 001</button>
        #
        # Necesitamos EXTRAER solo los tokens usando REGEX
        
        # REGEX PATTERN 1: Buscar tokens en onclick
        # Explicación detallada:
        # ─────────────────────
        # r"..." = raw string (las \ no se escapan)
        # onclick= = busca literal "onclick="
        # \" = comilla doble (escapada porque estamos en string)
        # descargarE14\( = literal "descargarE14(" (paréntesis escapado)
        # ' = comilla simple de apertura
        # ([^']+) = GRUPO 1: Captura TODO lo que NO sea comilla simple
        #          [^'] = "negación" (NO comillas simples)
        #          + = "uno o más caracteres"
        # ' = comilla simple de cierre
        # \) = paréntesis de cierre (escapado)
        
        token_pattern = r"onclick=\"descargarE14\('([^']+)'\)"
        
        # re.findall() busca TODAS las coincidencias
        # Retorna una LISTA con todos los tokens encontrados
        # Ejemplo: ['token1', 'token2', 'token3']
        
        tokens = re.findall(token_pattern, html)
        
        print(f"         ✅ Se encontraron {len(tokens)} tokens")
        
        # PASO 4: EXTRAER NÚMEROS DE MESA usando REGEX
        # ============================================
        #
        # El HTML tiene:
        # <button>Mesa 001</button>
        # <button>Mesa  002</button>   (puede haber múltiples espacios)
        # <button>Mesa   003</button>
        #
        # Necesitamos extraer: 001, 002, 003
        
        # REGEX PATTERN 2: Buscar números de mesa
        # Explicación:
        # ──────────
        # Mesa = busca literal "Mesa"
        # \s+ = uno O MÁS espacios en blanco
        # (\d+) = GRUPO 1: Captura uno O MÁS dígitos
        
        mesa_pattern = r"Mesa\s+(\d+)"
        
        # re.findall() retorna lista de números de mesa
        # Ejemplo: ['001', '002', '003']
        
        num_mesas = re.findall(mesa_pattern, html)
        
        # PASO 5: COMBINAR MESAS CON TOKENS
        # =================================
        #
        # Ahora tenemos:
        # tokens = ['token1', 'token2', 'token3']
        # num_mesas = ['001', '002', '003']
        #
        # Necesitamos combinar en PARALELO:
        # [
        #     {'num_mesa': '001', 'token': 'token1'},
        #     {'num_mesa': '002', 'token': 'token2'},
        #     {'num_mesa': '003', 'token': 'token3'},
        # ]
        
        mesas = []
        
        # Iterar sobre todos los tokens
        for i, token in enumerate(tokens):
            # enumerate() da el ÍNDICE y el VALOR
            # i = 0, 1, 2, ...
            # token = 'token1', 'token2', ...
            
            # Si tenemos número de mesa, usarlo; si no, generar uno
            if i < len(num_mesas):
                # Usar el número de mesa capturado
                num_mesa = num_mesas[i]
            else:
                # Si falta número de mesa, generar automáticamente
                # (esto evita errores si hay mesas sin número visible)
                num_mesa = str(i+1).zfill(3)  # zfill(3) = "01" → "001"
            
            # Crear diccionario con mesa + token
            mesas.append({
                'num_mesa': num_mesa,
                'token': token
            })
        
        # PASO 6: Retornar lista de mesas con tokens
        print(f"         ✅ Se extrajeron {len(mesas)} mesas con tokens")
        return mesas

    def limpiar_nombre_para_carpeta(self, texto: str) -> str:
        """
        Convierte un nombre a formato seguro para carpetas.
        """
        texto = texto.strip()
        texto = re.sub(r"[\\/:*?\"<>|]", "_", texto)
        texto = re.sub(r"\s+", "_", texto)
        return texto

    def descargar_pdf_por_token(
        self,
        token_pdf: str,
        ruta_fallback_relativa: Path,
    ) -> Tuple[bool, Optional[Path]]:
        """
        Descarga un PDF desde /descargae14 usando el token de UNA mesa.

        Devuelve (éxito, ruta_relativa_desde_OUTPUT_DIR).
        Intenta leer el nombre oficial del archivo (Content-Disposition) para
        guardar en data/raw/dept/muni/zona/puesto/mesa.pdf. Si no puede, usa
        ruta_fallback_relativa (por ejemplo .../00/031.pdf cuando aún no sabemos puesto).
        """
        data = {"data": token_pdf}
        destino_final_rel: Optional[Path] = None

        for intento in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.post(
                    DESCARGA_URL,
                    data=data,
                    verify=VERIFY_SSL,
                    timeout=TIMEOUT,
                    allow_redirects=True,
                )

                if response.status_code != 200:
                    print(
                        f"            ❌ Descarga falló (status {response.status_code}) "
                        f"[intento {intento}/{MAX_RETRIES}]"
                    )
                    continue

                nombre_srv = _filename_from_content_disposition(
                    response.headers.get("Content-Disposition", "")
                )
                parsed = _ruta_relativa_desde_nombre_oficial(nombre_srv) if nombre_srv else None
                if parsed:
                    destino_final_rel, _form_serial = parsed
                else:
                    destino_final_rel = ruta_fallback_relativa

                ruta_abs = OUTPUT_DIR / destino_final_rel
                ruta_abs.parent.mkdir(parents=True, exist_ok=True)

                contenido = response.content
                if not contenido.startswith(b"%PDF"):
                    print(
                        f"            ❌ Respuesta no parece PDF "
                        f"[intento {intento}/{MAX_RETRIES}]"
                    )
                    continue

                if ruta_abs.exists() and ruta_abs.stat().st_size == len(contenido):
                    return True, destino_final_rel

                with open(ruta_abs, "wb") as f:
                    f.write(contenido)

                self.pdf_count += 1
                return True, destino_final_rel

            except requests.exceptions.RequestException as e:
                print(
                    f"            ❌ Error de red al descargar PDF: {str(e)} "
                    f"[intento {intento}/{MAX_RETRIES}]"
                )

            time.sleep(0.5)

        self.error_count += 1
        return False, None

    def guardar_manifest(self, registros: List[Dict], archivo: Path) -> None:
        """
        Guarda un JSON con el resumen de descargas para reanudar luego.
        """
        payload = {
            "total_registros": len(registros),
            "pdfs_descargados": self.pdf_count,
            "errores": self.error_count,
            "registros": registros,
        }
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def ejecutar_descarga(
        self,
        max_departamentos: int = 1,
        max_municipios: int = 1,
        max_zonas: int = 1,
        max_mesas_por_zona: int = 5,
    ) -> Dict:
        """
        Ejecuta el flujo completo y descarga PDFs.
        """
        departamentos = self.obtener_departamentos()
        if not departamentos:
            return {"ok": False, "motivo": "No se obtuvieron departamentos"}

        departamentos = departamentos[:max_departamentos]
        registros = []

        for depto in departamentos:
            depto_code = depto["code"]
            depto_name = self.limpiar_nombre_para_carpeta(depto["name"])
            print(f"\n🏛️ Departamento {depto_code} - {depto['name']}")

            municipios = self.obtener_municipios(depto_code)[:max_municipios]
            for muni in municipios:
                muni_code = muni["code"]
                muni_name = self.limpiar_nombre_para_carpeta(muni["name"])
                print(f"   🏙️ Municipio {muni_code} - {muni['name']}")

                zonas = self.obtener_zonas(depto_code, muni_code)[:max_zonas]
                for zona in zonas:
                    zona_code = zona["code"]
                    zona_name = self.limpiar_nombre_para_carpeta(zona["name"])
                    print(f"      🗺️ Zona {zona_code} - {zona['name']}")

                    mesas = self.obtener_mesas_y_tokens(depto_code, muni_code, zona_code)
                    mesas = mesas[:max_mesas_por_zona]

                    for mesa in mesas:
                        mesa_num = mesa["num_mesa"].zfill(3)
                        token_pdf = mesa["token"]

                        # "00" = puesto desconocido hasta que el servidor nos diga el nombre real del PDF.
                        ruta_relativa = Path(depto_code) / muni_code / zona_code / "00" / f"{mesa_num}.pdf"
                        ruta_archivo = OUTPUT_DIR / ruta_relativa

                        if ruta_archivo.exists():
                            print(f"         ⏭️ Ya existe, se omite: {ruta_relativa}")
                            registros.append(
                                {
                                    "departamento_code": depto_code,
                                    "departamento_name": depto_name,
                                    "municipio_code": muni_code,
                                    "municipio_name": muni_name,
                                    "zona_code": zona_code,
                                    "zona_name": zona_name,
                                    "mesa_numero": mesa_num,
                                    "token_pdf_prefix": token_pdf[:24],
                                    "pdf_path": str(ruta_relativa),
                                    "status": "SKIPPED_EXISTS",
                                }
                            )
                            continue

                        exito, ruta_final = self.descargar_pdf_por_token(token_pdf, ruta_relativa)
                        ruta_para_registro = ruta_final if (exito and ruta_final) else ruta_relativa
                        status = "DOWNLOADED" if exito else "FAILED"
                        print(f"         {'✅' if exito else '❌'} Mesa {mesa_num} -> {status}")

                        registros.append(
                            {
                                "departamento_code": depto_code,
                                "departamento_name": depto_name,
                                "municipio_code": muni_code,
                                "municipio_name": muni_name,
                                "zona_code": zona_code,
                                "zona_name": zona_name,
                                "mesa_numero": mesa_num,
                                "token_pdf_prefix": token_pdf[:24],
                                "pdf_path": str(ruta_para_registro),
                                "status": status,
                            }
                        )
                        time.sleep(REQUEST_DELAY_SECONDS)

        manifest_path = OUTPUT_DIR / "manifest_descargas.json"
        self.guardar_manifest(registros, manifest_path)

        return {
            "ok": True,
            "manifest_path": str(manifest_path),
            "registros": len(registros),
            "pdfs_descargados": self.pdf_count,
            "errores": self.error_count,
        }
# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Scraper CLI para descarga de formularios E-14"
    )
    parser.add_argument("--max-departamentos", type=int, default=1)
    parser.add_argument("--max-municipios", type=int, default=1)
    parser.add_argument("--max-zonas", type=int, default=1)
    parser.add_argument("--max-mesas", type=int, default=5)
    return parser.parse_args()


def main():
    print("=" * 70)
    print("🚀 SCRAPER E-14 - DESCARGA DE PDFS")
    print("=" * 70)
    print()

    args = parse_args()
    scraper = ScraperE14()
    resultado = scraper.ejecutar_descarga(
        max_departamentos=args.max_departamentos,
        max_municipios=args.max_municipios,
        max_zonas=args.max_zonas,
        max_mesas_por_zona=args.max_mesas,
    )

    print()
    print("=" * 70)
    if not resultado.get("ok"):
        print("❌ EJECUCIÓN FALLIDA")
        print(f"Motivo: {resultado.get('motivo')}")
    else:
        print("✅ EJECUCIÓN COMPLETADA")
        print(f"Registros procesados: {resultado['registros']}")
        print(f"PDFs descargados: {resultado['pdfs_descargados']}")
        print(f"Errores: {resultado['errores']}")
        print(f"Manifest: {resultado['manifest_path']}")
    print("=" * 70)


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()