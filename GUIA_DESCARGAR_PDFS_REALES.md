# 📥 Guía: Cómo Descargar PDFs Reales desde la Registraduría

## 🎯 Objetivo
Descargar formularios E-14 reales desde https://presidente1v2022.registraduria.gov.co/ y procesarlos con nuestro backend.

## 📋 Requisitos
- Navegador web (Chrome, Firefox, Safari)
- ~30 minutos para descargar 30 formularios
- Estructura esperada: `backend/data/raw/{depto}/{muni}/{zona}/{puesto}/{mesa}.pdf`

---

## 🔗 Paso 1: Acceder al Portal

1. Abre: https://presidente1v2022.registraduria.gov.co/
2. Verás un menú lateral con opciones
3. Selecciona "Formularios E-14" o "Actas de Escrutinio"
4. El portal es dinámico (JavaScript) - puede tardar en cargar

---

## 🌍 Paso 2: Seleccionar Ubicación Electoral

El portal requiere que selecciones:

1. **Corporación**: Presidente (PRE)
2. **Departamento**: Ej: Antioquia, Cundinamarca, etc
3. **Municipio**: Ej: Medellín, Bogotá, etc
4. **Zona**: Número de zona (001, 002, etc)
5. **Puesto**: Número del puesto de votación (01, 02, etc)

**Luego**: Haz clic en "Consultar"

---

## 📊 Paso 3: Descargar Formularios

Después de "Consultar", verás una tabla con **mesas de votación**.

Cada fila representa una mesa con un botón de descarga. 

**Para descargar:**
1. Identifica el número de mesa (ej: 001, 002, etc)
2. Haz clic en el botón descargar (ícono 📥 o PDF)
3. Se descargará un archivo `.pdf`

**⚠️ IMPORTANTE - Cambiar Nombre del Archivo:**

El archivo descargado probablemente se llamará algo genérico como `descargae14.pdf`.

**Debes renombrarlo** según la estructura correcta:
- **Nombre correcto**: `{numero_de_mesa}.pdf` (ej: `001.pdf`, `002.pdf`)
- **Luego colocarlo en**: `/workspaces/E14-challenge/backend/data/raw/{depto}/{muni}/{zona}/{puesto}/`

---

## 📁 Estructura de Carpetas

Antes de descargar, crea la estructura:

```
backend/data/raw/
├── 01/                    (Antioquia)
│   ├── 001/               (Medellín)
│   │   ├── 001/           (Zona 001)
│   │   │   ├── 01/        (Puesto 01)
│   │   │   │   ├── 001.pdf
│   │   │   │   ├── 002.pdf
│   │   │   │   └── ...
│   │   │   └── 02/        (Puesto 02)
│   │   └── 002/           (Zona 002)
│   └── 002/               (Bello)
│
├── 15/                    (Cundinamarca)
│   ├── 001/               (Bogotá)
│   └── ...
└── ...
```

**Puedes crearlas manualmente** o **ejecutar el script helper**:
```bash
# Script para crear estructura
mkdir -p backend/data/raw/{01,15,31}/{001}/{001}/{01}
```

---

## 🔄 Paso 4: Registrar PDFs en Backend

Una vez hayas descargado y colocado los PDFs en la estructura correcta:

```bash
cd /workspaces/E14-challenge/backend
python3 scripts/register_downloaded_pdfs.py
```

Este script:
1. 🔍 Busca todos los PDFs en `backend/data/raw/`
2. 📝 Extrae ubicación desde la ruta
3. 💾 Registra en la BD
4. 📊 Muestra resumen

---

## 💡 Alternativa: Usar Interfaz Web

**Después** de registrar con el script anterior, puedes usar la interfaz web para agregar más:

1. Abre: http://127.0.0.1:8000/
2. Arrasta un PDF o selecciona uno
3. Ingresa los códigos de ubicación
4. Haz clic "Cargar Formulario"

---

## 📊 Códigos de Departamento

Usa estos códigos al descargar:

| Código | Departamento | Código | Departamento |
|--------|--------------|--------|--------------|
| 01 | Antioquia | 19 | Huila |
| 03 | Atlántico | 21 | Magdalena |
| 05 | Bolívar | 23 | Nariño |
| 07 | Boyacá | 24 | Risaralda |
| 09 | Caldas | 25 | N. Santander |
| 11 | Cauca | 26 | Quindío |
| 12 | Cesar | 27 | Santander |
| 13 | Córdoba | 28 | Sucre |
| 15 | Cundinamarca | 29 | Tolima |
| 16 | Bogotá D.C. | 31 | Valle |
| 17 | Chocó | 40 | Arauca |
| 52 | Meta | 64 | Putumayo |

---

## 🚀 Flujo Completo

```
Portal Registraduría
        ↓
   Descargar PDF
        ↓
Renombrar: 001.pdf
        ↓
Colocar en carpeta:
backend/data/raw/{depto}/{muni}/{zona}/{puesto}/
        ↓
Ejecutar script registro:
python scripts/register_downloaded_pdfs.py
        ↓
BD actualizada ✅
        ↓
Frontend puede visualizar
```

---

## ⚠️ Posibles Problemas

### Portal muy lento
- **Solución**: Usa navegador en modo incógnito
- **Alternativa**: Intenta en horas de menor tráfico

### Botón de descarga no funciona
- **Solución**: Busca el logo de PDF en la fila
- **Alternativa**: Haz clic derecho → "Guardar como..."

### Error "Departamento no existe"
- **Solución**: Verifica el código del departamento
- **Nota**: Algunos departamentos pueden no tener datos

### PDF corrupto
- **Solución**: Descárgalo de nuevo
- **Verificación**: Abre el PDF en tu visor antes de copiarlo

---

## 📝 Checklist

- [ ] Portal accesible y funciona
- [ ] Seleccioné departamento y municipio
- [ ] Descargué al menos 1 PDF
- [ ] Renombré el PDF correctamente
- [ ] Copié el PDF a la carpeta correcta
- [ ] Ejecuté el script de registro
- [ ] El registro fue exitoso (sin errores)
- [ ] La BD ahora muestra los PDFs (`GET /pdfs`)

---

## 🎯 Próximos Pasos

Una vez registres los PDFs:

1. **Frontend React** - Visualizar PDFs cargados
2. **Integración IA** - Procesar con Gemini
3. **Dashboard** - Mostrar estadísticas
4. **Anomalías** - Detectar inconsistencias

---

**¡Listo!** Si todo funciona, el backend estará procesando tus PDFs reales. 🎉
