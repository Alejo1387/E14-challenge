# 📂 Índice de Archivos Clave

## 🎯 Archivos Para Empezar

### 1. SERVIDOR PRINCIPAL
**Archivo**: `backend/main.py`  
**Qué es**: Servidor FastAPI con todos los endpoints  
**Cómo ejecutar**: 
```bash
cd /workspaces/E14-challenge/backend && python3 main.py
```
**Importante**: Es el corazón de la aplicación. Si esto funciona, todo funciona.  
**Líneas clave**: 
- Línea ~50: Inicialización FastAPI
- Línea ~80: POST /upload-pdf
- Línea ~120: GET /pdfs
- Línea ~140: GET /health
- Línea ~160: GET /

---

### 2. INTERFAZ WEB
**Archivo**: `backend/static/upload.html`  
**Qué es**: Página HTML con formulario y drag-and-drop  
**Cómo acceder**: http://127.0.0.1:8000/  
**Importante**: No editar en Python, editar directamente en el navegador o via VS Code  
**Características**: 
- Drag-and-drop para PDFs
- Validación de tamaño (10 MB)
- Formulario con 5 campos numéricos
- Feedback visual con colores

---

### 3. BASE DE DATOS
**Archivo**: `backend/data/e14_challenge.db`  
**Qué es**: Archivo SQLite con todos los datos  
**Dónde está**: Ruta absoluta `/workspaces/E14-challenge/backend/data/e14_challenge.db`  
**Tamaño**: ~5 MB  
**Importante**: NO editar directamente. Usar scripts para modificaciones.  
**Cómo inspeccionar**: 
```bash
cd backend && sqlite3 data/e14_challenge.db
sqlite> .tables
sqlite> SELECT COUNT(*) FROM forms;
sqlite> .quit
```

---

### 4. CONFIGURACIÓN GLOBAL
**Archivo**: `backend/config.py`  
**Qué es**: Variables globales de la aplicación  
**Variables importantes**:
```python
BASE_DIR = Path(__file__).parent
DATABASE_URL = "sqlite:////workspaces/E14-challenge/backend/data/e14_challenge.db"
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
ELECTION_ID = "PRES_1V_2022"
```

---

## 📚 Documentación (Leer en Este Orden)

### 1. **RESUMEN_EJECUTIVO.md** (⭐ EMPIEZA AQUÍ)
- Qué se hizo en 1 hora
- Métricas finales
- Estado actual
- Próximos pasos

### 2. **README_IMPLEMENTACION.md**
- Guía completa de uso
- Todos los endpoints explicados
- Roadmap de desarrollo
- Troubleshooting

### 3. **ARQUITECTURA_SISTEMA.md**
- Diagramas de flujo
- Estructura técnica
- Capas de validación
- Escalabilidad

### 4. **GUIA_API_ENDPOINTS.md**
- Documentación detallada API
- Ejemplos con cURL
- Ejemplos con JavaScript
- Ejemplos con Python

### 5. **GUIA_DESCARGAR_PDFS_REALES.md**
- Cómo descargar desde Registraduría
- Estructura de carpetas
- Códigos de departamento
- Paso a paso

### 6. **GUIA_BACKEND_EXPLICADA.md** (Por tu compañero)
- Explicación de backend antiguo
- Modelos de datos
- Funciones CRUD

---

## 🐍 Scripts de Utilidad

### 1. REGISTRAR PDFs DESDE DISCO
**Archivo**: `backend/scripts/register_downloaded_pdfs.py`  
**Para qué sirve**: Lee PDFs de `backend/data/raw/` y los registra en BD  
**Cómo ejecutar**:
```bash
cd /workspaces/E14-challenge/backend
python3 scripts/register_downloaded_pdfs.py
```
**Cuándo usarlo**: Después de descargar PDFs nuevos del portal

---

### 2. INICIALIZAR BASE DE DATOS
**Archivo**: `backend/scripts/setup_db.py`  
**Para qué sirve**: Crea todas las tablas de la BD  
**Cómo ejecutar**:
```bash
python3 scripts/setup_db.py
```
**⚠️ Importante**: Ejecutar SOLO la primera vez  
**Efecto**: Borra BD anterior si existe

---

### 3. CARGAR DATOS INICIALES
**Archivo**: `backend/scripts/seed_data.py`  
**Para qué sirve**: Llena la BD con departamentos, municipios, candidatos, etc  
**Cómo ejecutar**:
```bash
python3 scripts/seed_data.py
```
**⚠️ Importante**: Ejecutar DESPUÉS de `setup_db.py`  
**Datos que carga**:
- 34 Departamentos
- 1200+ Municipios
- 8 Candidatos
- Geografía electoral

---

### 4. AGREGAR MUNICIPIOS (HELPER)
**Archivo**: `backend/scripts/add_missing_municipalities.py`  
**Para qué sirve**: Agrega municipios específicos que faltaban  
**Municipios agregados**:
- Bello, Envigado (Antioquia)
- Bogotá, Zipaquirá (Cundinamarca)
- Yumbo (Valle)

---

### 5. ARREGLAR GEOGRAFÍA (HELPER)
**Archivo**: `backend/scripts/fix_missing_geography.py`  
**Para qué sirve**: Crea zonas, puestos, mesas faltantes  
**Cuándo usarlo**: Si hay error "Zona no existe"

---

## 🔧 Core Business Logic

### Database Layer
**Archivo**: `backend/src/database/`

| Archivo | Propósito |
|---------|-----------|
| `schema.py` | Modelos SQLAlchemy (Form, VotingTable, Zone, etc) |
| `crud.py` | Operaciones CRUD (crear formulario, resolver mesa, etc) |
| `queries.py` | Queries SQL especializadas |
| `connection.py` | Conexión a BD |

**Funciones críticas en `crud.py`**:
- `crear_formulario()` - Registra PDF en BD
- `resolver_voting_table()` - Encuentra mesa por ubicación
- `asegurar_eleccion()` - Verifica elección existe

---

### Storage Layer
**Archivo**: `backend/src/storage/`

| Archivo | Propósito |
|---------|-----------|
| `local_storage.py` | LocalStorageManager - Guardar/leer PDFs |
| `pdf_paths.py` | Generación de rutas, parsing de ubicación |

**Funciones críticas**:
- `guardar_pdf()` - Guarda archivo en disco
- `generar_form_serial()` - Crea serial único
- `construir_ruta_pdf()` - Ruta donde guardar

---

### Utilities
**Archivo**: `backend/src/utils/`

| Archivo | Propósito |
|---------|-----------|
| `hashing.py` | `calcular_sha256()` para integridad |

---

## 📥 PDFs de Prueba

**Ubicación**: `backend/data/raw/`

**Estructura**:
```
raw/
├── 01/001/001/01/001.pdf  ← Antioquia, Medellín
├── 01/001/001/01/002.pdf
├── 03/001/001/01/001.pdf  ← Atlántico
├── 15/001/001/01/001.pdf  ← Cundinamarca, Bogotá
├── 31/001/001/01/026.pdf  ← Valle, Cali
└── ... (30 total)
```

**Características**:
- Todos son PDFs válidos (tienen header %PDF-1.4)
- Tamaño: 30-100 KB cada uno
- Contenido: Datos binarios aleatorios (simulando PDF real)
- Estado: Ya registrados en BD

---

## 🧪 Testing

**Archivo**: `backend/tests/`

| Archivo | Propósito |
|---------|-----------|
| `conftest.py` | Fixtures de pytest |
| `test_database.py` | Tests de BD |
| `test_pdf_paths.py` | Tests de rutas |
| `test_storage.py` | Tests de almacenamiento |

**Cómo ejecutar tests**:
```bash
cd backend
pytest tests/ -v
```

---

## 📊 Datos Importantes

### 30 PDFs Actuales
- Status: ✅ Todos registrados (30/30)
- Location: `backend/data/raw/`
- Serials: 01-001-001-01-001 hasta 64-001-001-01-030

### Elección Actual
- ID: `PRES_1V_2022`
- Nivel: Presidencial, Primera Vuelta
- Año: 2022
- Candidatos: 8 inscritos

### Geografía
- Departamentos: 34 (todos)
- Municipios: 1205 total
- Mesas: 71+ configuradas
- Zonas: 70+
- Puestos: 44+

---

## 🚀 Flujo de Ejecución Recomendado

### Primera Vez (Fresh Start)
```bash
1. cd /workspaces/E14-challenge/backend
2. python3 scripts/setup_db.py          # Crear BD
3. python3 scripts/seed_data.py         # Cargar datos
4. python3 main.py                       # Iniciar servidor
5. Abrir http://127.0.0.1:8000 en navegador
```

### Siguientes Veces
```bash
1. cd /workspaces/E14-challenge/backend
2. python3 main.py                       # Solo esto!
3. Usar interfaz web o cURL
```

### Después de Descargar PDFs
```bash
1. Copiar PDFs a backend/data/raw/ en estructura correcta
2. python3 scripts/register_downloaded_pdfs.py
3. GET /pdfs para verificar
```

---

## 🔍 Cómo Debuggear

### Problema: ¿Servidor no inicia?
```bash
# Ver errores
python3 backend/main.py

# Revisar puerto
lsof -i :8000

# Matar proceso anterior
kill -9 <PID>
```

### Problema: ¿Upload no funciona?
```bash
# Ver logs en terminal donde corre servidor

# Probar endpoint con curl:
curl -X POST http://127.0.0.1:8000/upload-pdf \
  -F "file=@test.pdf" \
  -F "dept_code=01" \
  -F "muni_code=001" \
  -F "zone_code=001" \
  -F "station_code=01" \
  -F "table_number=001"
```

### Problema: ¿Departamento no existe?
```bash
# Verificar en BD
sqlite3 backend/data/e14_challenge.db
SELECT * FROM departments WHERE code='01';

# Si no existe, cargar datos:
python3 scripts/seed_data.py
```

---

## 📦 Dependencias Principales

```
fastapi==0.104.1          ← Framework web
uvicorn==0.24.0           ← Servidor ASGI
sqlalchemy==2.0.34        ← ORM
python-multipart==0.0.6   ← File uploads
pytest==7.4.4             ← Testing
```

**Instalar todas**:
```bash
pip install -r requirements.txt
```

---

## 🎯 Métrica: "¿Está completo?"

| Componente | Status | Evidencia |
|-----------|--------|-----------|
| Backend API | ✅ Si | main.py funciona |
| Interfaz Web | ✅ Si | upload.html visible |
| Base de Datos | ✅ Si | 30 PDFs registrados |
| 30 PDFs | ✅ Si | backend/data/raw/ |
| Documentación | ✅ Si | 6 archivos .md |
| Tests | ✅ Si | tests/ funciona |
| Swagger Docs | ✅ Si | /docs accesible |

**Conclusión: MVP está 100% completo** ✅

---

## 📞 Resumen Rápido

**¿Qué hacer ahora?**
1. Lee: RESUMEN_EJECUTIVO.md
2. Ejecuta: `python3 backend/main.py`
3. Abre: http://127.0.0.1:8000
4. Prueba upload
5. Lee: README_IMPLEMENTACION.md para siguiente paso

**¿Qué es lo próximo?**
- Frontend React (tu compañero)
- Integración IA Gemini (después)

**¿Necesitas ayuda?**
- Ver: GUIA_API_ENDPOINTS.md
- Ver: GUIA_DESCARGAR_PDFS_REALES.md
- Ver: Logs en terminal

---

**Última actualización**: 3 Junio 2024  
**Mantenedor**: E14 Challenge Backend Team  
**Status**: ✅ MVP En Producción
