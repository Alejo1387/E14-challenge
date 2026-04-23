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