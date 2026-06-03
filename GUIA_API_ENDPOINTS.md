# 🔌 Guía de API - E14 Challenge

**Base URL**: `http://127.0.0.1:8000`  
**Documentación Interactiva**: `http://127.0.0.1:8000/docs` (Swagger UI)  
**Documentación Alternativa**: `http://127.0.0.1:8000/redoc` (ReDoc)

---

## 📝 Endpoints Disponibles

### 1️⃣ GET `/` - Interfaz Web

**Descripción**: Sirve la página de upload HTML  
**Método**: GET  
**Autenticación**: No requerida

```bash
# En navegador:
http://127.0.0.1:8000/

# Con curl:
curl http://127.0.0.1:8000/ | head -20
```

**Respuesta**: Página HTML completa con formulario de upload

---

### 2️⃣ POST `/upload-pdf` - Cargar Formulario

**Descripción**: Carga un PDF, lo valida, lo guarda y lo registra en BD

**Método**: POST  
**Autenticación**: No requerida  
**Content-Type**: `multipart/form-data`

#### Parámetros

| Nombre | Tipo | Obligatorio | Descripción | Ejemplo |
|--------|------|-------------|-------------|---------|
| file | File | ✅ Sí | Archivo PDF | `formulario.pdf` |
| dept_code | String | ✅ Sí | Código departamento (2 dígitos) | `01` |
| muni_code | String | ✅ Sí | Código municipio (3 dígitos) | `001` |
| zone_code | String | ✅ Sí | Código zona (3 dígitos) | `001` |
| station_code | String | ✅ Sí | Código puesto (2 dígitos) | `01` |
| table_number | String | ✅ Sí | Número mesa (3 dígitos) | `001` |

#### Con cURL

```bash
# Crear un PDF de prueba primero (si no tienes uno)
echo "%PDF-1.4" > test.pdf && dd if=/dev/urandom bs=1024 count=50 >> test.pdf

# Cargar el PDF
curl -X POST http://127.0.0.1:8000/upload-pdf \
  -F "file=@test.pdf" \
  -F "dept_code=01" \
  -F "muni_code=001" \
  -F "zone_code=001" \
  -F "station_code=01" \
  -F "table_number=001"
```

#### Con JavaScript (Fetch)

```javascript
const formData = new FormData();
formData.append('file', pdfFile); // HTMLInputElement.files[0]
formData.append('dept_code', '01');
formData.append('muni_code', '001');
formData.append('zone_code', '001');
formData.append('station_code', '01');
formData.append('table_number', '001');

const response = await fetch('http://127.0.0.1:8000/upload-pdf', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

#### Con Python (requests)

```python
import requests

with open('test.pdf', 'rb') as f:
    files = {
        'file': f,
        'dept_code': (None, '01'),
        'muni_code': (None, '001'),
        'zone_code': (None, '001'),
        'station_code': (None, '01'),
        'table_number': (None, '001'),
    }
    
    response = requests.post('http://127.0.0.1:8000/upload-pdf', files=files)
    print(response.json())
```

#### Respuesta Exitosa (200 OK)

```json
{
  "success": true,
  "message": "Formulario cargado y registrado exitosamente",
  "form_id": 42,
  "details": {
    "form_serial": "01-001-001-01-001",
    "file_path": "backend/data/raw/01/001/001/01/001.pdf",
    "file_hash": "a1b2c3d4e5f6g7h8i9j0...",
    "file_size_mb": 0.052,
    "voting_table_id": 15,
    "uploaded_at": "2024-06-03T21:45:32.123456"
  }
}
```

#### Errores Posibles

**Caso 1: PDF no válido**
```json
{
  "success": false,
  "error": "El archivo no es un PDF válido"
}
```

**Caso 2: Tamaño excedido**
```json
{
  "success": false,
  "error": "El archivo excede el tamaño máximo de 10 MB"
}
```

**Caso 3: Ubicación no existe**
```json
{
  "success": false,
  "error": "La ubicación electoral no existe en la BD"
}
```

**Código HTTP**: 400 (Bad Request)

---

### 3️⃣ GET `/pdfs` - Listar Formularios

**Descripción**: Retorna lista de todos los PDFs registrados

**Método**: GET  
**Autenticación**: No requerida  
**Parámetros**: Ninguno

#### Con cURL

```bash
curl http://127.0.0.1:8000/pdfs

# Formateado (con jq):
curl http://127.0.0.1:8000/pdfs | jq '.'

# Con paginación (si se implementa):
curl "http://127.0.0.1:8000/pdfs?skip=0&limit=10"
```

#### Con JavaScript

```javascript
const response = await fetch('http://127.0.0.1:8000/pdfs');
const data = await response.json();
console.log(data);
```

#### Con Python

```python
import requests

response = requests.get('http://127.0.0.1:8000/pdfs')
data = response.json()
print(data)
```

#### Respuesta (200 OK)

```json
{
  "total": 30,
  "forms": [
    {
      "id": 1,
      "form_serial": "01-001-001-01-001",
      "department": "01",
      "municipality": "001",
      "zone": "001",
      "station": "01",
      "table_number": "001",
      "file_path": "backend/data/raw/01/001/001/01/001.pdf",
      "file_hash": "hash1...",
      "file_size_bytes": 53248,
      "created_at": "2024-06-03T21:30:00.000000"
    },
    {
      "id": 2,
      "form_serial": "01-001-001-01-002",
      "department": "01",
      "municipality": "001",
      "zone": "001",
      "station": "01",
      "table_number": "002",
      "file_path": "backend/data/raw/01/001/001/01/002.pdf",
      "file_hash": "hash2...",
      "file_size_bytes": 61440,
      "created_at": "2024-06-03T21:30:15.000000"
    },
    // ... 28 más
  ]
}
```

---

### 4️⃣ GET `/health` - Estado del Sistema

**Descripción**: Verifica que el servidor está activo

**Método**: GET  
**Autenticación**: No requerida

#### Con cURL

```bash
curl http://127.0.0.1:8000/health
```

#### Respuesta (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2024-06-03T21:49:26.047514",
  "election_id": "PRES_1V_2022",
  "database": "sqlite",
  "raw_data_dir": "/workspaces/E14-challenge/backend/data/raw"
}
```

---

### 5️⃣ GET `/docs` - Documentación Swagger

**Descripción**: Documentación interactiva de la API

```
http://127.0.0.1:8000/docs
```

Desde aquí puedes:
- ✅ Ver todos los endpoints
- ✅ Ver modelos de datos
- ✅ Probar endpoints en tiempo real
- ✅ Ver códigos de error

---

## 🧪 Ejemplos de Uso Completos

### Ejemplo 1: Upload vía HTML Form

```html
<!DOCTYPE html>
<html>
<head><title>Upload PDF</title></head>
<body>
  <form action="http://127.0.0.1:8000/upload-pdf" method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".pdf" required>
    <input type="text" name="dept_code" placeholder="01" required>
    <input type="text" name="muni_code" placeholder="001" required>
    <input type="text" name="zone_code" placeholder="001" required>
    <input type="text" name="station_code" placeholder="01" required>
    <input type="text" name="table_number" placeholder="001" required>
    <button type="submit">Cargar</button>
  </form>
</body>
</html>
```

### Ejemplo 2: Procesar respuesta en JavaScript

```javascript
document.querySelector('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  
  try {
    const response = await fetch('/upload-pdf', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert(`✅ Formulario ID: ${data.form_id}`);
      console.log(data.details);
    } else {
      alert(`❌ Error: ${data.error}`);
    }
  } catch (error) {
    console.error('Error:', error);
  }
});
```

### Ejemplo 3: Automatizar upload con Python

```python
import requests
import os
from pathlib import Path

BASE_URL = 'http://127.0.0.1:8000'

def upload_pdf(pdf_path, dept_code, muni_code, zone_code, station_code, table_number):
    """Sube un PDF a la API"""
    
    with open(pdf_path, 'rb') as f:
        files = {
            'file': f,
            'dept_code': (None, dept_code),
            'muni_code': (None, muni_code),
            'zone_code': (None, zone_code),
            'station_code': (None, station_code),
            'table_number': (None, table_number),
        }
        
        response = requests.post(
            f'{BASE_URL}/upload-pdf',
            files=files
        )
    
    return response.json()

# Uso
resultado = upload_pdf(
    'test.pdf',
    '01', '001', '001', '01', '001'
)

print(f"Exitoso: {resultado['success']}")
print(f"Form ID: {resultado['form_id']}")
```

---

## 📊 Códigos de Respuesta HTTP

| Código | Significado | Endpoint |
|--------|-------------|----------|
| 200 | OK - Exitoso | Todos |
| 400 | Bad Request - Datos inválidos | POST /upload-pdf |
| 404 | Not Found - Endpoint no existe | (raro) |
| 500 | Server Error - Error interno | Cualquiera |

---

## ⏱️ Límites y Cuotas

| Limite | Valor | Notas |
|--------|-------|-------|
| Tamaño máximo PDF | 10 MB | Configurable en `config.py` |
| Timeout request | 30s | Por defecto Uvicorn |
| Conexiones simultáneas | 1000 | Por defecto Uvicorn |

---

## 🔒 CORS (Cross-Origin)

La API tiene CORS habilitado para desarrollo. Puedes hacer requests desde cualquier origen.

**Producción**: Cambiar `allow_origins=['*']` a `allow_origins=['tudominio.com']`

---

## 📝 Headers Recomendados

```
Accept: application/json
User-Agent: E14-Challenge-Client/1.0
```

---

## 🚀 Flujo Típico de Integración

```
1. Usuario selecciona PDF en interfaz web
2. JavaScript valida en cliente (tipo, tamaño)
3. JavaScript envía POST /upload-pdf
4. Backend valida y procesa
5. Backend retorna form_id
6. JavaScript muestra resultado
7. Usuario ve PDF en lista GET /pdfs
```

---

## 🔗 Rutas Útiles

```
API Base:        http://127.0.0.1:8000
Upload UI:       http://127.0.0.1:8000/
API Docs:        http://127.0.0.1:8000/docs
Alternative:     http://127.0.0.1:8000/redoc
Health Check:    http://127.0.0.1:8000/health
List PDFs:       http://127.0.0.1:8000/pdfs
```

---

**Última actualización**: 3 Junio 2024  
**Versión API**: 1.0  
**Estado**: Producción ✅
