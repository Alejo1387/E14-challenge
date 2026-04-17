"""
connection.py - Conexión a la Base de Datos

Este módulo proporciona funciones para conectar a la BD.

¿Por qué?
    En lugar de repetir el código de conexión en 10 scripts,
    todos dicen: "Dame una conexión" y listo.

¿Cómo usarlo?
    from src.database.connection import get_session, get_engine
    
    # Opción 1: Usar sesión (recomendado para consultas simples)
    session = get_session()
    usuarios = session.query(User).all()
    
    # Opción 2: Usar engine (para operaciones más complejas)
    engine = get_engine()
"""

import sys
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

# Importar lo que necesitamos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DATABASE_URL
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

# ============================================================================
# VARIABLES GLOBALES (Se crean UNA SOLA VEZ)
# ============================================================================

_engine = None
_SessionLocal = None

# ============================================================================
# FUNCIÓN 1: Obtener el Engine
# ============================================================================

def get_engine():
    """
    Obtiene (o crea) la conexión Engine a la BD.
    
    El Engine es el "intermediario" entre Python y la BD.
    Se crea UNA SOLA VEZ y se reutiliza.
    
    Returns:
        sqlalchemy.engine.Engine
    
    Ejemplo:
        >>> engine = get_engine()
        >>> print(engine)
        Engine(sqlite:///backend/data/e14_challenge.db)
    """
    
    global _engine
    
    # Si ya existe, devolverlo
    if _engine is not None:
        return _engine
    
    # Si no existe, crearlo
    print(f"🔗 Creando conexión a: {DATABASE_URL}")
    _engine = create_engine(
        DATABASE_URL,
        echo=False,  # Si es True, muestra todas las queries SQL
        # SQLite específico:
        connect_args={"check_same_thread": False}  # Permite múltiples threads
    )
    
    # IMPORTANTE: Habilitar foreign keys en SQLite
    # (SQLite no las valida por defecto)
    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Ejecuta 'PRAGMA foreign_keys=ON' cada vez que se conecta"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    print("   ✅ Engine creado\n")
    
    return _engine


# ============================================================================
# FUNCIÓN 2: Obtener la Sesión
# ============================================================================

def get_session() -> Session:
    """
    Obtiene una nueva sesión a la BD.
    
    La sesión es como una "conversación" con la BD.
    Cada vez que necesitas consultar/guardar datos, usas una sesión.
    
    IMPORTANTE: Debes cerrarla cuando termines (o usar context manager).
    
    Returns:
        sqlalchemy.orm.Session
    
    Ejemplo (INCORRECTO):
        >>> session = get_session()
        >>> usuarios = session.query(User).all()
        # OLVIDAS cerrar session ← MALO
    
    Ejemplo (CORRECTO):
        >>> session = get_session()
        >>> try:
        ...     usuarios = session.query(User).all()
        ... finally:
        ...     session.close()
    
    Mejor aún (usa with):
        >>> with get_session() as session:
        ...     usuarios = session.query(User).all()
        # Se cierra automáticamente
    """
    
    global _SessionLocal
    
    # Crear la "fábrica de sesiones" si no existe
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    
    # Devolver una nueva sesión
    return _SessionLocal()


# ============================================================================
# FUNCIÓN 3: Context Manager (for statement with)
# ============================================================================

@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager para usar sesión de forma segura.
    
    Esto permite usar la sesión con 'with' para asegurar que se cierre.
    
    Returns:
        Generator[Session, None, None]
    
    Ejemplo:
        >>> from src.database.connection import session_scope
        >>> 
        >>> with session_scope() as session:
        ...     usuario = session.query(User).first()
        ...     print(usuario.nombre)
        # La sesión se cierra automáticamente
    
    O en una función:
        >>> def obtener_usuarios():
        ...     with session_scope() as session:
        ...         return session.query(User).all()
    """
    
    session = get_session()
    
    try:
        yield session
    finally:
        session.close()


# ============================================================================
# FUNCIÓN 4: Verificar conexión
# ============================================================================

def verificar_conexion() -> bool:
    """
    Verifica que la BD está accesible.
    
    Intenta hacer una consulta simple. Si funciona, la conexión está bien.
    
    Returns:
        bool: True si la conexión es buena, False si hay error
    
    Ejemplo:
        >>> if verificar_conexion():
        ...     print("✅ BD accesible")
        ... else:
        ...     print("❌ BD inaccesible")
    """
    
    try:
        with session_scope() as session:
            # Hacer una consulta simple
            session.execute(text("SELECT 1"))
        
        return True
    
    except Exception as e:
        print(f"❌ Error verificando conexión: {e}")
        return False


# ============================================================================
# PRUEBAS
# ============================================================================

if __name__ == "__main__":
    """
    Para probar este módulo:
    python backend/src/database/connection.py
    """
    
    print("\n" + "="*60)
    print("🧪 PRUEBAS DE CONEXIÓN")
    print("="*60 + "\n")
    
    # PRUEBA 1: Obtener engine
    print("Prueba 1️⃣: Obtener engine...")
    engine = get_engine()
    print(f"   ✅ Engine: {engine}\n")
    
    # PRUEBA 2: Obtener sesión
    print("Prueba 2️⃣: Obtener sesión...")
    session = get_session()
    print(f"   ✅ Sesión: {session}")
    session.close()
    print(f"   ✅ Sesión cerrada\n")
    
    # PRUEBA 3: Usar context manager
    print("Prueba 3️⃣: Usar context manager...")
    with session_scope() as session:
        print(f"   ✅ Sesión abierta: {session}")
    print(f"   ✅ Sesión cerrada automáticamente\n")
    
    # PRUEBA 4: Verificar conexión
    print("Prueba 4️⃣: Verificar conexión...")
    if verificar_conexion():
        print("   ✅ Conexión verificada\n")
    else:
        print("   ❌ Conexión fallida\n")
    
    # PRUEBA 5: Hacer una consulta real
    print("Prueba 5️⃣: Hacer consulta a la BD...")
    try:
        from src.database.schema import Department
        
        with session_scope() as session:
            # Contar departamentos
            cantidad = session.query(Department).count()
            print(f"   ✅ Departamentos en BD: {cantidad}\n")
            
            # Mostrar algunos
            print("   Primeros 5 departamentos:")
            for dept in session.query(Department).limit(5):
                print(f"      • {dept.code}: {dept.name}")
            print()
    
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("="*60 + "\n")