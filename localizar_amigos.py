import time

from compartido.gestor_archivos import leer_config_global, leer_contactos, leer_mensaje, obtener_estadisticas_contactos, leer_historial_envios, agregar_url_a_historial
from localizadores.localizador_facebook import LocalizadorFacebook

# ── Colores ANSI ──────────────────────────────────────────────
V  = '\033[92m'   # verde
R  = '\033[91m'   # rojo
A  = '\033[93m'   # amarillo
C  = '\033[96m'   # cian
N  = '\033[1m'    # negrita
X  = '\033[0m'    # reset
# ─────────────────────────────────────────────────────────────


def main():
    print(f"{N}{'='*70}{X}")
    print(f"{N}          🔎 LOCALIZADOR DE AMIGOS - FACEBOOK{X}")
    print(f"{N}{'='*70}{X}\n")

    config = leer_config_global()
    contactos = leer_contactos()

    if not contactos:
        print(f"{R}❌ No hay contactos configurados en contactos.json{X}")
        return

    stats = obtener_estadisticas_contactos()
    print(f"{C}📊 Total de contactos: {stats['total_contactos']}{X}")
    print(f"{C}📊 Con mensaje asignado: {stats['con_mensaje_asignado']}{X}\n")

    contactos_validos = [c for c in contactos if c.get('mensaje')]
    if not contactos_validos:
        print(f"{R}❌ Ningún contacto tiene mensaje asignado{X}")
        return

    localizador = LocalizadorFacebook(config)
    localizador.iniciar_navegador()

    if not localizador.verificar_sesion():
        localizador.cerrar_navegador()
        return

    exitosos = []
    fallidos = []
    total_mensajes_enviados = 0
    total_mensajes_intentados = 0
    tiempo_espera = int(config.get('tiempo_minimo_entre_envios_segundos', 10))
    cantidad_resultados = int(config.get('cantidad_resultados_intentar', 1))
    urls_ya_enviadas = leer_historial_envios()

    for i, contacto in enumerate(contactos_validos):
        nombre = contacto['nombre']
        texto_mensaje = leer_mensaje(contacto['mensaje'])

        if not texto_mensaje:
            print(f"\n{A}⚠️  Mensaje vacío para '{nombre}', se omite{X}")
            fallidos.append(nombre)
            continue

        filtro_amistad = contacto.get('filtro_amistad', 'todos')
        evitar_duplicados = contacto.get('evitar_duplicados', False)
        ubicacion = contacto.get('ubicacion', '')

        enviados, encontrados, urls_enviadas_ahora = localizador.procesar_contacto(
            nombre, texto_mensaje, cantidad_resultados, filtro_amistad,
            evitar_duplicados, urls_ya_enviadas, ubicacion
        )
        total_mensajes_enviados += enviados
        total_mensajes_intentados += encontrados

        for url in urls_enviadas_ahora:
            agregar_url_a_historial(url)
            urls_ya_enviadas.append(url)

        if enviados > 0:
            exitosos.append(f"{nombre} ({enviados}/{encontrados})")
        else:
            fallidos.append(nombre)

        if i < len(contactos_validos) - 1:
            time.sleep(tiempo_espera)

    localizador.cerrar_navegador()

    print(f"\n{N}{'='*70}{X}")
    print(f"{N}                    📋 RESUMEN{X}")
    print(f"{N}{'='*70}{X}")
    print(f"{C}📨 Mensajes enviados: {total_mensajes_enviados}/{total_mensajes_intentados}{X}")
    print(f"{V}✅ Contactos con al menos 1 envío: {len(exitosos)}{X} {exitosos}")
    print(f"{R}❌ Contactos sin ningún envío: {len(fallidos)}{X} {fallidos}")
    print(f"{N}{'='*70}{X}")


if __name__ == "__main__":
    main()