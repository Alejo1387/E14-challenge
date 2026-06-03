# =============================================================================
# config.py — "La caja de herramientas con las direcciones y reglas del juego"
# =============================================================================
# Imagina que el scraper es un cartero.
# Este archivo es la libreta donde escribes:
# - La dirección del edificio (URL base)
# - El buzón de cada trámite (cada endpoint)
# - La carpeta donde dejas las cartas (PDFs)
# - Cuánto tiempo esperas antes de rendirte (timeout)
# Si NO existiera este archivo, tendrías que repetir esas direcciones en cada
# script; un solo cambio en la web rompería todo y costaría encontrarlo.

# --- import os: trae funciones para leer variables de entorno del sistema ---
# (por ejemplo un token secreto sin pegarlo en el código).
import os

# --- Path: tipo de dato de Python para rutas de carpetas/archivos que ---
# funcionan igual en Windows, Mac y Linux.
from pathlib import Path

# =============================================================================
# Dónde está "la raíz del proyecto E14" en tu disco
# =============================================================================
# __file__ = "esta ruta: .../config.py"
# .parent = la carpeta donde vive config.py = "Data Sources and Scraping Strategy"
# .parents[1] = sube UN nivel más = carpeta "E14-challenge"
# Si NO calcularas REPO_ROOT así, podrías guardar PDFs dentro de la carpeta
# del scraper por error, y tu compañero buscaría en otro lado.
REPO_ROOT = Path(__file__).resolve().parents[1]

# =============================================================================
# Carpeta oficial para PDFs crudos (lo que pide el enunciado del reto)
# =============================================================================
# Formato acordado: data/raw/{dept}/{muni}/{zona}/{puesto}/{mesa}.pdf
# Esa carpeta vive en la raíz del repo E14-challenge, NO dentro del scraper.
# Si NO existiera DATA_RAW_DIR definida, cada desarrollador guardaría donde le
# parezca y el pipeline (IA, API) se rompería.
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"

# --- mkdir(parents=True): crea la carpeta y todas las padres que falten ---
# exist_ok=True: si ya existe, NO pasa nada (no da error).
# Si NO creáramos la carpeta aquí, el primer guardado de PDF fallaría.
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Alias para no romper código viejo que usa OUTPUT_DIR
# =============================================================================
# scrape.py histórico usaba OUTPUT_DIR; ahora apunta al mismo sitio oficial.
# Si quitáramos OUTPUT_DIR, habría que reescribir muchas líneas de scrape.py.
OUTPUT_DIR = DATA_RAW_DIR

# =============================================================================
# URLs del portal de la Registraduría (elección de desarrollo)
# =============================================================================
# BASE_URL = "puerta principal del edificio en internet".
# Si cambiara el dominio, solo tocas esta línea.
BASE_URL = "https://e14_pres1v_2022.registraduria.gov.co"

# --- Cada ENDPOINT es un "mostrador" distinto dentro del mismo edificio ---
# HOME: página HTML con los menús desplegables (departamento, municipio…).
HOME_ENDPOINT = "/"
# AVANCE_DEPTO: a veces se usa para progreso/listados (según versión del sitio).
AVANCE_DEPTO_ENDPOINT = "/avanceDepto"
# SELECT_MPIO: "dame municipios de este departamento".
SELECT_MPIO_ENDPOINT = "/selectMpio"
# SELECT_ZONA: "dame zonas de este municipio".
SELECT_ZONA_ENDPOINT = "/selectZona"
# CONSULTAR_E14: "dame HTML con botones de mesas y tokens para descargar".
CONSULTAR_E14_ENDPOINT = "/consultarE14"
# DESCARGA: "aquí te entrego el PDF" cuando mandas el token correcto.
DESCARGA_ENDPOINT = "/descargae14"

# --- Concatenamos BASE_URL + ruta para tener la URL completa ---
# Si NO hiciéramos esto, tendrías que escribir el dominio otra y otra vez.
HOME_URL = BASE_URL + HOME_ENDPOINT
AVANCE_DEPTO_URL = BASE_URL + AVANCE_DEPTO_ENDPOINT
SELECT_MPIO_URL = BASE_URL + SELECT_MPIO_ENDPOINT
SELECT_ZONA_URL = BASE_URL + SELECT_ZONA_ENDPOINT
CONSULTAR_E14_URL = BASE_URL + CONSULTAR_E14_ENDPOINT
DESCARGA_URL = BASE_URL + DESCARGA_ENDPOINT

# =============================================================================
# Token largo (NO es el JWT; es otro dato que apareció en pruebas antiguas)
# =============================================================================
# OJO: En producción lo ideal es NO pegar secretos en el código.
# Mejor: variable de entorno. Aquí dejamos get("...") or "" para que puedas
# poner E14_REGISTRO_TOKEN en tu sistema y reemplazar esto sin editar archivo.
# Si borras esta línea y el código la importa, Python lanzaría ImportError.
TOKEN_REGISTRO_PRESIDENCIAL = os.environ.get(
    "E14_REGISTRO_TOKEN",
    "84a6J7jvUm+sKzlTVgLB98kt+a2Maam82/8eieWRSPlYd5mJlVtwlXEB/DJsSSo/llyyLteJwHgw3f8/QcLGLtY020BJEvHWX7wW/VNwsSk=",
)

# =============================================================================
# Comportamiento de red (timeouts, SSL, cortesía con el servidor)
# =============================================================================
# TIMEOUT: segundos máximos esperando respuesta antes de decir "no contestó".
TIMEOUT = 30
# VERIFY_SSL: False = no validar certificado TLS (a veces necesario con este
# dominio en desarrollo). True = más seguro pero puede fallar si el cert
# no coincide con el nombre del host.
VERIFY_SSL = False
# Pausa entre descargas para no martillar el servidor (cortesía + rate limit).
REQUEST_DELAY_SECONDS = 0.35
# Reintentos si la red falla un instante.
MAX_RETRIES = 3
