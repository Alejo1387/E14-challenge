# 🏗️ E14 Challenge - Arquitectura del Sistema

## 📊 Diagrama de Flujo General

```
┌─────────────────────────────────────────────────────────────────┐
│                    USUARIO FINAL                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Interfaz Web (React)  │  ← TO DO: Desarrollar
            │  http://localhost:3000 │
            └─────────┬──────────────┘
                      │
                      ▼
    ┌─────────────────────────────────┐
    │      API REST (FastAPI)         │  ✅ READY
    │  http://localhost:8000/api      │
    └────────────┬────────────────────┘
                 │
         ┌───────┴───────┬─────────────┐
         ▼               ▼             ▼
    ┌────────┐   ┌──────────┐   ┌─────────┐
    │ Upload │   │ Process  │   │ AI      │  ← AI Integration: TO DO
    │ Handler│   │ Handler  │   │ Handler │     (Gemini API)
    └───┬────┘   └──────┬───┘   └────┬────┘
        │                │           │
        └────────────────┼───────────┘
                         ▼
    ┌──────────────────────────────────┐
    │  Storage Manager                 │
    │  (Disk I/O, Validation)          │
    │  backend/src/storage/            │
    └────────┬─────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────┐
    │  PDF Files on Disk               │
    │  backend/data/raw/               │
    │  {depto}/{muni}/{zona}/{puesto}/ │
    │  {mesa}.pdf                      │
    │  (30 test files currently)       │
    └──────────────────────────────────┘
         
         PARALELO:
         
    ┌──────────────────────────────────┐
    │  Database Layer (SQLAlchemy)     │
    │  backend/src/database/           │
    └────────┬─────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────┐
    │  SQLite Database                 │
    │  backend/data/                   │
    │  e14_challenge.db                │
    │  (All metadata, forms registry)  │
    └──────────────────────────────────┘
```

---

## 🔄 Flujo de Carga de PDF

```
1. USUARIO CARGA PDF
   ↓
2. VALIDACIÓN CLIENTE (upload.html)
   • ¿Es PDF? (extension check)
   • ¿Tamaño < 10MB?
   • ¿Códigos válidos?
   ↓
3. ENVÍO A SERVIDOR
   POST /upload-pdf
   {
     file: <PDF_BINARY>,
     dept_code: "01",
     muni_code: "001",
     zone_code: "001",
     station_code: "01",
     table_number: "001"
   }
   ↓
4. VALIDACIÓN SERVIDOR (FastAPI)
   • ¿Header PDF válido?
   • ¿Tamaño < 10MB?
   • ¿Ubicación existe en BD?
   ↓
5. GUARDAR DISCO
   Ruta: backend/data/raw/{depto}/{muni}/{zona}/{puesto}/{mesa}.pdf
   Calcula SHA-256 hash
   ↓
6. REGISTRAR BD
   Tabla: forms
   • form_serial
   • file_path
   • file_hash
   • file_size_mb
   • voting_table_id
   • created_at
   ↓
7. RESPUESTA A USUARIO
   {
     "success": true,
     "form_id": 42,
     "details": {
       "form_serial": "01-001-001-01-001",
       "file_hash": "abc123...",
       "file_size_mb": 0.052,
       "uploaded_at": "2024-06-03T..."
     }
   }
   ↓
8. INTERFAZ MUESTRA RESULTADO
   ✅ Formulario registrado exitosamente
```

---

## 📂 Estructura de Archivos Actual

```
backend/
├── main.py                           ← Servidor FastAPI (ACTIVO ✅)
├── config.py                         ← Configuración global
├── requirements.txt                  ← Dependencias pip
├── pytest.ini                        ← Configuración pytest
│
├── static/
│   └── upload.html                   ← Interfaz web (LISTA ✅)
│
├── data/
│   ├── raw/                          ← Almacenamiento PDFs
│   │   ├── 01/001/001/01/001.pdf    │
│   │   ├── 01/001/001/01/002.pdf    │ 30 PDFs
│   │   ├── ...                       │ generados
│   │   └── 64/001/001/01/030.pdf    │
│   │
│   ├── processed/                    ← Para post-procesamiento (vacío)
│   │
│   ├── e14_challenge.db              ← Base de datos SQLite (ACTIVA ✅)
│   └── logs/                         ← Logs de la aplicación
│
├── scripts/
│   ├── register_downloaded_pdfs.py   ← Registrar PDFs del disco
│   ├── seed_data.py                  ← Cargar datos iniciales
│   ├── setup_db.py                   ← Crear tablas
│   ├── fix_missing_geography.py      ← Helper: geografía faltante
│   ├── add_missing_municipalities.py ← Helper: municipios faltantes
│   └── inspect_db.py                 ← Inspeccionar BD
│
└── src/
    ├── __init__.py
    ├── database/
    │   ├── __init__.py
    │   ├── connection.py              ← Conexión BD
    │   ├── crud.py                    ← Operaciones BD (CREATE, READ, UPDATE, DELETE)
    │   ├── queries.py                 ← Queries específicas
    │   └── schema.py                  ← Modelos SQLAlchemy
    │
    ├── storage/
    │   ├── __init__.py
    │   ├── local_storage.py           ← LocalStorageManager (guardar, leer, verificar PDFs)
    │   └── pdf_paths.py               ← Utilidades de rutas
    │
    └── utils/
        ├── __init__.py
        └── hashing.py                 ← Cálculo de SHA-256
```

---

## 🔌 Interfaces de Componentes

### FastAPI (main.py)
```
Input:  HTTP Request (multipart or JSON)
        └─ POST /upload-pdf
           └─ file: UploadFile
           └─ dept_code, muni_code, zone_code, station_code, table_number

Process: Validación → Guardado → Registro BD

Output: HTTP Response (JSON)
        └─ {success, form_id, details}
```

### Storage Manager (local_storage.py)
```
Input:  PDF binary data + ubicación (dept, muni, zona, puesto, mesa)

Process: 
  1. Crear estructura de carpetas si no existe
  2. Calcular ruta según convención
  3. Guardar archivo
  4. Calcular SHA-256

Output: (path, hash, size)
```

### CRUD Layer (crud.py)
```
Input:  Datos de formulario (form_serial, file_path, file_hash, etc)

Process:
  1. Buscar voting_table por ubicación
  2. Crear registro Form
  3. Guardar en BD

Output: Form object con form_id asignado
```

### Database (e14_challenge.db)
```
Tablas principales:
├── forms                    ← Formularios cargados (30 actualmente)
├── voting_tables            ← Mesas de votación (71+)
├── zones                    ← Zonas electorales (70+)
├── stations                 ← Puestos de votación (44+)
├── municipalities           ← Municipios (1200+)
├── departments              ← Departamentos (34)
├── elections                ← Elecciones (PRES_1V_2022)
├── election_candidates      ← Candidatos (8 para PRES_1V_2022)
├── extraction_results       ← Vacío (para IA)
├── anomalies                ← Vacío (para IA)
└── candidate_votes          ← Vacío (para IA)
```

---

## 🔐 Validación en Capas

### Capa 1: Cliente (JavaScript)
```javascript
✓ Validar tipo MIME: application/pdf
✓ Validar tamaño: < 10MB
✓ Validar códigos: formato correcto (2/3 dígitos)
✓ Feedback visual: errores antes de enviar
```

### Capa 2: API (FastAPI)
```python
✓ Validar header PDF: comienza con %PDF
✓ Validar tamaño: < 10MB
✓ Validar formato de códigos
✓ Validar existencia en BD (geografía)
✓ Manejo de excepciones
```

### Capa 3: Storage
```python
✓ Crear estructura de carpetas
✓ Escribir archivo con integridad
✓ Calcular hash para verificación
✓ Manejo de permisos
```

### Capa 4: BD
```sql
✓ Constraints de integridad referencial
✓ Validación de tipos de datos
✓ Índices para búsquedas rápidas
```

---

## 📈 Escalabilidad & Roadmap

### Fase 1: MVP (ACTUAL ✅)
- [x] Backend API con upload básico
- [x] Interfaz web simple
- [x] 30 PDFs de prueba
- [x] Base de datos completa con geografía

### Fase 2: Frontend React (PRÓXIMA)
- [ ] Dashboard bonito
- [ ] Tabla de PDFs cargados
- [ ] Búsqueda y filtros
- [ ] Visualización individual de PDFs
- [ ] Estadísticas por departamento

### Fase 3: IA Integration (DESPUÉS)
- [ ] Endpoint de procesamiento con Gemini
- [ ] Extracción de datos del PDF
- [ ] Detección de anomalías
- [ ] Almacenamiento de resultados

### Fase 4: Scraping Real (OPCIONAL)
- [ ] Descarga automatizada desde Registraduría
- [ ] Manejo de CAPTCHAs
- [ ] Descarga masiva y scheduling

### Fase 5: Production (FUTURO)
- [ ] Migrar a PostgreSQL
- [ ] Deploy en servidor (AWS/GCP/Azure)
- [ ] Autenticación de usuarios
- [ ] Autorización por roles
- [ ] Caché con Redis
- [ ] Colas de procesamiento (Celery)

---

## 🔄 Variables de Configuración

```python
# config.py
BASE_DIR = Path(__file__).parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATABASE_URL = "sqlite:////workspaces/E14-challenge/backend/data/e14_challenge.db"
ELECTION_ID = "PRES_1V_2022"  # Elección seleccionada
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
```

---

## 🚀 Cómo Ejecutar

```bash
# 1. Instalar dependencias
cd /workspaces/E14-challenge/backend
pip install -r requirements.txt

# 2. Inicializar BD (si es primera vez)
python3 scripts/setup_db.py
python3 scripts/seed_data.py

# 3. Iniciar servidor
python3 main.py

# 4. Acceder
http://127.0.0.1:8000/              ← Interfaz upload
http://127.0.0.1:8000/docs          ← API Swagger
http://127.0.0.1:8000/pdfs          ← Listar PDFs (JSON)
```

---

## 🔗 Dependencias Clave

| Librería | Versión | Propósito |
|----------|---------|----------|
| FastAPI | 0.104.1 | Framework web async |
| Uvicorn | 0.24.0 | Servidor ASGI |
| SQLAlchemy | 2.0.34 | ORM para BD |
| python-multipart | 0.0.6 | Parsing de multipart/form-data |
| pytest | 7.4.4 | Testing (para tests/) |

---

## ✅ Checklist de Operación

- [x] FastAPI server activo
- [x] Base de datos inicializada
- [x] 30 PDFs generados y registrados
- [x] Interfaz web funcional
- [x] Validación en cliente y servidor
- [x] Endpoints documentados
- [ ] Frontend React (PRÓXIMO)
- [ ] Integración IA (PRÓXIMO)

---

**Arquitectura lista para escalabilidad. MVP funcional y en producción.** 🚀
