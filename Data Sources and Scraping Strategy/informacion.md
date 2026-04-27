# 🗳️ E14-CHALLENGE: Auditoría Electoral en Colombia

## 📌 ¿Qué es este proyecto?

**E14-Challenge** es una plataforma para auditar las elecciones en Colombia usando formularios E-14 (formularios electorales).

Los formularios E-14 contienen:
- Votos por cada candidato
- Votos en blanco y nulos
- Datos de ubicación (departamento, municipio, zona, mesa)

Nuestro proyecto **automatiza** la lectura y análisis de estos formularios.

---

## 🎯 Mi parte del proyecto (SCRAPING)

Me encargo de:
1. **Descargar** los formularios E-14 en PDF desde los servidores de la Registraduría
2. **Organizarlos** por carpetas (departamento/municipio/zona/mesa)
3. **Preparar** los archivos para que mi compañero los procese

---

## 🤔 Explicación nivel "Niño de 5 años"

### ¿Cómo funciona el scraping?

Imagina que tienes un amigo que tiene muchos libros en su casa y tú necesitas fotocopiarlos:

1. **Tocas la puerta** → `requests.post(url)`
2. **Le das tu carné de identidad** → `token`
3. **Tu amigo te da el PDF** → `response`
4. **Guardas el PDF en tu carpeta** → `with open(...)`

**ESO ES TODO.**

Tu compañero hace lo demás (leer el PDF con IA, guardar en base de datos, etc).

---

## ⚙️ Estructura del código

### Archivo: `config.py`

**¿Qué es?** Un archivo donde guardamos toda la configuración (URLs, tokens, rutas) en UN SOLO LUGAR.

**¿Por qué?** Si mañana cambia la URL o el token, no tenemos que buscar en todo el código. Solo cambiamos en `config.py`.

**Qué contiene:**

```
DESCARGA_URL = "https://e14_pres1v_2022.registraduria.gov.co/descargae14"
```
Este es el "número de teléfono" del servidor. Aquí mandamos la petición.

```
TOKEN_REGISTRO_PRESIDENCIAL = "84a6J7jvUm+sKzlTVgLB98kt+..."
```
Este es nuestro "carné de identidad". El servidor dice: "Dame el token para verificar que eres tú".

```
OUTPUT_DIR = BASE_DIR / "pdfs_descargados"
```
Esta es la carpeta donde guardamos los PDFs que descargamos.

---

### Archivo: `scrape.py`

**¿Qué es?** El programa principal que descarga los PDFs.

**Estructura paso a paso:**

#### 🔷 PASO 1: IMPORTACIONES

```python
import requests
import urllib3
from config import DESCARGA_URL, TOKEN_REGISTRO_PRESIDENCIAL, ...
```

- `import requests` → Traemos la librería para hacer peticiones HTTP
- `import urllib3` → Traemos la librería para manejar conexiones seguras
- `from config import ...` → Traemos las configuraciones que guardamos en `config.py`

#### 🔷 PASO 2: DESACTIVAR ADVERTENCIAS

```python
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

Cuando usamos `verify=False` (no verificar certificado), Python nos avisa que es "inseguro".
Esta línea = "Está bien Python, calla" (solo para desarrollo, NO en producción).

#### 🔷 PASO 3: FUNCIÓN `descargar_pdf()`

Esta función hace TODO el trabajo de descargar UN PDF.

**Paso a paso:**

1. **Preparar los datos a enviar:**
```python
datos_envio = {"data": TOKEN_REGISTRO_PRESIDENCIAL}
```
Esto es como preparar una "carta" con tu token dentro.

2. **Hacer la petición HTTP POST:**
```python
response = requests.post(url=DESCARGA_URL, data=datos_envio, verify=VERIFY_SSL, timeout=TIMEOUT)
```
Esto es como enviar la carta al servidor y esperar respuesta.

3. **Verificar que la respuesta fue exitosa:**
```python
if response.status_code == 200:
    print("✅ Éxito")
```
El servidor responde con un código:
- 200 = Éxito ✅
- 404 = Archivo no encontrado ❌
- 500 = Error en el servidor ❌

4. **Guardar el PDF en el computadora:**
```python
ruta_completa = OUTPUT_DIR / nombre_archivo
with open(ruta_completa, "wb") as archivo:
    archivo.write(response.content)
```
Esto es como decir: "Abre un archivo nuevo en mi computadora y escribe adentro el PDF que recibí".

5. **Manejar errores:**
```python
try:
    # intentar hacer algo
except requests.exceptions.Timeout:
    # si hay timeout, hacer esto
except Exception as e:
    # si hay cualquier otro error, hacer esto
```
Esto es como tener un "plan B". Si algo sale mal, no se cae el programa, solo muestra un error.

#### 🔷 PASO 4: FUNCIÓN `main()`

Esta es la función que ejecuta TODO. Aquí es donde empieza el programa.

```python
def main():
    exito = descargar_pdf("formulario_e14_001.pdf")
    if exito:
        print("✅ Proceso completado exitosamente")
```

Llama a `descargar_pdf()` y espera el resultado.

#### 🔷 PASO 5: PUNTO DE ENTRADA

```python
if __name__ == "__main__":
    main()
```

Esto es como decir: "Si alguien corre este archivo directamente, ejecuta `main()`".

---

## 🚀 ¿Cómo ejecutarlo?

### Step 1: Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instala todas las librerías necesarias (requests, urllib3, etc).

### Step 2: Ejecutar el scraper

```bash
python scrape.py
```

El programa:
1. Conecta con el servidor de la Registraduría
2. Envía el token
3. Recibe el PDF
4. Lo guarda en la carpeta `pdfs_descargados/`

---

## 📊 Salida esperada

```
============================================================
🚀 SCRAPER DE FORMULARIOS E-14
============================================================

📁 Carpeta de salida: C:\...\pdfs_descargados
🌐 Servidor: https://e14_pres1v_2022.registraduria.gov.co/descargae14

Descargando PDFs...
------------------------------------------------------------
📤 Enviando petición al servidor...
   URL: https://e14_pres1v_2022.registraduria.gov.co/descargae14
   Token: 84a6J7jvUm+sKzlTVgLB...*** (oculto por seguridad)
✅ Respuesta exitosa del servidor (código 200)
✅ PDF descargado exitosamente
   Nombre: formulario_e14_001.pdf
   Ubicación: C:\...\pdfs_descargados\formulario_e14_001.pdf
   Tamaño: 156.34 KB

------------------------------------------------------------
✅ Proceso completado exitosamente
============================================================
```

---

## 🔄 Próximos pasos (no hecho aún)

Cuando tengamos esto funcionando, haremos:

1. **Descargar múltiples PDFs** (no solo uno)
2. **Organizarlos por carpetas** (departamento/municipio/zona/mesa)
3. **Recuperación de errores** (si falla, reintentar)
4. **Logging** (guardar un registro de qué descargamos)

---

## ❓ Preguntas de validación

Para verificar que entendiste:

1. ¿Qué es el `token` y para qué sirve?
2. ¿Qué hace `verify=False`?
3. ¿Dónde guardamos el PDF descargado?
4. ¿Qué significa "código 200"?
5. ¿Por qué usamos `config.py` en lugar de escribir todo en `scrape.py`?

---

## 🎨 Tecnologías usadas

- **Python** → Lenguaje de programación
- **requests** → Librería para hacer peticiones HTTP
- **urllib3** → Librería para manejar conexiones HTTPS
- **FastAPI** (compañero) → API REST
- **PostgreSQL** (compañero) → Base de datos
- **AWS S3** (compañero) → Almacenamiento en la nube

---

## 👥 Equipo

- **Yo** (este proyecto) → Scraping, descargas, reverse API
- **Mi compañero** → API, base de datos, storage, IA (OCR)


mira yo estaba haciendo un proyecto con un amigo pero nos dividimos el trabajo y cada uno esta trabajando consus inteligenias artificiales y sus partes del proyecto y acontinuacion te voy a pasar el proyecto:
🧠 RESUMEN COMPLETO DEL PDF (E14 Challenge)
📌 ¿Qué es el proyecto?

Plataforma tecnológica para auditar elecciones en Colombia usando formularios E-14.

👉 Hace esto:

Descarga formularios oficiales (PDF)
Usa IA (OCR) para leer números escritos a mano
Detecta errores o irregularidades
Muestra todo en un dashboard interactivo
🎯 Objetivo principal
Aumentar la transparencia electoral
Permitir ver resultados desde nivel:
Nacional → departamento → municipio → mesa
Detectar:
Errores matemáticos
Datos sospechosos
Inconsistencias
📊 Datos que usa
Formularios E-14 de la Registraduría
Ejemplo base: elecciones 2022 (~102,000 mesas)

👉 Para desarrollo:

Solo ciudades grandes (~20,000 formularios)
🌐 Cómo funciona (flujo general)

Scraping (descarga)
Se descargan PDFs desde páginas oficiales
Se guardan organizados por:

departamento / municipio / zona / mesa
2. Procesamiento con IA (OCR)
Convierte PDF → imagen
Usa IA (Gemini 3 Flash) para extraer:
Votos por candidato
Votos en blanco, nulos, etc.
Totales de mesa

👉 También detecta problemas como:

Números tachados
Escritura ilegible
Valores ambiguos
3. Validación automática

Se revisa que:

Sumas sean correctas
No haya valores negativos
Todo tenga sentido lógico
4. Clasificación de calidad

Cada formulario se clasifica:

🟢 CLEAN → todo correcto
🟡 HAS_ISSUES → tiene problemas
🔴 UNREADABLE → ilegible
5. Detección de anomalías
🔹 En una sola mesa:
Sumas incorrectas
Diferencias entre votantes y votos
Muchos números corregidos
Valores raros (ej: 0 votos en mesas grandes)
🔹 Entre mesas:
Comportamientos muy diferentes
Participación anormal
Resultados sospechosamente iguales
🔹 A nivel región:
Ley de Benford
Desviaciones estadísticas
Comparación con resultados oficiales
🏗️ Arquitectura del sistema
🔹 Backend
FastAPI (solo lectura)
🔹 Frontend
React
🔹 Base de datos
PostgreSQL
🔹 Almacenamiento
AWS S3 (archivos)
🔹 IA
Gemini 3 Flash (OCR)
⚙️ Pipeline (procesos separados)

Scripts en Python:

scrape.py → descarga PDFs
extract.py → usa IA
analyze.py → detecta anomalías
sync_s3.py → sube archivos

👉 Todos son:

Reanudables
Independientes
📊 Dashboard (interfaz)

Muestra:

📍 Mapa de Colombia con anomalías
📊 Resultados por candidato
📄 Vista del formulario + datos extraídos
⚠️ Lista de errores detectados
🔍 Funciones clave
Filtrar por:
Ubicación
Candidato
Tipo de error
Comparar:
Municipios
Mesas
Ver detalles por formulario
💰 Monetización
Google AdSense
Donaciones (Stripe, PSE)
🗂️ Base de datos (estructura básica)

Tablas principales:

elections
forms
extraction_results
candidate_votes
anomalies
🗳️ Qué contiene un formulario E-14
Información de ubicación
Número de mesa
Votos por candidato
Votos:
en blanco
nulos
no marcados
Totales
Firmas
🚀 Fases del proyecto
Base del sistema
Scraping
IA (OCR)
Análisis
API
Dashboard
Funciones avanzadas
Producción
💡 Idea clave (lo MÁS importante)

👉 Es un sistema que:

automatiza la revisión de elecciones
usando IA + análisis estadístico
para detectar fraude o errores



analiza este proyecto y sigue las instrucciones que digo en el promt, elimina lo que tengas que eliminar y haz lo que tengas que hacer para descargar esos pdfs y mi parte del trabajo es lo que esta en la carpeta data sources and scraping strategy


Actúa como un desarrollador de software senior con 30 años de experiencia
en backend Python, scraping y APIs REST, y también como un profesor experto
en enseñar programación desde cero a personas sin experiencia previa.
Tu misión: enseñarme paso a paso a construir MI PARTE de un proyecto real
de auditoría electoral colombiana llamado "E14 Challenge".
════════════════════════════════════════════════════════════
📋 QUÉ ES EL PROYECTO (contexto completo)
════════════════════════════════════════════════════════════
E14 Challenge es una plataforma de tecnología cívica que busca promover
la transparencia electoral en Colombia. El sistema:

Descarga los formularios E-14 (Actas de Escrutinio de Mesa) publicados
por la Registraduría Nacional del Estado Civil en formato PDF.
Usa IA (Gemini 3 Flash vía Google Vertex AI) para leer los formularios
escritos a mano y extraer los votos por candidato.
Detecta anomalías, errores aritméticos e irregularidades estadísticas.
Muestra todo en un dashboard web interactivo para ciudadanos, periodistas
y organizaciones como la MOE (Misión de Observación Electoral).

DATOS CLAVE DEL PROYECTO:

Dataset de desarrollo: elecciones presidenciales 2022 (primera vuelta,
29 de mayo de 2022).
Aproximadamente 102,152 mesas en 12,513 puestos de votación a nivel nacional.
Fase local (desarrollo): solo 6 ciudades principales → ~21,800 formularios.
· Bogotá D.C.   (código DANE: 11-001) → ~12,000 mesas
· Medellín      (código DANE: 05-001) → ~3,500 mesas
· Cali          (código DANE: 76-001) → ~2,800 mesas
· Barranquilla  (código DANE: 08-001) → ~1,500 mesas
· Cartagena     (código DANE: 13-001) → ~1,200 mesas
· Bucaramanga   (código DANE: 68-001) → ~800 mesas

PORTAL DE LA REGISTRADURÍA:

URL base del dataset de desarrollo:
e14_pres1v_2022.registraduria.gov.co
El portal usa una interfaz renderizada en JavaScript con selectores
dinámicos (departamento → municipio → zona → puesto → mesa).
La estrategia preferida: hacer reverse engineering de las llamadas
XHR/fetch que hace el navegador para encontrar los endpoints JSON
ocultos que alimentan esos selectores.
Alternativa si no se encuentran los endpoints: usar Playwright o
Puppeteer para navegar el portal de forma automática.

ESTRUCTURA DE LOS ARCHIVOS PDF:
Los PDFs siguen este patrón de nombre:
5036317_E14_PRE_X_01_001_001_XX_01_031_X_XXX.pdf
Decodificado campo por campo:
5036317  → Número único del formulario (coincide con número KIT)
E14      → Tipo de formulario (siempre E14)
PRE      → Tipo de elección (PRE=Presidencial, SEN=Senado, CAM=Cámara)
X        → Indicador de ronda
01       → Código DANE del departamento (01 = Antioquia)
001      → Código DANE del municipio (001 = Medellín)
001      → Zona de votación
XX       → Reservado
01       → Número del puesto de votación
031      → Número de la mesa de votación
X_XXX    → Sufijo de versión
ESTRUCTURA DE CARPETAS PARA GUARDAR LOS PDFs:
./data/raw/{dept_code}/{muni_code}/{zone}/{station}/{table}.pdf
Ejemplo:
./data/raw/01/001/001/01/031.pdf
Esta misma estructura se replica en AWS S3:
s3://e14-challenge/{election_id}/{dept}/{muni}/{zone}/{station}/{table}.pdf
EL FORMULARIO E-14 (qué contiene):
Cada formulario tiene:

Encabezado: departamento, municipio, zona, puesto, mesa, código de barras.
Nivelación de mesa:
· Total Sufragantes (del formato E-11)
· Total Votos en la Urna
· Total Votos Incinerados
Votos por candidato (elecciones 2022, 8 candidatos):

Rodolfo Hernández   (LIGA)
John Milton Rodríguez (Colombia Justa Libres)
Federico Gutiérrez  (Equipo por Colombia / FICO)
Sergio Fajardo      (Centro Esperanza)
Enrique Gómez       (Fuerza Nacional)
Gustavo Petro       (Pacto Histórico)
Luis Pérez          (Piensa en Grande)
Ingrid Betancourt   (Oxígeno)
Cada candidato tiene 3 celdas: centenas, decenas, unidades.
Un asterisco (*) en centenas significa número de 2 dígitos.


Votos en blanco, nulos, no marcados.
Total votos de la mesa.
Pie: constancias, si hubo reconteo, firmas de 6 jurados.

════════════════════════════════════════════════════════════
👥 DIVISIÓN DEL TRABAJO (2 desarrolladores)
════════════════════════════════════════════════════════════
MI COMPAÑERO — mencionar solo cuando afecte mi flujo:
· Diseño del esquema de base de datos (PostgreSQL 16 + PostGIS en Docker)
· Storage local y AWS S3 + CloudFront CDN
· FastAPI (backend API REST, solo lectura)
· Metadata y tracking de archivos (tabla forms en PostgreSQL)
· Scripts: sync_s3.py, extract.py, analyze.py
YO — ENFOQUE EXCLUSIVO (95% de tu atención):
· Reverse engineering del portal de la Registraduría
→ Inspeccionar las llamadas XHR/fetch del navegador
→ Documentar los endpoints, parámetros y formatos de respuesta
→ Crear un archivo markdown con la API descubierta
· scrape.py — CLI en Python que:
→ Acepta election_id y lista de municipios como argumentos
→ Descubre todos los formularios disponibles via la API del portal
→ Descarga los PDFs de forma concurrente y con límite de velocidad
→ Guarda los archivos en la estructura de carpetas correcta
→ Registra el progreso en la base de datos (tabla forms)
→ Es idempotente: si se interrumpe, puede reanudarse sin redescargar
→ Implementa reintentos con backoff exponencial (máx. 5 intentos)
→ Guarda el hash SHA-256 de cada PDF para verificar integridad
→ Respeta un rate limit de 2-5 requests/segundo
════════════════════════════════════════════════════════════
🛠️ STACK TECNOLÓGICO (usa SIEMPRE estos, sin excepción)
════════════════════════════════════════════════════════════
· Python 3.12+
· httpx (cliente HTTP async, preferido sobre aiohttp)
· asyncio (concurrencia nativa de Python)
· Click (para construir la interfaz CLI)
· psycopg2 o SQLAlchemy (para escribir en PostgreSQL,
coordinado con mi compañero)
· pathlib (para manejo de rutas de archivos)
· hashlib (para calcular SHA-256 de los PDFs)
· tenacity (para reintentos con backoff exponencial)
Instalación base:
pip install httpx click asyncio psycopg2-binary sqlalchemy tenacity
════════════════════════════════════════════════════════════
🗄️ BASE DE DATOS — tabla que afecta mi trabajo
════════════════════════════════════════════════════════════
Mi compañero creará la tabla forms. Yo solo necesito ESCRIBIR en ella.
La tabla relevante para mí:
forms (
id                  PRIMARY KEY,
table_id            FK → tables,
election_id         FK → elections,
form_serial         VARCHAR,        ← el número único del formulario
local_path          VARCHAR NULL,   ← ruta local donde guardé el PDF
s3_key_pdf          VARCHAR,        ← clave S3 (la llena sync_s3.py)
download_timestamp  TIMESTAMP,      ← cuándo lo descargué
file_hash           VARCHAR,        ← SHA-256 del PDF
processing_status   ENUM(          ← estado actual
'PENDING',        ← recién descargado, listo para extraer
'EXTRACTED',      ← ya procesado por la IA
'ANALYZED',       ← ya analizado por el motor de anomalías
'FAILED'          ← falló en algún paso
)
)
Cuando yo descargo un PDF, escribo una fila con:
processing_status = 'PENDING'
local_path = la ruta en disco
file_hash = el SHA-256 calculado
════════════════════════════════════════════════════════════
🎯 MIS 3 OBJETIVOS
════════════════════════════════════════════════════════════

Terminar mi parte correctamente y que funcione en producción
Entender al 100% cada línea de código que escribo
Aprender backend y scraping desde cero de verdad

════════════════════════════════════════════════════════════
🧠 MI NIVEL Y CÓMO DEBES ENSEÑARME
════════════════════════════════════════════════════════════
Soy principiante. Parte desde cero absoluto. No asumas NINGÚN
conocimiento previo sobre scraping, APIs, async, ni línea de comandos.
Balance exacto de enseñanza:
· Simple de entender → como si se lo explicaras a alguien que
nunca ha programado en backend
· Pero código real y profesional → nada de pseudocódigo, nada
de ejemplos que no funcionen en el proyecto real
· Analogías: bienvenidas SOLO si hacen el concepto más claro,
no solo más "bonito"
· Cuando algo sea difícil, avísame ANTES de explicarlo
════════════════════════════════════════════════════════════
⚙️ ESTRUCTURA OBLIGATORIA DE CADA LECCIÓN
════════════════════════════════════════════════════════════
Cada vez que enseñes algo, SIEMPRE sigue este orden exacto:

📌 QUÉ vamos a aprender (1-2 oraciones máximo)
🧠 POR QUÉ existe esto (el problema que resuelve)
💡 CÓMO funciona (explicación sin código todavía)
🔗 CÓMO aplica a nuestro proyecto E14 específicamente
💻 CÓDIGO paso a paso:
· Muestra el código completo primero
· Luego explica CADA línea con comentario inline
· Señala qué pasaría si esa línea no existiera
▶️ CÓMO ejecutarlo (comando exacto en terminal)
✅ QUÉ debe pasar cuando funcione bien (output esperado)
❓ 1-2 PREGUNTAS de validación antes de continuar

════════════════════════════════════════════════════════════
🔁 REGLAS DE INTERACCIÓN
════════════════════════════════════════════════════════════
· Después de cada lección: haz preguntas de validación
· NO avances al siguiente tema hasta que yo confirme que entendí
· Si no entiendo: explica diferente, más simple, divide más
· Cada concepto nuevo SIEMPRE conectado al proyecto E14
· Si me equivoco: corrígeme con amabilidad y explica por qué
· Antes de usar cualquier librería: dime exactamente cómo instalarla
════════════════════════════════════════════════════════════
⛔ REGLAS CRÍTICAS (nunca las rompas)
════════════════════════════════════════════════════════════
· NO saltarte pasos
· NO dar todo de una vez
· NO asumir conocimiento previo de ningún tipo
· NO avanzar de tema sin mi confirmación explícita
· El código SIEMPRE debe ser ejecutable y real
· SIEMPRE dime qué instalar antes de usar algo nuevo
· SIEMPRE conecta lo que explicas con el proyecto E14 real
════════════════════════════════════════════════════════════
🚀 POR DÓNDE EMPEZAMOS (obligatorio)
════════════════════════════════════════════════════════════
Empezamos SIEMPRE por:
👉 Sección 2 del documento: "Data Sources and Scraping Strategy"
👉 Subsección exacta para comenzar: "2.3.1 Discovery Phase"
→ Entender el portal de la Registraduría
→ Cómo funciona su interfaz JS dinámica
→ Qué son las llamadas XHR/fetch y cómo espiarlas
→ Cómo documentar los endpoints descubiertos
No cambies de tema hasta que yo te lo indique explícitamente.
════════════════════════════════════════════════════════════
🎯 TONO Y ESTILO
════════════════════════════════════════════════════════════
· Directo, claro y pedagógico
· Sin relleno ni texto innecesario
· Prioriza que YO entienda sobre avanzar rápido
· Celebra cuando algo quede claro (sin exagerar)
· Si algo es complejo, dímelo antes: "esto es más difícil, presta atención"
