import os
import sys
import time
import pyperclip

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ── Colores ANSI ──────────────────────────────────────────────
V  = '\033[92m'   # verde
R  = '\033[91m'   # rojo
A  = '\033[93m'   # amarillo
C  = '\033[96m'   # cian
N  = '\033[1m'    # negrita
X  = '\033[0m'    # reset
# ─────────────────────────────────────────────────────────────


class LocalizadorFacebook:
    """Busca personas por nombre en Facebook y envía un mensaje al primer resultado"""

    def __init__(self, config):
        self.config = config
        self.driver = None
        self.wait = None

    # ==================== NAVEGADOR ====================

    def iniciar_navegador(self):
        """Inicia Firefox con el perfil dedicado de LocalizadorAmigos"""
        print(f"{N}🌐 Iniciando Firefox...{X}")

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        options = FirefoxOptions()

        perfil_path = os.path.join(base_dir, self.config.get('carpeta_perfil_custom', 'perfiles/localizador_amigos'))
        os.makedirs(perfil_path, exist_ok=True)
        options.add_argument('-profile')
        options.add_argument(perfil_path)
        print(f"   ✓ Perfil Firefox: {os.path.basename(perfil_path)}")

        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("dom.push.enabled", False)

        self.driver = webdriver.Firefox(options=options)
        self.wait = WebDriverWait(self.driver, 20)
        self.driver.maximize_window()

        print(f"   {V}✅ Navegador iniciado{X}")

    def verificar_sesion(self):
        """Abre Facebook y verifica si hay una sesión activa"""
        print(f"\n{N}🔐 Verificando sesión de Facebook...{X}")
        self.driver.get("https://www.facebook.com")
        time.sleep(4)

        try:
            self.driver.find_element(By.XPATH, "//div[@aria-label='Buscar en Facebook' or @aria-label='Search Facebook']")
            print(f"   {V}✅ Ya tienes sesión activa en Facebook{X}")
            return True
        except NoSuchElementException:
            print(f"   {A}⚠️  No se detectó sesión activa. Inicia sesión manualmente en la ventana abierta.{X}")
            print(f"   {A}   Esperando hasta 60s...{X}")
            for _ in range(12):
                time.sleep(5)
                try:
                    self.driver.find_element(By.XPATH, "//div[@aria-label='Buscar en Facebook' or @aria-label='Search Facebook']")
                    print(f"   {V}✅ Sesión detectada{X}")
                    return True
                except NoSuchElementException:
                    continue
            print(f"   {R}❌ No se detectó inicio de sesión a tiempo{X}")
            return False

    # ==================== BÚSQUEDA ====================

    def _encontrar_barra_busqueda(self, timeout=10):
        """Selector en cascada para la barra de búsqueda de Facebook"""
        selectores = [
            "//div[@aria-label='Buscar en Facebook']",
            "//div[@aria-label='Search Facebook']",
            "//input[@aria-label='Buscar en Facebook']",
            "//input[@aria-label='Search Facebook']",
            "//input[@placeholder='Buscar en Facebook']",
        ]
        for selector in selectores:
            try:
                elemento = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                return elemento
            except TimeoutException:
                continue
        return None

    def buscar_persona(self, nombre):
        """Escribe el nombre en la barra de búsqueda de Facebook"""
        print(f"\n🔍 Buscando: '{nombre}'")

        barra_busqueda = self._encontrar_barra_busqueda()
        if not barra_busqueda:
            print(f"   {R}❌ No se encontró la barra de búsqueda{X}")
            return False

        barra_busqueda.click()
        time.sleep(0.5)
        barra_busqueda.send_keys(Keys.CONTROL + "a")
        barra_busqueda.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)

        for caracter in nombre:
            barra_busqueda.send_keys(caracter)
            time.sleep(0.05)

        time.sleep(float(self.config.get('tiempo_espera_busqueda_segundos', 5)))
        return True

    def _encontrar_primer_resultado(self, nombre):
        """Busca el primer resultado de tipo persona en el desplegable de búsqueda"""
        selectores = [
            f"//span[text()='{nombre}']/ancestor::a[1]",
            f"//span[contains(text(), '{nombre}')]/ancestor::a[1]",
            "//div[@role='listbox']//a[@role='link'][1]",
        ]
        for selector in selectores:
            try:
                elemento = self.driver.find_element(By.XPATH, selector)
                return elemento
            except NoSuchElementException:
                continue
        return None

    def abrir_perfil(self, nombre):
        """Hace clic en el primer resultado de búsqueda para abrir su perfil"""
        resultado = self._encontrar_primer_resultado(nombre)
        if not resultado:
            print(f"   {R}❌ No se encontró ningún resultado para '{nombre}'{X}")
            return False

        resultado.click()
        time.sleep(4)
        print(f"   {V}✅ Perfil abierto{X}")
        return True

    # ==================== MENSAJE ====================

    def _encontrar_boton_mensaje(self, timeout=10):
        """Selector en cascada para el botón 'Enviar mensaje' del perfil"""
        selectores = [
            "//div[@aria-label='Enviar mensaje']",
            "//div[@aria-label='Message']",
            "//span[text()='Enviar mensaje']/ancestor::div[@role='button'][1]",
            "//span[text()='Message']/ancestor::div[@role='button'][1]",
        ]
        for selector in selectores:
            try:
                elemento = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                return elemento
            except TimeoutException:
                continue
        return None

    def _encontrar_campo_mensaje(self, timeout=10):
        """Selector en cascada para el campo de texto del chat de Messenger"""
        selectores = [
            "//div[@aria-label='Mensaje' and @role='textbox']",
            "//div[@aria-label='Message' and @role='textbox']",
            "//div[@contenteditable='true'][@role='textbox']",
        ]
        for selector in selectores:
            try:
                elemento = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                return elemento
            except TimeoutException:
                continue
        return None

    def enviar_mensaje(self, texto):
        """Abre el chat de Messenger desde el perfil y envía el mensaje"""
        btn_mensaje = self._encontrar_boton_mensaje()
        if not btn_mensaje:
            print(f"   {R}❌ No se encontró el botón 'Enviar mensaje'{X}")
            return False

        btn_mensaje.click()
        time.sleep(3)

        campo_mensaje = self._encontrar_campo_mensaje()
        if not campo_mensaje:
            print(f"   {R}❌ No se encontró el campo de texto del chat{X}")
            return False

        campo_mensaje.click()
        time.sleep(0.5)

        pyperclip.copy(texto)
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)

        campo_mensaje.send_keys(Keys.ENTER)
        time.sleep(2)

        print(f"   {V}✅ Mensaje enviado{X}")
        return True

    # ==================== ORQUESTACIÓN ====================

    def procesar_contacto(self, nombre, texto_mensaje):
        """Ejecuta el flujo completo: buscar → abrir perfil → enviar mensaje"""
        if not self.buscar_persona(nombre):
            return False

        if not self.abrir_perfil(nombre):
            return False

        return self.enviar_mensaje(texto_mensaje)

    def cerrar_navegador(self):
        """Cierra el navegador"""
        if self.driver:
            print(f"\n{N}🔒 Cerrando navegador...{X}")
            try:
                self.driver.quit()
                print(f"   {V}✅ Navegador cerrado{X}")
            except Exception:
                pass
            self.driver = None