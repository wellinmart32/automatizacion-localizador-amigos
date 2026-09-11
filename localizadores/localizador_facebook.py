import os
import sys
import time
import pyperclip
from urllib.parse import quote

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
        """Abre Facebook y verifica sesión activa mediante la URL actual (más estable que selectores de DOM)"""
        print(f"\n{N}🔐 Verificando sesión de Facebook...{X}")
        self.driver.get("https://www.facebook.com")
        time.sleep(4)

        if self._es_pagina_seguridad():
            print(f"\n{A}{N}⚠️  FACEBOOK REQUIERE VERIFICACIÓN DE SEGURIDAD{X}")
            print(f"{A}Por favor resuelve el puzzle en el navegador. Tienes 3 minutos.{X}\n")
            return self._esperar_resolucion(timeout=180)

        url_actual = self.driver.current_url
        if 'login' in url_actual:
            print(f"\n{A}{N}⚠️  NO HAS INICIADO SESIÓN EN FACEBOOK{X}")
            print(f"{A}Por favor inicia sesión en el navegador. Tienes 2 minutos.{X}\n")
            return self._esperar_resolucion(timeout=120)

        print(f"   {V}✅ Ya tienes sesión activa en Facebook{X}")
        return True

    def _es_pagina_seguridad(self):
        """Detecta si Facebook mostró una página de verificación de seguridad"""
        url_actual = self.driver.current_url
        urls_seguridad = [
            'two_step_verification', 'checkpoint', 'login/device-based',
            'security_check', 'identity_confirmation', 'recaptcha', 'captcha'
        ]
        return any(p in url_actual for p in urls_seguridad)

    def _esperar_resolucion(self, timeout=180):
        """Espera a que el usuario inicie sesión o resuelva la verificación de seguridad"""
        tiempo_transcurrido = 0
        while tiempo_transcurrido < timeout:
            time.sleep(5)
            tiempo_transcurrido += 5
            url_actual = self.driver.current_url
            if not self._es_pagina_seguridad() and 'login' not in url_actual and 'facebook.com' in url_actual:
                print(f"   {V}✅ Sesión detectada{X}")
                time.sleep(3)
                return True
            restantes = timeout - tiempo_transcurrido
            print(f"   ⏳ Esperando... ({restantes}s restantes)")
        print(f"   {R}❌ Tiempo de espera agotado{X}")
        return False

    # ==================== BÚSQUEDA ====================

    def buscar_persona(self, nombre):
        """Navega directo a la página de resultados de búsqueda de personas (más estable que el dropdown en vivo)"""
        print(f"\n🔍 Buscando: '{nombre}'")

        url = f"https://www.facebook.com/search/people/?q={quote(nombre)}"
        self.driver.get(url)
        time.sleep(float(self.config.get('tiempo_espera_busqueda_segundos', 5)))
        return True

    def _encontrar_resultados(self, cantidad, timeout=10):
        """Localiza hasta 'cantidad' links de foto de perfil de los primeros resultados (más estable que el nombre)"""
        xpath = "//a[starts-with(@aria-label, 'Foto de perfil de')]"
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
        except TimeoutException:
            return []

        elementos = self.driver.find_elements(By.XPATH, xpath)
        hrefs = []
        for elemento in elementos[:cantidad]:
            href = elemento.get_attribute('href')
            if href:
                hrefs.append(href)
        return hrefs

    def abrir_perfil_por_url(self, url_perfil):
        """Navega directo a la URL del perfil"""
        self.driver.get(url_perfil)
        time.sleep(4)
        print(f"   {V}✅ Perfil abierto{X}")
        return True

    # ==================== MENSAJE ====================

    def _encontrar_boton_mensaje(self, timeout=10):
        """Selector en cascada para el botón 'Enviar mensaje' del perfil"""
        selectores = [
            "//div[@aria-label='Enviar mensaje']",
            "//div[@aria-label='Message']",
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
        """Selector en cascada para el campo de texto del chat de Messenger (evita confundirse con otros composers de la página)"""
        selectores = [
            "//div[@contenteditable='true'][starts-with(@aria-label, 'Escribe a')]",
            "//div[@contenteditable='true'][starts-with(@aria-label, 'Write to')]",
            "//div[@aria-label='Mensaje' and @role='textbox']",
            "//div[@aria-label='Message' and @role='textbox']",
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

        self.driver.execute_script("arguments[0].click();", btn_mensaje)
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
        self._cerrar_chat_activo()
        return True

    def _cerrar_chat_activo(self):
        """Cierra la ventanita de chat de Messenger para que no obstruya el siguiente perfil"""
        try:
            btn_cerrar = self.driver.find_element(By.XPATH, "//div[@aria-label='Cerrar chat']")
            self.driver.execute_script("arguments[0].click();", btn_cerrar)
            time.sleep(1)
        except NoSuchElementException:
            pass

    # ==================== ORQUESTACIÓN ====================

    def procesar_contacto(self, nombre, texto_mensaje, cantidad_resultados=1):
        """Ejecuta el flujo completo: buscar → obtener hasta X resultados → enviar mensaje a cada uno"""
        if not self.buscar_persona(nombre):
            return 0, 0

        urls_perfiles = self._encontrar_resultados(cantidad_resultados)
        if not urls_perfiles:
            print(f"   {R}❌ No se encontró ningún resultado{X}")
            return 0, 0

        print(f"   {C}📋 {len(urls_perfiles)} resultado(s) encontrado(s) para '{nombre}'{X}")

        exitosos = 0
        for i, url_perfil in enumerate(urls_perfiles):
            print(f"\n   {N}➡️  Resultado {i + 1}/{len(urls_perfiles)}{X}")
            if not self.abrir_perfil_por_url(url_perfil):
                continue
            if self.enviar_mensaje(texto_mensaje):
                exitosos += 1

        return exitosos, len(urls_perfiles)

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