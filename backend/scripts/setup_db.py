"""
setup_db.py - Inicializar la Base de Datos E14 Challenge

Este script CREA la base de datos la PRIMERA VEZ.

IMPORTANTE: Ejecutar SOLO UNA VEZ al principio del proyecto.
Si lo ejecutas de nuevo, sobrescribe las tablas (¡cuidado!).

¿Cómo ejecutar?
    cd backend
    python scripts/setup_db.py

¿Qué hace?
    1. Lee el schema (estructura de tablas) de src/database/schema.py
    2. Conecta a la BD (SQLite)
    3. Crea todas las tablas
    4. Verifica que todo está bien
"""

import sys
from pathlib import Path

# Agregar backend/ al path para importar nuestros módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar lo que necesitamos
from config import DATABASE_URL, DATABASE_PATH, DATA_DIR
from src.database.schema import create_all_tables, Base

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """
    Ejecuta la inicialización de la BD.
    """
    
    print("\n" + "="*70)
    print("🔧 INICIALIZANDO BASE DE DATOS E14 CHALLENGE")
    print("="*70 + "\n")
    
    # PASO 1: Verificar que existen las carpetas de datos
    print("📁 Verificando carpetas de datos...")
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Carpeta de datos lista: {DATA_DIR}\n")
    except Exception as e:
        print(f"   ❌ Error creando carpeta: {e}\n")
        return False
    
    # PASO 2: Crear la BD y todas las tablas
    print("🗄️  Creando base de datos...")
    print(f"   Ubicación: {DATABASE_PATH}")
    print(f"   URL: {DATABASE_URL}\n")
    
    try:
        # Esto llama a create_all_tables() de schema.py
        engine = create_all_tables(DATABASE_URL)
        print(f"   ✅ Base de datos creada exitosamente\n")
    except Exception as e:
        print(f"   ❌ Error creando BD: {e}\n")
        return False
    
    # PASO 3: Mostrar las tablas que se crearon
    print("📋 Tablas creadas:")
    for tabla in Base.metadata.tables.keys():
        # Obtener información sobre la tabla
        tabla_obj = Base.metadata.tables[tabla]
        columnas = len(tabla_obj.columns)
        print(f"   ✅ {tabla:20} ({columnas} columnas)")
    print()
    
    # PASO 4: Mostrar estructura de cada tabla
    print("🔍 Estructura de tablas:\n")
    for tabla_nombre, tabla_obj in Base.metadata.tables.items():
        print(f"   📊 {tabla_nombre.upper()}")
        for columna in tabla_obj.columns:
            # Información de la columna
            tipo = str(columna.type)
            nullable = "nullable" if columna.nullable else "NOT NULL"
            pk = "PRIMARY KEY" if columna.primary_key else ""
            
            # Combinar información
            info_partes = [nullable]
            if pk:
                info_partes.append(pk)
            info = " | ".join(info_partes)
            
            print(f"      • {columna.name:25} {tipo:15} {info}")
        print()
    
    # PASO 5: Resumen final
    print("="*70)
    print("✅ INICIALIZACIÓN COMPLETADA")
    print("="*70)
    print()
    print("📝 Próximos pasos:")
    print("   1. Llenar la BD con datos de prueba:")
    print("      python scripts/seed_data.py")
    print()
    print("   2. Crear un script para procesar PDFs")
    print()
    
    return True


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    """
    Se ejecuta cuando haces: python scripts/setup_db.py
    """
    
    try:
        exito = main()
        
        # Salir con código de error si falla
        sys.exit(0 if exito else 1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)