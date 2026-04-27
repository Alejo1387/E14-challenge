# 🎓 Guía Completa del Backend - E14 Challenge
## Para Entender la Estructura del Proyecto (Super Explicado)

---

## 📚 Tabla de Contenidos

1. [Introducción: ¿Qué es el Backend?](#introducción-qué-es-el-backend)
2. [Estructura de Carpetas](#estructura-de-carpetas)
3. [Los Archivos Principales](#los-archivos-principales)
4. [Las Relaciones Entre Archivos](#las-relaciones-entre-archivos)
5. [Flujo de Datos (Cómo Funciona Todo)](#flujo-de-datos)

---

## 🤔 Introducción: ¿Qué es el Backend?

Imagina que tu proyecto es un **restaurante**:

- **Backend** = La cocina (donde se prepara la comida)
- **Frontend** = La sala (donde come la gente)
- **Base de Datos** = La despensa (donde se guardan los ingredientes)

El **backend** es el responsable de:
- ✅ Guardar datos en la base de datos
- ✅ Recuperar datos cuando se necesitan
- ✅ Procesar información
- ✅ Verificar que todo sea válido
- ✅ Organizar y guardar archivos (PDFs)

---

## 📁 Estructura de Carpetas

Aquí te muestro cómo se organiza el backend:

```
backend/
│
├── config.py                 👈 La "guía de configuración"
│
├── data/                     👈 La "despensa" (donde se guardan cosas)
│   ├── raw/                 └─ PDFs sin procesar (como llegan)
│   ├── processed/           └─ PDFs ya procesados
│   └── e14_challenge.db     └─ La base de datos (archivo)
│
├── logs/                     👈 "Diario" de lo que hace el programa
│
├── scripts/                  👈 "Guiones" para tareas especiales
│   ├── setup_db.py         └─ Script para crear BD
│   ├── seed_data.py        └─ Script para llenar BD con datos de prueba
│   └── register_downloaded_pdfs.py └─ Script para registrar PDFs
│
└── src/                      👈 El "corazón" del programa
    │
    ├── __init__.py
    │
    ├── database/            👈 "Gestor de la base de datos"
    │   ├── __init__.py
    │   ├── connection.py     └─ Cómo conectarse a la BD
    │   ├── schema.py        └─ La estructura de las tablas
    │   ├── crud.py          └─ Crear, leer, actualizar, eliminar
    │   └── queries.py       └─ Consultas especiales
    │
    ├── api/                  👈 "Interfaz" para hablar con el programa
    │   └── routes/          └─ Las "rutas" (endpoints)
    │
    ├── storage/             👈 "Gestor de archivos"
    │   ├── __init__.py
    │   └── local_storage.py └─ Guardar/leer PDFs en disco
    │
    └── utils/               👈 "Herramientas útiles"
        ├── __init__.py
        └── hashing.py       └─ Calcular códigos de archivos
```

---

## 📄 Los Archivos Principales

Ahora te explico qué hace **cada archivo** en detalle:

### 1️⃣ `config.py` - La "Guía de Configuración"

**¿Qué es?**

Es como el **"carnet de identidad"** del proyecto. Define:
- ¿Dónde se guardan las cosas?
- ¿Cuáles son los nombres de las carpetas?
- ¿Qué elección estamos procesando?
- ¿Qué reglas tenemos? (tamaño máximo, extensiones, etc.)

**Analógía:**

Imagina que es una lista pegada en la pared de tu casa que dice:
```
- Carpeta de PDFs: /home/usuario/backend/data/raw
- BD está en: /home/usuario/backend/data/e14_challenge.db
- La elección es: PRES_1V_2022
- PDFs no deben pesar más de: 10 MB
```

**¿Por qué existe?**

En lugar de escribir la ruta completa en 50 archivos diferentes, solo la escribes UNA VEZ en `config.py`, y todos los demás archivos la importan.

**Ejemplo:**

```python
# En config.py (se define UNA sola vez)
DATABASE_URL = "sqlite:////home/.../backend/data/e14_challenge.db"

# En otros archivos (se importa y se usa)
from config import DATABASE_URL
print(DATABASE_URL)  # ✅ Usa la que está en config.py
```

---

### 2️⃣ `schema.py` - El "Plano Arquitectónico" de la BD

**¿Qué es?**

Define **cómo se vee la base de datos**. Es como un "plano" que dice:

```
┌─────────────────────────┐
│     DEPARTAMENTOS       │
├─────────────────────────┤
│ code      │ "05"        │
│ name      │ "Antioquia" │
│ created_at│ 2026-04-17  │
└─────────────────────────┘
```

**¿Por qué existe?**

Porque SQLAlchemy necesita saber:
- ¿Qué tablas existen?
- ¿Cuáles son las columnas?
- ¿Qué tipo de dato tiene cada columna?
- ¿Cuál es la relación entre tablas?

**Las Tablas que Define:**

1. **`departments`** (Departamentos de Colombia)
   - `code`: "05", "11", etc.
   - `name`: "Antioquia", "Bogotá D.C.", etc.

2. **`municipalities`** (Ciudades/Municipios)
   - `code`: "001", "002", etc.
   - `department_code`: "05" (relación con departments)
   - `name`: "Medellín", "Bogotá", etc.

3. **`zones`** (Zonas de votación dentro de un municipio)
   - `id`: 1, 2, 3, etc.
   - `municipality_code`: "001"
   - `zone_number`: "01", "02", etc.

4. **`stations`** (Puestos de votación - escuelas, centros comunitarios)
   - `id`: 1, 2, 3, etc.
   - `zone_id`: 1, 2, etc. (relación con zones)
   - `name`: "Escuela La Esperanza", etc.
   - `address`: Dirección del puesto

5. **`voting_tables`** (Mesas de votación)
   - `id`: 1, 2, 3, etc.
   - `station_id`: 1 (relación con stations)
   - `table_number`: "031", "032", etc.
   - `registered_voters`: 400, 380, etc.

6. **`forms`** (Formularios E-14 descargados)
   - `id`: 1, 2, 3, etc.
   - `form_serial`: "5036317" (código único del PDF)
   - `local_path`: "data/raw/05_Antioquia/001_Medellin/5036317.pdf"
   - `file_hash`: "a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9..." (código de verificación)
   - `processing_status`: "PENDING", "EXTRACTED", "ANALYZED", "FAILED"

**Relación Entre Tablas (El Árbol Genealógico):**

```
DEPARTAMENTOS
    ↓
    └─→ MUNICIPIOS
        ↓
        └─→ ZONAS
            ↓
            └─→ ESTACIONES
                ↓
                └─→ MESAS
                    ↓
                    └─→ FORMULARIOS E-14
```

---

### 3️⃣ `connection.py` - Cómo Conectarse a la BD

**¿Qué es?**

Es el **"gestor de conexiones"**. Crea y maneja la comunicación entre Python y la base de datos.

**¿Por qué existe?**

Porque conectarse a una BD es complicado:
- ¿De dónde obtener la conexión?
- ¿Cómo reutilizarla?
- ¿Cómo cerrarla correctamente?

En lugar de resolver esto en cada archivo, lo hacemos UNA VEZ en `connection.py`.

**Las Funciones Principales:**

#### `get_engine()`
- **¿Qué hace?** Crea el "intermediario" entre Python y la BD
- **¿Cuándo se crea?** UNA sola vez (después se reutiliza)
- **Ejemplo:**
  ```python
  engine = get_engine()  # ✅ Crea conexión a la BD
  ```

#### `get_session()`
- **¿Qué hace?** Crea una nueva "conversación" con la BD
- **¿Para qué?** Para hacer consultas (SELECT, INSERT, UPDATE, DELETE)
- **Ejemplo:**
  ```python
  session = get_session()          # ✅ Abre conversación
  users = session.query(User).all() # ✅ Pregunta
  session.close()                   # ✅ Cierra conversación
  ```

#### `session_scope()` - El Context Manager
- **¿Qué es?** Permite usar `with` para cerrar automáticamente
- **¿Por qué es importante?** Garantiza que se cierre aunque haya error
- **Ejemplo:**
  ```python
  # ✅ CORRECTO (se cierra automáticamente)
  with session_scope() as session:
      users = session.query(User).all()
  
  # ❌ INCORRECTO (si hay error, no se cierra)
  session = get_session()
  users = session.query(User).all()
  # OLVIDAS session.close()
  ```

#### `verificar_conexion()`
- **¿Qué hace?** Prueba si la BD está accesible
- **¿Cuándo usarlo?** Para diagnosticar problemas
- **Ejemplo:**
  ```python
  if verificar_conexion():
      print("✅ BD accesible")
  else:
      print("❌ BD no funciona")
  ```

---

### 4️⃣ `hashing.py` - Calcular Códigos de Archivos

**¿Qué es?**

Calcula un **código único** (SHA-256) para cada PDF.

**¿Para qué?**

Imagina que descargaste un PDF, pero mientras estabas descargando se cortó internet y el archivo se dañó. ¿Cómo sabes?

Con el hash:
1. El servidor calcula y dice: "Este PDF tiene hash `a3c5f7e2...`"
2. Tú descargas el archivo
3. Tú calculas el hash: `a3c5f7e2...`
4. Comparas: ¿Coinciden? ✅ Sí → El archivo está bien | ❌ No → Se dañó
5. Si está dañado, descargas de nuevo

**¿Cómo funciona?**

```
Entrada: PDF de Medellín  →  SHA-256  →  "a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9..."
```

**Las Funciones:**

#### `calcular_sha256(ruta_archivo)`
```python
hash_pdf = calcular_sha256("backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf")
# Devuelve: "a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9..." (64 caracteres)
```

**Propiedad Mágica:** Si cambias UN solo bit del PDF, el hash es completamente diferente:

```
PDF original:  a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9
PDF con error: b4d6e8f3e0c5d9g2f3e4b5c6d7e8f0ga  ← Totalmente diferente
```

---

### 5️⃣ `local_storage.py` - Gestor de Archivos

**¿Qué es?**

Es el **"bibliotecario"** que:
- Organiza PDFs en carpetas
- Guarda PDFs en el disco
- Lee PDFs cuando se necesitan
- Verifica que los PDFs no estén dañados

**¿Por qué existe?**

Porque guardar archivos tiene complejidad:
- ¿En qué carpeta guardar?
- ¿Crear carpetas automáticamente?
- ¿Verificar integridad?
- ¿Qué pasa si el nombre duplicado?

**La Clase Principal: `LocalStorageManager`**

```python
# Crear un "bibliotecario"
manager = LocalStorageManager()

# Guardar un PDF
ruta = manager.guardar_pdf(
    contenido_bytes=pdf_bytes,
    dept_code="05",
    dept_name="Antioquia",
    muni_code="001",
    muni_name="Medellin",
    form_serial="5036317"
)
# Resultado: "backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf"

# Leer un PDF
contenido = manager.leer_pdf(ruta)

# Verificar integridad
¿Es válido el PDF? manager.es_hash_valido(ruta, hash_esperado)
```

**Estructura de Carpetas:**

```
data/
└── raw/                          (PDFs sin procesar)
    └── 05_Antioquia/            (Por departamento)
        └── 001_Medellin/        (Por municipio)
            ├── 5036317.pdf      ✅ PDF descargado
            ├── 5036318.pdf      ✅ PDF descargado
            └── ...
```

---

### 6️⃣ `scripts/`:  Los "Guiones" del Programa

Son scripts que **se ejecutan desde la terminal** para tareas especiales:

#### `setup_db.py` - Crear la Base de Datos

**¿Qué hace?**
- Crea todas las tablas (según el schema)
- Prepara la BD para recibir datos
- Se ejecuta UNA sola vez

**¿Cómo se usa?**
```bash
python backend/scripts/setup_db.py
```

**¿Qué pasa?**
```
✅ Tablas creadas en: sqlite:///backend/data/e14_challenge.db
```

---

#### `seed_data.py` - Llenar la BD con Datos de Prueba

**¿Qué hace?**
- Inserta 32 departamentos (reales de Colombia)
- Inserta 12 municipios (Bogotá, Medellín, Cali, etc.)
- Inserta 36 zonas ficticias
- Inserta 405 estaciones ficticias
- Inserta 2900+ mesas ficticias
- Inserta 10 PDFs de prueba

**¿Por qué?**

Para que tengas datos con los que "jugar" mientras desarrollas.

**¿Cómo se usa?**
```bash
python backend/scripts/seed_data.py
```

**¿Qué pasa?**
```
🌱 LLENANDO BASE DE DATOS CON DATOS DE PRUEBA
✅ 32 departamentos insertados
✅ 12 municipios insertados
✅ 36 zonas insertadas
✅ 405 estaciones insertadas
✅ 2900+ mesas insertadas
✅ 10 PDFs de prueba insertados
```

---

#### `register_downloaded_pdfs.py` - Registrar PDFs Descargados

**¿Qué hace?**
- Busca PDFs en `data/raw/`
- Los registra en la BD
- Calcula y guarda el hash de cada uno

**¿Cómo se usa?**
```bash
python backend/scripts/register_downloaded_pdfs.py
```

**¿Qué pasa?**
```
📝 Registrando PDFs descargados...
✅ 5036317.pdf registrado
✅ 5036318.pdf registrado
...
✅ 150 PDFs registrados
```

---

## 🔗 Las Relaciones Entre Archivos

Aquí te muestro **cómo se comunican** los archivos:

### Relación 1: `config.py` → Todos

```python
# Archivo 1: config.py
DATABASE_URL = "sqlite:///backend/data/e14_challenge.db"
ELECTION_ID = "PRES_1V_2022"
DATA_RAW_DIR = Path(__file__).parent / "data" / "raw"

# Archivo 2: connection.py (importa config)
from config import DATABASE_URL
engine = create_engine(DATABASE_URL)  # ✅ Usa DATABASE_URL

# Archivo 3: local_storage.py (importa config)
from config import DATA_RAW_DIR
carpeta = DATA_RAW_DIR / "05_Antioquia"  # ✅ Usa DATA_RAW_DIR

# Archivo 4: seed_data.py (importa config)
from config import ELECTION_ID
form = Form(election_id=ELECTION_ID)  # ✅ Usa ELECTION_ID
```

**¿De verdad es importante?**

Sí, porque si cambias la ruta de la BD, solo cambias `config.py` y todos los demás archivos automáticamente usan la nueva ruta. Si no fuera así, tendrías que cambiar 50 archivos.

---

### Relación 2: `connection.py` → `schema.py`

```python
# connection.py (crea la conexión)
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
session = sessionmaker(bind=engine)()

# schema.py (define las tablas)
class Department(Base):
    __tablename__ = "departments"
    code = Column(String(2), primary_key=True)
    name = Column(String(100))

# Cómo se usa:
from src.database.connection import get_session
from src.database.schema import Department

session = get_session()  # ✅ Abre conversación
depts = session.query(Department).all()  # ✅ Pregunta por departments
session.close()  # ✅ Cierra conversación
```

---

### Relación 3: `hashing.py` → `local_storage.py`

```python
# hashing.py (calcula hashes)
def calcular_sha256(ruta_archivo):
    # ... calcula y devuelve hash

# local_storage.py (usa el hash)
from src.utils.hashing import calcular_sha256

class LocalStorageManager:
    def guardar_pdf(self, contenido, ...):
        # 1. Guarda el PDF
        pdf_path.write_bytes(contenido)
        
        # 2. Calcula su hash (para verificación)
        hash_file = calcular_sha256(pdf_path)  # ✅ Usa hashing
        
        # 3. Guarda el hash en la BD
        return hash_file
```

---

### Relación 4: `all` → `scripts`

```python
# scripts/seed_data.py (usa todos los archivos)
from config import DATABASE_URL, ELECTION_ID
from src.database.schema import Department, Municipality, ...
from src.database.connection import get_session

def insertar_departamentos(session):
    for code, name in DEPARTAMENTOS_COLOMBIA:  # ✅ Usa config
        dept = Department(code=code, name=name)  # ✅ Usa schema
        session.add(dept)  # ✅ Usa connection
    session.commit()
```

---

## 📊 Flujo de Datos (Cómo Funciona Todo)

Ahora veamos **qué sucede cuando haces algo** en el proyecto:

### Escenario 1: Ejecutar `setup_db.py`

```
1. Terminal
   └─ python backend/scripts/setup_db.py

2. setup_db.py
   └─ Importa: from src.database.schema import Base, create_engine
   └─ Importa: from config import DATABASE_URL

3. connection.py (indirectamente)
   └─ Crea engine para la BD
   └─ Conexión a: sqlite:///backend/data/e14_challenge.db

4. schema.py
   └─ Define todas las tablas:
      ├─ departments
      ├─ municipalities
      ├─ zones
      ├─ stations
      ├─ voting_tables
      └─ forms

5. Base de Datos
   └─ ✅ Se crean todas las tablas (vacías, sin datos)

6. Terminal
   └─ ✅ Tablas creadas en: sqlite:///backend/data/e14_challenge.db
```

---

### Escenario 2: Ejecutar `seed_data.py`

```
1. Terminal
   └─ python backend/scripts/seed_data.py

2. seed_data.py
   └─ Importa todo (config, schema, connection, hashing)
   └─ Importa: DEPARTAMENTOS_COLOMBIA (lista hardcodeada)

3. connection.py
   └─ get_session() crea una sesión
   └─ Conversación abierta con la BD

4. Función: insertar_departamentos()
   └─ Lee DEPARTAMENTOS_COLOMBIA
      ├─ Crea objeto Department
      ├─ session.add(dept)  ← Lo añade a la sesión
      └─ Repite para los 32 departamentos
   └─ session.commit()  ← **GUARDA todo en la BD**

5. Base de Datos
   └─ ✅ INSERT INTO departments (code, name) VALUES ('01', 'Amazonas')
   └─ ✅ INSERT INTO departments (code, name) VALUES ('02', 'Antioquia')
   └─ ... (32 veces)

6. Función: insertar_municipios()
   └─ Lo mismo que #4, pero para municipios
   └─ Crea relación: municipio → departamento

7. Función: insertar_geografia_votacion()
   └─ Para cada municipio:
      ├─ Crea 3 zonas
      ├─ Para cada zona, crea 5 estaciones
      ├─ Para cada estación, crea 3-4 mesas
      └─ Todo se guarda en BD

8. Función: insertar_pdfs_prueba()
   └─ Crea 10 PDFs ficticios
   └─ Los registra en tabla `forms`
   └─ Calcula hash usando hashing.py

9. Terminal
   └─ ✅ 32 departamentos insertados
   └─ ✅ 12 municipios insertados
   └─ ✅ 36 zonas insertadas
   └─ ✅ 405 estaciones insertadas
   └─ ✅ 2900+ mesas insertadas
   └─ ✅ 10 PDFs de prueba insertados
```

---

### Escenario 3: Descarga de PDFs Reales (Futuro)

```
1. Persona A descarga PDFs
   └─ Los guarda en: backend/data/raw/05_Antioquia/001_Medellin/...'

2. Terminal
   └─ python backend/scripts/register_downloaded_pdfs.py

3. register_downloaded_pdfs.py
   └─ Busca PDFs en backend/data/raw/
   └─ Para cada PDF:
      ├─ Leer contenido (usando local_storage.py)
      ├─ Calcular hash (usando hashing.py)
      ├─ Crear objeto Form (con datos de schema.py)
      ├─ Guardar en BD (usando connection.py)
      └─ Pasar al siguiente

4. Base de Datos
   └─ ✅ INSERT INTO forms
      ├─ form_serial: "5036317"
      ├─ local_path: "backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf"
      ├─ file_hash: "a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9..."
      ├─ processing_status: "PENDING"
      └─ download_timestamp: 2026-04-17 10:30:45

5. Terminal
   └─ ✅ 150 PDFs registrados en la BD
```

---

## 🎯 Resumen: El Flujo Completo

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  1. config.py (PUNTO DE PARTIDA)                       │
│  └─ Define dónde está TODO                             │
│                                                         │
│  2. connection.py (CARRETERA)                          │
│  └─ Crea el camino entre Python y la BD                │
│                                                         │
│  3. schema.py (PLANO)                                  │
│  └─ Define la estructura de las tablas                 │
│                                                         │
│  4. scripts/ (MÁQUINAS)                                │
│  ├─ setup_db.py: Crea tablas vacías                   │
│  ├─ seed_data.py: Llena con datos de prueba           │
│  └─ register_downloaded_pdfs.py: Registra PDFs reales │
│                                                         │
│  5. Utilidades (HERRAMIENTAS)                          │
│  ├─ hashing.py: Calcula códigos de archivos           │
│  └─ local_storage.py: Organiza archivos               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Analogía Final: El Restaurante

Imagina todo el backend como un **restaurante**:

| Componente | Rol |
|-----------|-----|
| **config.py** | El gerente que dice dónde está todo |
| **schema.py** | El plano del restaurante (mesas, cocina, baños) |
| **connection.py** | El teléfono entre sala y cocina |
| **hashing.py** | El inspector de calidad que verifica comida |
| **local_storage.py** | El almacenero que guarda ingredientes |
| **scripts/** | Los únicos trabajadores que hacen tareas |
| **Base de Datos** | La despensa donde se guardan ingredientes |

**Cuando alguien ordena un plato:**

1. El mesero (API) toma la orden
2. La pasa por el teléfono (connection.py)
3. La cocina (backend) la recibe
4. El cocinero (scripts) prepara el plato
5. El inspector (hashing.py) verifica calidad
6. El mesero trae el plato

---

## 🎓 Próximos Pasos para Aprender

Una vez que entiendas esto, aprenderás:

1. **API (routes/)**: Cómo recibir órdenes del frontend
2. **CRUD Operations (crud.py)**: Crear, leer, actualizar, eliminar datos
3. **Advanced Queries (queries.py)**: Preguntas complejas a la BD
4. **OCR Processing**: Leer el contenido de los PDFs
5. **Error Handling**: Qué hacer cuando algo sale mal

---

## 📝 Notas Importantes

> **Nota 1:** El archivo `__init__.py` en cada carpeta simplemente dice "esta carpeta es un módulo Python" (es como un cartel que dice "Soy una sala del restaurante").

> **Nota 2:** `__pycache__/` es una carpeta que Python crea automáticamente con versiones compiladas de los archivos (es como basura, la ignoras).

> **Nota 3:** El archivo `.gitignore` dice qué cosas NO subir a GitHub (como archivos grandes, bases de datos, etc.).

---

## 🚀 Conclusión

El backend es un **sistema bien organizado** donde:

- ✅ Cada archivo tiene UN trabajo específico
- ✅ Los archivos se comunican claramente
- ✅ Es fácil agregar nuevas funciones
- ✅ Es fácil encontrar y arreglar errores
- ✅ Otro programador puede entender el código

**¡Felicitaciones por intentar entender cómo funciona!** 🎉

---

*Documento creado como guía de aprendizaje - E14 Challenge Backend*
