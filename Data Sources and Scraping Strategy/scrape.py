# ========================================
# SCRAPER DE FORMULARIOS E-14
# Proyecto para auditar elecciones en Colombia
# ========================================
# Este script descargar PDFs de la Registraduría

# IMPORTACIONES
# ============
# Estas son las librerías que necesitamos para que funcione todo

import requests  # Para hacer peticiones HTTP (golpear la puerta del servidor)
import urllib3  # Para manejar conexiones HTTPS
from config import (  # Importar la configuración que guardamos en config.py
    DESCARGA_URL,  # La URL del servidor
    TOKEN_REGISTRO_PRESIDENCIAL,  # El token autenticación
    OUTPUT_DIR,  # La carpeta donde guardaremos PDFs
    TIMEOUT,  # Tiempo máximo de espera
    VERIFY_SSL,  # Si verificar certificado SSL o no
)

# DESACTIVAR ADVERTENCIAS DE SSL
# =============================
# Cuando usamos verify=False, Python nos avisa (es peligroso en producción)
# Esta línea dice: "Está bien, lo sabemos, calla"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# FUNCIÓN PARA DESCARGAR UN PDF
# =============================
# Una función es como una "receta" que repetimos varias veces

def descargar_pdf(nombre_archivo: str):
    """
    Descargar UN PDF de la Registraduría
    
    - Preparas tu "paquete" (token)
    - Se lo envías al servidor (POST)
    - El servidor te devuelve un PDF
    - Tú lo guardas en tu computadora
    
    Args:
        nombre_archivo (str): Nombre del archivo a guardar (ej: "formulario_001.pdf")
    """
    
    # PASO 1: PREPARAR LOS DATOS A ENVIAR
    # ===================================
    # Creamos un "diccionario" (como una maleta) con lo que queremos enviar
    
    datos_envio = {
        "data": TOKEN_REGISTRO_PRESIDENCIAL  # Metemos el token en la maleta
    }
    
    print(f"📤 Enviando petición al servidor...")
    print(f"   URL: {DESCARGA_URL}")
    print(f"   Token: {TOKEN_REGISTRO_PRESIDENCIAL[:20]}...*** (oculto por seguridad)")
    
    # PASO 2: HACER LA PETICIÓN POST
    # ==============================
    # Golpeamos la puerta del servidor y le pasamos nuestro token
    
    try:  # "Try" = intenta esto, pero si hay error, no te caigas
        response = requests.post(
            url=DESCARGA_URL,  # ¿A dónde enviar? → Al servidor
            data=datos_envio,  # ¿Qué enviar? → El token
            verify=VERIFY_SSL,  # ¿Verificar certificado? → No (solo desarrollo)
            timeout=TIMEOUT  # ¿Cuánto tiempo esperar? → 30 segundos
        )
        
        # PASO 3: VERIFICAR QUE LA RESPUESTA FUE EXITOSA
        # =============================================
        # El servidor responde con un "código de estado"
        # 200 = Éxito ✅
        # 404 = No encontrado ❌
        # 500 = Error del servidor ❌
        
        if response.status_code == 200:
            print(f"✅ Respuesta exitosa del servidor (código 200)")
        else:
            print(f"❌ Error del servidor (código {response.status_code})")
            return False  # Salir de la función sin guardar nada
        
        # PASO 4: GUARDAR EL PDF EN LA COMPUTADORA
        # ========================================
        # El servidor nos envió el contenido del PDF en "response.content"
        # Ahora lo guardamos en un archivo
        
        ruta_completa = OUTPUT_DIR / nombre_archivo  # Ruta completa del archivo
        
        with open(ruta_completa, "wb") as archivo:  # Abre el archivo en modo escritura binaria
            archivo.write(response.content)  # Escribe el contenido del PDF
        
        # PASO 5: CONFIRMAR QUE TODO SALIÓ BIEN
        # ===================================
        
        tamaño_kb = len(response.content) / 1024  # Convertir bytes a kilobytes
        print(f"✅ PDF descargado exitosamente")
        print(f"   Nombre: {nombre_archivo}")
        print(f"   Ubicación: {ruta_completa}")
        print(f"   Tamaño: {tamaño_kb:.2f} KB")
        print()
        
        return True  # Todo salió bien
    
    except requests.exceptions.Timeout:
        # El servidor tardó demasiado en responder
        print(f"❌ TIMEOUT: El servidor tardó más de {TIMEOUT} segundos en responder")
        return False
    
    except requests.exceptions.ConnectionError:
        # No pudimos conectarse al servidor (sin internet, URL mal, etc)
        print(f"❌ ERROR DE CONEXIÓN: No pudimos alcanzar el servidor")
        print(f"   Verifica: internet, URL, firewall")
        return False
    
    except Exception as e:
        # Cualquier otro error
        print(f"❌ ERROR INESPERADO: {str(e)}")
        return False


# FUNCIÓN PRINCIPAL
# =================
# Esta es la función que ejecuta TODO el programa

def main():
    """
    Función principal del scraper
    Aquí es donde empieza TODO
    """
    
    print("=" * 60)
    print("🚀 SCRAPER DE FORMULARIOS E-14")
    print("=" * 60)
    print()
    
    # PASO 1: MOSTRAR INFORMACIÓN
    print(f"📁 Carpeta de salida: {OUTPUT_DIR}")
    print(f"🌐 Servidor: {DESCARGA_URL}")
    print()
    
    # PASO 2: DESCARGAR EL PDF
    # Por ahora descargamos UNO, pero después haremos múltiples
    
    print("Descargando PDFs...")
    print("-" * 60)
    
    # Descargar el primer PDF
    exito = descargar_pdf("formulario_e14_001.pdf")
    
    # PASO 3: RESULTADO FINAL
    print("-" * 60)
    if exito:
        print("✅ Proceso completado exitosamente")
    else:
        print("❌ Hubo un error durante el proceso")
    
    print("=" * 60)


# PUNTO DE ENTRADA DEL PROGRAMA
# =============================
# "if __name__ == '__main__':" es una forma de decir:
# "Solo ejecuta esto si corren este archivo directamente"
# NO lo ejecuta si alguien lo importa desde otro archivo

if __name__ == "__main__":
    main()