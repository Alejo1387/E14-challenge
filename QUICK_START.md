# ⚡ Quick Start - E14 Challenge (1 Página)

## 🚀 Empezar Ahora (2 comandos)

```bash
cd /workspaces/E14-challenge/backend && python3 main.py
```

**Luego abre en navegador:**
```
http://127.0.0.1:8000
```

---

## 📍 Lo que ves

| URL | Qué Es | Acciones Posibles |
|-----|--------|------------------|
| http://127.0.0.1:8000 | 📄 Formulario Web | Upload PDF + ver lista |
| http://127.0.0.1:8000/docs | 📚 API Docs | Testing endpoints |
| http://127.0.0.1:8000/pdfs | 📊 JSON Lista | GET lista PDFs |

---

## 🧪 Probar Upload (5 minutos)

### Vía Interfaz Web
1. Ve a http://127.0.0.1:8000/
2. Arrastra un PDF (o clic para seleccionar)
3. Llena códigos de ubicación:
   - **Depto**: `01` (Antioquia)
   - **Municipio**: `001` (Medellín)
   - **Zona**: `001`
   - **Puesto**: `01`
   - **Mesa**: `001`
4. Haz clic "Cargar Formulario"
5. ✅ Verás resultado con Form ID

### Vía Terminal (cURL)
```bash
# Crea un PDF de prueba
echo "%PDF-1.4" > test.pdf && dd if=/dev/urandom bs=1024 count=50 >> test.pdf

# Sube
curl -X POST http://127.0.0.1:8000/upload-pdf \
  -F "file=@test.pdf" \
  -F "dept_code=01" \
  -F "muni_code=001" \
  -F "zone_code=001" \
  -F "station_code=01" \
  -F "table_number=001"
```

---

## 📊 Estado Actual

✅ 30 PDFs generados y registrados  
✅ Servidor FastAPI activo  
✅ Interfaz web funcional  
✅ Base de datos completa (34 depto, 1200+ municipios)  

---

## 📚 Documentación (Por Importancia)

1. **RESUMEN_EJECUTIVO.md** ← Empieza aquí
2. **README_IMPLEMENTACION.md** ← Guía completa
3. **GUIA_API_ENDPOINTS.md** ← Referencia API
4. **ARQUITECTURA_SISTEMA.md** ← Diseño técnico
5. **INDICE_ARCHIVOS.md** ← Dónde encontrar qué

---

## 🐍 Scripts Útiles

```bash
# Ver los 30 PDFs en BD
curl http://127.0.0.1:8000/pdfs | jq '.total'

# Registrar PDFs nuevos de disco
cd backend && python3 scripts/register_downloaded_pdfs.py

# Reiniciar BD (⚠️ Borra datos)
python3 scripts/setup_db.py
python3 scripts/seed_data.py
```

---

## 🚨 Problemas Comunes

| Problema | Solución |
|----------|----------|
| "Port already in use" | `kill -9 $(lsof -t -i :8000)` |
| "Module not found" | `pip install -r requirements.txt` |
| "BD not found" | `python3 scripts/setup_db.py` && `seed_data.py` |
| "Upload fails" | Verifica código depto/municipio existe |

---

## 📂 Archivos Clave

```
backend/main.py              ← Servidor (ejecutar esto)
backend/static/upload.html   ← Interfaz web
backend/data/raw/            ← 30 PDFs almacenados
backend/data/e14_challenge.db ← Base de datos
```

---

## 🎯 Próximo Paso

**Opción A**: Descargar PDFs reales desde Registraduría  
→ Ver: `GUIA_DESCARGAR_PDFS_REALES.md`

**Opción B**: Construir Frontend React  
→ (Tu compañero se encarga)

**Opción C**: Integrar IA (Gemini)  
→ (Después de frontend)

---

## 💾 Códigos de Prueba (Copy-Paste)

```
Antioquia:       01-001-001-01-001
Atlántico:       03-001-001-01-001
Bolívar:         05-001-001-01-001
Cundinamarca:    15-001-001-01-001
Bogotá:          15-001-001-01-001
Valle:           31-001-001-01-001
```

---

## 🔗 URLs Útiles

| URL | Propósito |
|-----|----------|
| http://127.0.0.1:8000/ | Interfaz de upload |
| http://127.0.0.1:8000/docs | Swagger API |
| http://127.0.0.1:8000/pdfs | Lista JSON |
| http://127.0.0.1:8000/health | Status |

---

**Documentación completa**: Ver `RESUMEN_EJECUTIVO.md`  
**¿Necesitas ayuda?**: Ver `INDICE_ARCHIVOS.md`  
**Status**: ✅ MVP Activo
