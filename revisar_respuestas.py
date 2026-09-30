from compartido.gestor_archivos import leer_config_global, leer_historial_envios
from localizadores.localizador_facebook import LocalizadorFacebook
from localizadores.revisor_respuestas import RevisorRespuestas

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
    print(f"{N}          📬 REVISOR DE RESPUESTAS - FACEBOOK{X}")
    print(f"{N}{'='*70}{X}\n")

    config = leer_config_global()
    modo = config.get('modo_revisor_respuestas', 'no_vistos')
    cantidad_maxima = int(config.get('cantidad_maxima_revisor', 10))

    historial = leer_historial_envios()
    if not historial:
        print(f"{R}❌ No hay historial de envíos. Corre primero localizar_amigos.py{X}")
        return

    nombres_historial = [item['nombre'] for item in historial if item.get('nombre')]
    if not nombres_historial:
        print(f"{R}❌ El historial no tiene nombres registrados (formato antiguo){X}")
        return

    print(f"{C}📊 Personas en el historial: {len(nombres_historial)}{X}")
    print(f"{C}📊 Modo: {modo} | Máximo a revisar: {cantidad_maxima}{X}\n")

    localizador = LocalizadorFacebook(config)
    localizador.iniciar_navegador()

    if not localizador.verificar_sesion():
        localizador.cerrar_navegador()
        return

    revisor = RevisorRespuestas(localizador.driver)
    chats = revisor.buscar_respuestas(nombres_historial, modo=modo, cantidad_maxima=cantidad_maxima)

    if not chats:
        print(f"{A}⚠️  No se encontraron respuestas nuevas{X}")
        localizador.cerrar_navegador()
        return

    print(f"\n{N}{'='*70}{X}")
    print(f"{N}                📋 TE RESPONDIERON{X}")
    print(f"{N}{'='*70}{X}")
    for i, chat in enumerate(chats):
        print(f"{V}{i + 1}. {chat['nombre']}{X}")
    print(f"{N}{'='*70}{X}\n")

    revisor.recorrer_chats(chats)

    localizador.cerrar_navegador()

    print(f"\n{N}{'='*70}{X}")
    print(f"{V}✅ Revisión completada{X}")
    print(f"{N}{'='*70}{X}")


if __name__ == "__main__":
    main()