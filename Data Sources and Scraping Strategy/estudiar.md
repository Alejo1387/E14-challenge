# Estudiar — Guía del proyecto E14 (scraping y estado actual)

Este documento resume **para qué existe el proyecto E14 Challenge**, **qué hace cada cosa en la carpeta `Data Sources and Scraping Strategy`**, **qué librerías usamos**, **qué pasa si falta algo**, y **qué falta para poder descargar todos los PDFs** de forma masiva y estable.

---

## 1. Objetivo del proyecto (en una frase)

Construir una “fábrica” cívica: **bajar los formularios E-14 en PDF** desde el portal de la Registraduría, **organizarlos**, **registrar integridad (hash)**, y dejarlos listos para que **otro pipeline** (IA, base de datos, dashboard) los lea y audite.

Tu parte principal es el **camión**: descubrimiento de la API del portal + descarga confiable de PDFs.

---

## 2. Qué hay en el repositorio E14-challenge (visión general)

| Parte | Carpeta / área | Rol |
|--------|----------------|-----|
| Datos crudos | `data/raw/` | Donde deben vivir los PDF descargados (fuera de esta carpeta de código, en la raíz del challenge). |
| Backend (compañero) | `backend/` | Esquema SQLAlchemy, utilidades de hash, almacenamiento local, scripts de BD, etc. |
| Tu trabajo (scraping) | `Data Sources and Scraping Strategy/` | Scripts de descubrimiento, scrapers, pruebas Playwright, documentación de API descubierta. |
| Raíz | `README.md` | Descripción muy breve del repo (no sustituye esta guía). |

Si **no existiera** la carpeta de scraping, no habría forma automatizada de poblar `data/raw/` desde el portal.

---

## 3. Carpeta `Data Sources and Scraping Strategy` — archivo por archivo

### Archivos de configuración y dependencias

#### `requirements.txt`
- **Qué hace**: Lista las librerías de Python que debes instalar con `pip install -r requirements.txt` para correr los scripts de esta carpeta.
- **Función en el proyecto**: Garantiza que cualquier máquina (la tuya, la de tu compañero, CI) instale las mismas versiones de dependencias declaradas.
- **Si no está**: Nadie sabe qué instalar; los `import` fallan con `ModuleNotFoundError`.

#### `config.py`
- **Qué hace**: Centraliza URLs del portal (`BASE_URL`, endpoints), rutas (`DATA_RAW_DIR` → `E14-challenge/data/raw/`), timeouts, SSL, delays y constantes usadas por `scrape.py`.
- **Función en el proyecto**: Un solo lugar para cambiar dominio o carpeta de salida sin tocar toda la lógica.
- **Si no está**: `scrape.py` no puede importar configuración; habría que duplicar constantes en cada script (frágil).

---

### Descubrimiento de la API (reverse engineering)

#### `discovery_phase.py`
- **Qué hace**: CLI (Click) que descarga el HTML inicial, lista `<script src=...>`, baja los JS relevantes, busca rutas tipo `/selectMpio`, `/consultarE14`, etc., y genera documentación.
- **Función en el proyecto**: Automatiza la **fase 2.3.1 Discovery** y deja evidencia reproducible.
- **Si no está**: Tendrías que documentar endpoints solo a mano en el navegador (más lento y propenso a errores).

#### `api_discovery.md`
- **Qué hace**: Markdown generado (o actualizable) con endpoints detectados y notas del flujo.
- **Función en el proyecto**: Es el “contrato informal” legible por humanos para el equipo.
- **Si no está**: No rompe ejecución; solo pierdes documentación centralizada (puedes regenerarla con `discovery_phase.py`).

---

### Scrapers y flujos de descarga

#### `scrape.py`
- **Qué hace**: Scraper “clásico” con `requests` + `BeautifulSoup`: obtiene JWT por `/auth/csrf`, recorre selects vía POST (`selectDepto`, `selectMpio`, `selectZona`), intenta `/consultarE14`, extrae tokens con regex y descarga con `/descargae14`. Incluye lógica de rutas bajo `data/raw`, manifiesto, reintentos básicos, y soporte opcional de reCAPTCHA vía variable de entorno.
- **Función en el proyecto**: Pipeline principal histórico; útil cuando el portal responde bien sin bloqueo agresivo.
- **Si no está**: Pierdes un flujo completo ya probado en parte; tendrías solo scripts experimentales.

#### `scrape_waf_assisted.py`
- **Qué hace**: Abre **Playwright** (navegador real) para pasar WAF/captcha cuando es posible; luego descarga PDFs con **httpx + asyncio + tenacity** con límite de velocidad y concurrencia; genera manifiesto JSON.
- **Función en el proyecto**: Acerca el stack a lo pedido originalmente (async + httpx + click + tenacity) cuando el WAF permite automatización.
- **Si no está**: No puedes probar el camino “navegador + descarga async” desde un solo comando.

#### `scrape_v2_with_playwright.py`
- **Qué hace**: Variante que combina Playwright + descarga con `requests` (versión “v2” con lógica propia de selects y límite de mesas en prueba).
- **Función en el proyecto**: Sandbox / referencia de integración Playwright.
- **Si no está**: No afecta si usas `scrape_waf_assisted.py` o `scrape.py`; es redundancia útil para experimentos.

#### `scrape_manual_token.py`
- **Qué hace**: Flujo **asistido**: tú haces la consulta en el navegador normal, pegas `g-recaptcha-response` y opcionalmente `Cookie` + `User-Agent` desde DevTools; el script llama `/consultarE14`, parsea tokens y descarga PDFs con `requests`.
- **Función en el proyecto**: Plan B cuando **Playwright o tu IP están bloqueados** por WAF pero el navegador manual aún funciona (o desde otra red).
- **Si no está**: Pierdes la vía más práctica durante bloqueos duros del WAF.

---

### Playwright — pruebas y depuración

#### `playwright_test.py`, `playwright_inspect.py`, `playwright_stealth.py`
- **Qué hacen**: Scripts de prueba para abrir el portal, inspeccionar HTML, probar “stealth”, guardar respuestas en `debug_playwright/`.
- **Función en el proyecto**: Diagnóstico de bloqueos WAF y comportamiento del sitio sin mezclar todo en el scraper principal.
- **Si no están**: Sigues pudiendo scrapear; solo pierdes herramientas de depuración rápida.

#### `playwright.md`
- **Qué hace**: Apuntes sobre uso de Playwright en este contexto.
- **Si no está**: No rompe nada; es documentación opcional.

---

### Documentación y apuntes

#### `informacion.md`
- **Qué hace**: Documentación pedagógica más antigua (enfoque requests, un PDF, etc.).
- **Función**: Material de estudio; puede no coincidir al 100% con el último flujo.
- **Si no está**: No afecta ejecución; usa `estudiar.md` + `api_discovery.md` como fuentes actuales.

---

### Carpetas generadas (no son “código fuente” obligatorio)

#### `artifacts/`
- **Qué hace**: Guarda copias de HTML/JS y JSON de discovery (`discovery_phase.py`).
- **Función**: Evidencia para comparar con DevTools y para auditar qué vio el script.
- **Si no está**: Se recrea al correr discovery. Suele ignorarse en git (artefactos locales).

#### `debug_playwright/`
- **Qué hace**: HTML o capturas guardadas por scripts de prueba Playwright.
- **Si no está**: No importa; se regenera al depurar.

#### `__pycache__/`
- **Qué hace**: Bytecode compilado de Python (automático).
- **Si no está**: Python lo vuelve a crear. No versionar.

---

### Archivos de depuración sueltos (HTML)

#### `debug_error_500.html`, `debug_selectMpio.html`
- **Qué hacen**: Volcados de respuestas del servidor cuando algo falló (por ejemplo 500 en `/consultarE14` o respuesta de `/selectMpio`).
- **Función**: Ayudan a ver qué devolvió el backend en ese momento.
- **Si no están**: No afecta ejecución; solo pierdes la muestra de ese error concreto.

---

## 4. Librerías en `requirements.txt` — qué son y qué pasa si faltan

| Librería | Para qué está | Si falta |
|----------|----------------|----------|
| **httpx** | Cliente HTTP moderno; soporta async y es el preferido para descargas concurrentes en `scrape_waf_assisted.py`. | Fallan imports y no hay descargas async con esa API. |
| **click** | Construye interfaces de línea de comandos (`--depto`, `--help`, etc.) en `discovery_phase.py` y scrapers asistidos. | No puedes pasar parámetros limpios por CLI sin reescribir argparse a mano. |
| **sqlalchemy** | ORM / capa de acceso a BD (alineado con el backend del compañero; preparado para escribir en `forms`). | No puedes usar el mismo estilo de modelos si añades persistencia aquí. |
| **psycopg2-binary** | Driver PostgreSQL para conectar desde Python cuando la BD sea Postgres. | Falla la conexión a Postgres desde scripts que lo usen. |
| **tenacity** | Reintentos con backoff exponencial ante errores de red transitorios. | Debes implementar reintentos a mano o aceptar más fallos aleatorios. |
| **requests** | HTTP síncrono; usado en `scrape.py`, `scrape_manual_token.py`, pruebas. | Esos scripts no corren. |
| **urllib3** | Capa bajo requests; desactivar warnings de SSL en desarrollo. | Menos crítico si no usas `verify=False`; requests puede traer urllib3 embebido. |
| **beautifulsoup4** | Parsear HTML de selects y tablas de mesas. | No puedes extraer opciones ni tokens del HTML fácilmente. |
| **lxml** | Parser rápido opcional para BeautifulSoup. | BeautifulSoup puede usar el parser html por defecto (más lento o distinto en casos raros). |
| **playwright** | Automatizar navegador real (Chromium) para WAF/reCAPTCHA. | No corren `scrape_waf_assisted.py` ni pruebas Playwright. |

Instalación típica:

```bash
cd "…\E14-challenge\Data Sources and Scraping Strategy"
python -m pip install -r requirements.txt
python -m playwright install chromium
```

---

## 5. Qué hace “todo lo demás” del proyecto por ahora (resumen)

- **`backend/`**: Define modelos (por ejemplo tabla `forms`), rutas de datos, hashing, almacenamiento local; es la base para que tu compañero consuma PDFs y metadatos.
- **`data/raw/`**: Destino acordado de PDFs; debe alimentar el resto del pipeline (extracción IA, análisis, API de solo lectura, dashboard).

---

## 6. Qué falta para poder descargar **todos** los PDFs (lista honesta)

1. **Acceso estable al portal**  
   Si el **WAF bloquea tu IP** o el sitio no carga selects, **ningún script** puede completar la descarga masiva. Hay que: otra red/IP, ventana de tiempo sin bloqueo, o coordinación con soporte institucional según políticas.

2. **Estrategia de captcha**  
   reCAPTCHA invisible implica tokens de corta vida. Opciones reales:
   - **Modo asistido** (`scrape_manual_token.py`) mientras dure el token.
   - **Playwright con sesión humana** cuando el WAF no bloquee automatización.
   - En producción a gran escala: políticas legales/institucionales y límites de tasa estrictos.

3. **Iteración masiva geográfica**  
   Recorrer todas las combinaciones depto/municipio/zona/puesto/mesa con **checkpoints** (reanudar sin perder progreso), manifiestos por lote, y límites 2–5 req/s respetados.

4. **Persistencia en BD (`forms`)**  
   Escribir filas con `processing_status = PENDING`, `local_path`, `file_hash`, `download_timestamp`, y FKs correctas (`voting_table_id`, etc.) según el esquema final acordado con tu compañero.

5. **S3 / sync**  
   Lo define tu compañero (`sync_s3.py`); tu parte entrega archivos locales + hashes + manifiestos consistentes.

---

## 7. Cómo usar este archivo

- Estudia esta guía antes de correr scrapers en red.
- Si cambia el portal, actualiza `api_discovery.md` con `discovery_phase.py` y luego ajusta los scrapers según la nueva evidencia.

---

*Última actualización del inventario: según archivos presentes en `Data Sources and Scraping Strategy` (scrapers, discovery, Playwright, manifiestos y documentación).*
