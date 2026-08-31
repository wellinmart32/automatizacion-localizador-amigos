import os
import sys
import json
import configparser


def _base_dir():
    """Devuelve la carpeta base del proyecto, ya sea ejecutando como script o como .exe compilado"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def leer_config_global():
    """
    Lee config_global.txt y devuelve un diccionario con la configuración del sistema

    Returns:
        dict: Configuración con valores por defecto si el archivo no existe
    """
    archivo_config = os.path.join(_base_dir(), "config_global.txt")

    config = configparser.RawConfigParser(delimiters=('=',))

    valores_por_defecto = {
        'navegador': 'firefox',
        'carpeta_perfil_custom': 'perfiles/localizador_amigos',
        'tiempo_espera_busqueda_segundos': '5',
        'tiempo_minimo_entre_envios_segundos': '10',
        'carpeta_contactos': 'contactos.json',
        'carpeta_mensajes': 'mensajes'
    }

    if not os.path.exists(archivo_config):
        print(f"⚠️  No se encontró config_global.txt, usando valores por defecto")
        return valores_por_defecto

    config.read(archivo_config, encoding='utf-8')

    resultado = valores_por_defecto.copy()

    if config.has_section('NAVEGADOR'):
        resultado['navegador'] = config.get('NAVEGADOR', 'navegador', fallback=resultado['navegador'])
        resultado['carpeta_perfil_custom'] = config.get('NAVEGADOR', 'carpeta_perfil_custom', fallback=resultado['carpeta_perfil_custom'])

    if config.has_section('BUSQUEDA'):
        resultado['tiempo_espera_busqueda_segundos'] = config.get('BUSQUEDA', 'tiempo_espera_busqueda_segundos', fallback=resultado['tiempo_espera_busqueda_segundos'])

    if config.has_section('LIMITES'):
        resultado['tiempo_minimo_entre_envios_segundos'] = config.get('LIMITES', 'tiempo_minimo_entre_envios_segundos', fallback=resultado['tiempo_minimo_entre_envios_segundos'])

    return resultado


def leer_contactos():
    """
    Lee contactos.json y devuelve la lista de contactos

    Returns:
        list: Lista de diccionarios con 'nombre' y 'mensaje', o lista vacía si no existe
    """
    config = leer_config_global()
    archivo_contactos = os.path.join(_base_dir(), config['carpeta_contactos'])

    if not os.path.exists(archivo_contactos):
        print(f"⚠️  No se encontró {config['carpeta_contactos']}")
        return []

    try:
        with open(archivo_contactos, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return datos.get('contactos', [])
    except Exception as e:
        print(f"❌ Error leyendo contactos.json: {e}")
        return []


def obtener_ruta_mensaje(nombre_archivo):
    """
    Arma la ruta completa a un archivo de mensaje dentro de la carpeta mensajes/

    Args:
        nombre_archivo: nombre del archivo .txt (ej. 'mensaje-001.txt')

    Returns:
        str: ruta completa al archivo
    """
    config = leer_config_global()
    return os.path.join(_base_dir(), config['carpeta_mensajes'], nombre_archivo)


def leer_mensaje(nombre_archivo):
    """
    Devuelve el texto de un mensaje específico

    Args:
        nombre_archivo: nombre del archivo .txt (ej. 'mensaje-001.txt')

    Returns:
        str: contenido del mensaje, o cadena vacía si no existe
    """
    ruta = obtener_ruta_mensaje(nombre_archivo)

    if not os.path.exists(ruta):
        print(f"⚠️  No se encontró el mensaje: {nombre_archivo}")
        return ""

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"❌ Error leyendo mensaje {nombre_archivo}: {e}")
        return ""


def obtener_estadisticas_contactos():
    """
    Obtiene estadísticas sobre los contactos configurados

    Returns:
        dict: Estadísticas de contactos
    """
    contactos = leer_contactos()
    con_mensaje = [c for c in contactos if c.get('mensaje')]

    return {
        'total_contactos': len(contactos),
        'con_mensaje_asignado': len(con_mensaje),
        'sin_mensaje_asignado': len(contactos) - len(con_mensaje)
    }


def obtener_carpeta_perfil_firefox():
    """
    Obtiene (o crea) la carpeta del perfil dedicado de Firefox para esta automatización

    Returns:
        str: ruta absoluta a la carpeta del perfil
    """
    config = leer_config_global()
    carpeta_perfil = os.path.join(_base_dir(), config['carpeta_perfil_custom'])

    if not os.path.exists(carpeta_perfil):
        os.makedirs(carpeta_perfil)
        print(f"✅ Carpeta de perfil creada: {carpeta_perfil}")

    return os.path.abspath(carpeta_perfil)


def obtener_primer_perfil_firefox():
    """
    Encuentra automáticamente el primer perfil de Firefox disponible (fallback)

    Returns:
        str: ruta al perfil de Firefox o None si no se encuentra
    """
    ruta_perfiles = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")

    if not os.path.exists(ruta_perfiles):
        print(f"⚠️  No se encontró la carpeta de perfiles de Firefox: {ruta_perfiles}")
        return None

    perfiles = [f for f in os.listdir(ruta_perfiles) if os.path.isdir(os.path.join(ruta_perfiles, f))]

    if not perfiles:
        print("⚠️  No se encontraron perfiles de Firefox")
        return None

    perfil_seleccionado = os.path.join(ruta_perfiles, perfiles[0])
    print(f"🦊 Perfil Firefox detectado: {perfiles[0]}")
    return perfil_seleccionado