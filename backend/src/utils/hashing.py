"""
hashing.py - Calcular SHA-256 de archivos

SHA-256 es una función que toma un archivo y produce un código único.
Si el archivo cambia aunque sea un bit, el SHA-256 es completamente diferente.

¿Para qué?
- Para verificar que un PDF no se dañó
- Para saber si dos archivos son idénticos
"""

import hashlib
from pathlib import Path
from typing import Optional

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def calcular_sha256(ruta_archivo: str | Path) -> str:
    """
    Calcula el SHA-256 de un archivo.
    
    Args:
        ruta_archivo: Ruta al archivo (puede ser string o Path)
        
    Returns:
        String de 64 caracteres con el hash SHA-256
        
    Example:
        >>> hash_pdf = calcular_sha256("backend/data/raw/05_Antioquia/001_Medellin/5036317.pdf")
        >>> print(hash_pdf)
        'a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9...'
    """
    
    # Convertir a Path si es string
    ruta = Path(ruta_archivo)
    
    # Verificar que el archivo existe
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
    
    # Verificar que es un archivo (no una carpeta)
    if not ruta.is_file():
        raise ValueError(f"No es un archivo: {ruta}")
    
    # Crear un objeto "hasher" de SHA-256
    hasher = hashlib.sha256()
    
    # Leer el archivo en bloques (para no usar mucha memoria con archivos grandes)
    # Tamaño del bloque: 65536 bytes (64 KB)
    TAMAÑO_BLOQUE = 65536
    
    with open(ruta, "rb") as archivo:  # "rb" = read binary (leer en modo binario)
        # Mientras haya datos en el archivo
        while True:
            # Leer un bloque
            bloque = archivo.read(TAMAÑO_BLOQUE)
            
            # Si llegamos al final (bloque vacío), salir del loop
            if not bloque:
                break
            
            # Agregar el bloque al hasher
            hasher.update(bloque)
    
    # Devolver el hash como string hexadecimal (64 caracteres)
    return hasher.hexdigest()


# ============================================================================
# FUNCIÓN AUXILIAR: Verificar si un hash es válido
# ============================================================================

def es_hash_valido(hash_string: str) -> bool:
    """
    Verifica que un string sea un hash SHA-256 válido.
    
    SHA-256 siempre produce 64 caracteres hexadecimales.
    
    Args:
        hash_string: El hash a validar
        
    Returns:
        True si es válido, False si no
        
    Example:
        >>> es_hash_valido("a3c5f7e2d9b4c8f1e2d3a4b5c6d7e8f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4")
        True
        >>> es_hash_valido("no_es_hash")
        False
    """
    # Debe tener exactamente 64 caracteres
    if len(hash_string) != 64:
        return False
    
    # Todos deben ser caracteres hexadecimales (0-9, a-f)
    try:
        int(hash_string, 16)  # Intenta convertir como hexadecimal
        return True
    except ValueError:
        return False


# ============================================================================
# PRUEBAS
# ============================================================================

if __name__ == "__main__":
    """
    Código para probar si todo funciona.
    Ejecuta: python backend/src/utils/hashing.py
    """
    
    from pathlib import Path
    import tempfile
    
    print("\n" + "="*60)
    print("🧪 PRUEBAS DE HASHING")
    print("="*60 + "\n")
    
    # Crear un archivo temporal para la prueba
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Este es un archivo de prueba para hashing")
        temp_path = f.name
    
    try:
        # Calcular hash del archivo
        hash_resultado = calcular_sha256(temp_path)
        print(f"✅ Hash calculado: {hash_resultado}")
        
        # Verificar que es válido
        if es_hash_valido(hash_resultado):
            print(f"✅ Hash es válido (64 caracteres hexadecimales)")
        else:
            print(f"❌ Hash es inválido")
        
        # Calcular hash del mismo archivo otra vez
        hash_nuevamente = calcular_sha256(temp_path)
        
        # Debe ser idéntico
        if hash_resultado == hash_nuevamente:
            print(f"✅ Hash es consistente (mismo archivo = mismo hash)")
        else:
            print(f"❌ Hash cambió (algo está mal)")
    
    finally:
        # Limpiar: eliminar archivo temporal
        Path(temp_path).unlink()
    
    print("\n" + "="*60)