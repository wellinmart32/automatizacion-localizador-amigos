import time

from compartido.gestor_archivos import leer_config_global, leer_contactos, leer_mensaje, obtener_estadisticas_contactos
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
    tiempo_espera = int(config.get('tiempo_minimo_entre_envios_segundos', 10))

    for i, contacto in enumerate(contactos_validos):
        nombre = contacto['nombre']
        texto_mensaje = leer_mensaje(contacto['mensaje'])

        if not texto_mensaje:
            print(f"\n{A}⚠️  Mensaje vacío para '{nombre}', se omite{X}")
            fallidos.append(nombre)
            continue

        resultado = localizador.procesar_contacto(nombre, texto_mensaje)

        if resultado:
            exitosos.append(nombre)
        else:
            fallidos.append(nombre)

        if i < len(contactos_validos) - 1:
            time.sleep(tiempo_espera)

    localizador.cerrar_navegador()

    print(f"\n{N}{'='*70}{X}")
    print(f"{N}                    📋 RESUMEN{X}")
    print(f"{N}{'='*70}{X}")
    print(f"{V}✅ Exitosos: {len(exitosos)}{X} {exitosos}")
    print(f"{R}❌ Fallidos: {len(fallidos)}{X} {fallidos}")
    print(f"{N}{'='*70}{X}")


if __name__ == "__main__":
    main()