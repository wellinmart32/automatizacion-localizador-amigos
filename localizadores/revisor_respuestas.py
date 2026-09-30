import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# ── Colores ANSI ──────────────────────────────────────────────
V  = '\033[92m'   # verde
R  = '\033[91m'   # rojo
A  = '\033[93m'   # amarillo
C  = '\033[96m'   # cian
N  = '\033[1m'    # negrita
X  = '\033[0m'    # reset
# ─────────────────────────────────────────────────────────────


class RevisorRespuestas:
    """Revisa Messenger buscando respuestas de personas contactadas desde LocalizadorAmigos"""

    def __init__(self, driver):
        self.driver = driver

    def _extraer_chats(self):
        """Lee la lista de chats visible en Messenger y extrae nombre, link y estado de cada uno"""
        xpath_filas = "//div[@role='row']"
        filas = self.driver.find_elements(By.XPATH, xpath_filas)

        chats = []
        for fila in filas:
            try:
                link = fila.find_element(By.XPATH, ".//a[contains(@href, '/messages/')]")
                href = link.get_attribute('href')
            except NoSuchElementException:
                continue

            if not href:
                continue

            try:
                boton_opciones = fila.find_element(By.XPATH, ".//div[starts-with(@aria-label, 'Más opciones para')]")
                nombre = boton_opciones.get_attribute('aria-label').replace('Más opciones para', '').strip()
            except NoSuchElementException:
                continue

            no_leido = len(fila.find_elements(By.XPATH, ".//div[contains(text(), 'Mensaje no leído')]")) > 0

            texto_ultimo_mensaje = ""
            try:
                spans_mensaje = fila.find_elements(By.XPATH, ".//abbr/ancestor::div[3]/preceding-sibling::span[1]//span")
                if spans_mensaje:
                    texto_ultimo_mensaje = spans_mensaje[0].text
            except Exception:
                pass

            me_respondio = texto_ultimo_mensaje and not texto_ultimo_mensaje.startswith('Tú:')

            chats.append({
                'nombre': nombre,
                'href': href,
                'no_leido': no_leido,
                'me_respondio': me_respondio,
                'texto': texto_ultimo_mensaje
            })

        return chats

    def buscar_respuestas(self, nombres_historial, modo='no_vistos', cantidad_maxima=10):
        """
        Busca chats de gente en el historial que te respondió

        Args:
            nombres_historial: lista de nombres a los que se les envió mensaje desde LocalizadorAmigos
            modo: 'todos' o 'no_vistos'
            cantidad_maxima: tope de resultados a devolver

        Returns:
            list: chats que califican, con nombre y href
        """
        print(f"\n{N}📬 Revisando Messenger...{X}")
        self.driver.get("https://www.facebook.com/messages/t/")
        time.sleep(4)

        chats = self._extraer_chats()
        nombres_historial_lower = [n.lower() for n in nombres_historial]

        candidatos = []
        for chat in chats:
            if chat['nombre'].lower() not in nombres_historial_lower:
                continue
            if not chat['me_respondio']:
                continue
            if modo == 'no_vistos' and not chat['no_leido']:
                continue
            candidatos.append(chat)

        return candidatos[:cantidad_maxima]

    def abrir_chat(self, href):
        """Navega directo a un chat específico"""
        self.driver.get(href)
        time.sleep(3)

    def recorrer_chats(self, chats):
        """Abre cada chat uno por uno, esperando Enter en consola para avanzar al siguiente"""
        for i, chat in enumerate(chats):
            print(f"\n{N}➡️  Chat {i + 1}/{len(chats)}: {chat['nombre']}{X}")
            self.abrir_chat(chat['href'])
            input(f"   {A}Presiona Enter cuando termines de leer/responder para continuar...{X}")