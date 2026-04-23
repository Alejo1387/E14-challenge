# =============================================================================
# discovery_phase.py — "La lupa automática" para ver cómo habla el portal
# =============================================================================
# Analogía niño de 5 años:
# La página web es un escenario de títeres. Tú solo ves los títeres (menús).
# Detrás hay hilos (peticiones XHR/fetch) que el navegador jala sin que lo notes.
# Este programa hace de detective: mira el HTML, baja los guiones (archivos .js),
# busca palabras mágicas como "/consultarE14" y escribe un reporte para tu equipo.
#
# Si NO existiera este archivo, tendrías que hacer todo a mano cada vez que el
# sitio cambie, y es muy fácil olvidar un paso o documentar mal un endpoint.

# --- from __future__ import annotations ---
# Permite usar tipos "adelantados" (como EndpointFinding sin comillas) en todo el archivo.
# Si NO estuviera: en versiones viejas de Python algunas anotaciones romperían.
from __future__ import annotations

# --- json: leer/escribir datos en formato JSON (texto estructurado) ---
# Lo usamos para guardar la lista de scripts encontrados y la respuesta /auth/csrf.
import json

# --- re: expresiones regulares, buscar patrones en texto largo ---
# Sirve para encontrar <script src="..."> y rutas tipo /selectMpio dentro del JS.
import re

# --- dataclass: crea "pequeñas cajas de datos" con campos nombrados ---
# EndpointFinding es una caja con: path, source, method_hint, notes.
from dataclasses import dataclass

# --- datetime, timezone: marcar en el reporte CUÁNDO hicimos el descubrimiento ---
from datetime import datetime, timezone

# --- Path: rutas de archivos que funcionan bien en Windows y Linux ---
from pathlib import Path

# --- Any: tipo "cualquier cosa" para parámetros flexibles de httpx ---
from typing import Any

# --- click: construye la interfaz de terminal (flags como --no-verify-ssl) ---
# Si NO usáramos click, tendrías que editar el código para cambiar opciones.
import click

# --- httpx: cliente HTTP moderno (puede async/await) ---
# Aquí lo usamos en modo async para bajar HTML y JS rápido sin bloquear.
import httpx

# --- tenacity: reintentos automáticos con espera creciente (backoff) ---
# Si la red parpadea, no fallamos a la primera; intentamos de nuevo.
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# =============================================================================
# Valores por defecto (si no pasas flags en la terminal, se usan estos)
# =============================================================================
# DEFAULT_BASE_URL: portal de desarrollo que te dio el enunciado.
DEFAULT_BASE_URL = "https://e14_pres1v_2022.registraduria.gov.co"
# DEFAULT_OUTPUT_DOC: aquí se escribe el markdown "api_discovery.md" para humanos.
DEFAULT_OUTPUT_DOC = Path(__file__).parent / "api_discovery.md"
# DEFAULT_ARTIFACTS_DIR: carpeta con pruebas (HTML/JS) por si quieres abrirlos en el editor.
DEFAULT_ARTIFACTS_DIR = Path(__file__).parent / "artifacts" / "discovery"


# --- @dataclass: convierte la clase en un contenedor simple de datos ---
@dataclass
class EndpointFinding:
    # path: ruta del endpoint, por ejemplo "/selectMpio"
    path: str
    # source: nombre del archivo .js donde lo encontramos (para citar la evidencia)
    source: str
    # method_hint: pista del método HTTP (aquí asumimos POST porque el portal usa formularios)
    method_hint: str
    # notes: texto libre explicando cómo lo detectamos
    notes: str


# --- @retry(...) decorador: envuelve la función y reintenta si httpx falla por red ---
@retry(
    # Solo reintentar si el error es de red (RequestError), no si el servidor responde 404 lógico
    retry=retry_if_exception_type(httpx.RequestError),
    # Espera exponencial: 1s, 2s, 4s... hasta max 8s entre intentos
    wait=wait_exponential(multiplier=1, min=1, max=8),
    # Máximo 5 intentos (como pidió tu enunciado para producción)
    stop=stop_after_attempt(5),
    # Si tras reintentos sigue mal, vuelve a lanzar el error (no lo tragamos)
    reraise=True,
)
# --- async def fetch_with_retry: una petición HTTP con reintentos "de fábrica" ---
async def fetch_with_retry(client: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> httpx.Response:
    # client.request: ejecuta GET/POST/etc con la misma sesión (cookies, etc.)
    response = await client.request(method=method, url=url, **kwargs)
    # raise_for_status: si el código es 4xx/5xx, lanza error (así no seguimos ciegamente)
    response.raise_for_status()
    # Devolvemos la respuesta completa al llamador
    return response


def extract_script_srcs(html_text: str) -> list[str]:
    # Docstring corto: saca todos los src="..." de etiquetas <script ...>.
    # Busca <script src="..."> dentro del HTML.
    script_src_pattern = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
    # findall: lista de coincidencias; set: quita duplicados; sorted: orden estable
    return sorted(set(script_src_pattern.findall(html_text)))


def extract_endpoints_from_js(js_text: str) -> set[str]:
    # Docstring: busca rutas conocidas del portal dentro del texto JavaScript.
    # Captura endpoints típicos del portal (lista basada en lo que ya vimos en la práctica).
    endpoint_pattern = re.compile(
        r"/(?:auth/csrf|selectDepto|selectMpio|selectZona|consultarE14|descargae14|avanceDepto)\b"
    )
    # set(...) porque no nos importa el orden y queremos únicos
    return set(endpoint_pattern.findall(js_text))


def normalize_url(base_url: str, maybe_relative_url: str) -> str:
    # Docstring: convierte "rutas relativas" en URL absoluta descargable.
    # Si el HTML trae //cdn... es "protocol-relative"
    if maybe_relative_url.startswith("//"):
        # Le pegamos https: para que httpx sepa cómo conectar
        return "https:" + maybe_relative_url
    # Si ya es http(s) completo, no lo tocamos
    if maybe_relative_url.startswith("http://") or maybe_relative_url.startswith("https://"):
        return maybe_relative_url
    # Si es "/js/archivo.js", lo pegamos al dominio base
    return base_url.rstrip("/") + "/" + maybe_relative_url.lstrip("/")


def sanitize_filename(name: str) -> str:
    # Docstring: Windows no permite ciertos caracteres en nombres de archivo; los sustituimos.
    # Quita caracteres prohibidos en Windows para nombres de archivo
    clean = re.sub(r"[\\/:*?\"<>|]", "_", name)
    # & también suele romper cosas en URLs/nombres raros
    clean = clean.replace("&", "_")
    # Si quedó vacío, usamos un nombre genérico
    return clean or "script.js"


def render_markdown(
    base_url: str,
    findings: list[EndpointFinding],
    csrf_probe_status: str,
    csrf_probe_payload_keys: list[str],
) -> str:
    # Docstring: arma el texto final del reporte .md (markdown) para tu compañero.
    # Hora UTC: así todos entienden el instante exacto aunque estén en otra ciudad
    generated_at = datetime.now(timezone.utc).isoformat()
    # lines: vamos acumulando el documento como lista de strings
    lines = [
        "# 2.3.1 Discovery Phase - API del portal Registraduria",
        "",
        f"- Fecha UTC: `{generated_at}`",
        f"- Base URL: `{base_url}`",
        "",
        "## Objetivo",
        "",
        "Descubrir y documentar los endpoints reales (XHR/fetch) usados por el portal JS dinamico para navegar departamento -> municipio -> zona -> mesa y descargar PDFs E-14.",
        "",
        "## Endpoint de autenticacion detectado",
        "",
        f"- `GET /auth/csrf`: estado `{csrf_probe_status}`",
        f"- Claves del JSON de respuesta: `{', '.join(csrf_probe_payload_keys) if csrf_probe_payload_keys else 'N/A'}`",
        "",
        "## Endpoints detectados en scripts del portal",
        "",
    ]

    # Por cada endpoint encontrado, una viñeta con evidencia
    for item in findings:
        lines.append(
            f"- `{item.method_hint} {item.path}` | fuente: `{item.source}` | nota: {item.notes}"
        )

    # Parte final: flujo recomendado para el scraper (mapa mental)
    lines.extend(
        [
            "",
            "## Flujo esperado del scraping (resumen)",
            "",
            "- 1) Obtener token con `GET /auth/csrf`.",
            "- 2) Solicitar departamentos (normalmente `POST /selectDepto` o flujo equivalente).",
            "- 3) Solicitar municipios con `POST /selectMpio`.",
            "- 4) Solicitar zonas con `POST /selectZona`.",
            "- 5) Solicitar mesas/tokens con `POST /consultarE14`.",
            "- 6) Descargar cada PDF con `POST /descargae14` (campo `data`).",
            "",
            "## Nota",
            "",
            "Este archivo se regenera automaticamente con `python discovery_phase.py --run-probes`.",
        ]
    )
    # Unimos líneas con saltos de texto Windows/Linux (\n)
    return "\n".join(lines)


async def run_discovery(
    base_url: str,
    output_doc: Path,
    artifacts_dir: Path,
    run_probes: bool,
    verify_ssl: bool,
) -> None:
    # Docstring: orquesta todo el proceso async (descarga, parseo, reporte).
    # Crea carpeta de artefactos si no existe
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # findings_map: diccionario path -> EndpointFinding (evita duplicados por path)
    findings_map: dict[str, EndpointFinding] = {}
    # Texto de estado del probe de CSRF (código 200, error, etc.)
    csrf_status = "NO_EJECUTADO"
    # Lista de claves JSON devueltas por /auth/csrf (normalmente incluye "token")
    csrf_keys: list[str] = []

    # AsyncClient: sesión HTTP reutilizable; verify_ssl lo controla el usuario por bandera
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=verify_ssl) as client:
        # Primer paso: bajar la página principal "/"
        home_url = normalize_url(base_url, "/")
        home_response = await fetch_with_retry(client, "GET", home_url)
        # .text convierte bytes a string HTML
        html_text = home_response.text
        # Guardamos evidencia en disco para que puedas abrirla en el navegador/editor
        (artifacts_dir / "home.html").write_text(html_text, encoding="utf-8")

        # Lista de URLs de scripts encontrados en el HTML
        script_srcs = extract_script_srcs(html_text)
        # Guardamos también en JSON (más fácil de comparar entre ejecuciones)
        (artifacts_dir / "script_srcs.json").write_text(
            json.dumps(script_srcs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Recorremos cada script externo
        for script_src in script_srcs:
            # Algunos src no son descargables (data:..., blob:...) — los saltamos
            if script_src.startswith(("data:", "javascript:", "blob:")):
                continue
            # Convertimos a URL absoluta
            script_url = normalize_url(base_url, script_src)
            try:
                # Bajar el JavaScript (si falla certificado/red, seguimos con el siguiente)
                script_response = await fetch_with_retry(client, "GET", script_url)
            except (httpx.HTTPStatusError, httpx.RequestError, ValueError):
                continue

            # Texto del archivo .js
            script_text = script_response.text
            # Nombre de archivo seguro: quitamos query ?v=1 y fragmentos #...
            script_name = script_src.split("/")[-1].split("?")[0].split("#")[0] or "script.js"
            # Sanitizar para Windows
            script_name = sanitize_filename(script_name)
            # Guardar copia local del JS
            (artifacts_dir / script_name).write_text(script_text, encoding="utf-8")

            # Buscar endpoints conocidos dentro del JS
            for endpoint_path in extract_endpoints_from_js(script_text):
                # setdefault: si ya existe, no pisa la primera evidencia encontrada
                findings_map.setdefault(
                    endpoint_path,
                    EndpointFinding(
                        path=endpoint_path,
                        source=script_name,
                        method_hint="POST",
                        notes="Detectado por regex en JavaScript",
                    ),
                )

        # Opcional: probar /auth/csrf para documentar status real y JSON
        if run_probes:
            csrf_url = normalize_url(base_url, "/auth/csrf")
            try:
                csrf_response = await fetch_with_retry(client, "GET", csrf_url)
                csrf_status = str(csrf_response.status_code)
                maybe_json = csrf_response.json()
                if isinstance(maybe_json, dict):
                    csrf_keys = sorted(list(maybe_json.keys()))
                    (artifacts_dir / "csrf_response.json").write_text(
                        json.dumps(maybe_json, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
            except Exception as exc:
                csrf_status = f"ERROR: {exc}"

    # Ordenamos hallazgos para que el markdown sea estable (misma lectura siempre)
    ordered_findings = sorted(findings_map.values(), key=lambda x: x.path)
    # Escribimos el reporte final para humanos
    output_doc.write_text(
        render_markdown(
            base_url=base_url,
            findings=ordered_findings,
            csrf_probe_status=csrf_status,
            csrf_probe_payload_keys=csrf_keys,
        ),
        encoding="utf-8",
    )

    # Mensajes en terminal (click.echo respeta mejor la consola que print)
    click.echo(f"Documento generado: {output_doc}")
    click.echo(f"Artifacts guardados en: {artifacts_dir}")
    click.echo(f"Endpoints detectados: {len(ordered_findings)}")


# --- @click.command: esta función es el "main" de la CLI ---
@click.command()
# --base-url: permite apuntar a otro entorno sin editar código
@click.option("--base-url", default=DEFAULT_BASE_URL, show_default=True, help="URL base del portal de la Registraduria.")
@click.option(
    "--output-doc",
    default=str(DEFAULT_OUTPUT_DOC),
    show_default=True,
    help="Ruta del markdown donde se documentan endpoints descubiertos.",
)
@click.option(
    "--artifacts-dir",
    default=str(DEFAULT_ARTIFACTS_DIR),
    show_default=True,
    help="Carpeta donde se guardan HTML/JS descargados para inspeccion.",
)
@click.option("--run-probes/--no-run-probes", default=True, show_default=True, help="Ejecuta probes HTTP a endpoints conocidos.")
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=False,
    show_default=True,
    help="Verificar certificado TLS. Para este dominio suele requerirse --no-verify-ssl.",
)
# --- def cli: función síncrona que solo arranca el event loop de asyncio ---
def cli(base_url: str, output_doc: str, artifacts_dir: str, run_probes: bool, verify_ssl: bool) -> None:
    """Discovery Phase: descubre endpoints y documenta la API del portal."""
    # import local: asyncio solo se necesita aquí, no al importar el módulo como librería
    import asyncio

    # asyncio.run: crea un loop, ejecuta run_discovery(...), y cierra limpio
    asyncio.run(
        run_discovery(
            base_url=base_url,
            output_doc=Path(output_doc),
            artifacts_dir=Path(artifacts_dir),
            run_probes=run_probes,
            verify_ssl=verify_ssl,
        )
    )


# --- if __name__ == "__main__": solo corre la CLI cuando ejecutas el archivo directo ---
if __name__ == "__main__":
    cli()
