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

    FILTROS_CIUDAD = {
        'madrid': 'eyJjaXR5OjAiOiJ7XCJuYW1lXCI6XCJ1c2Vyc19sb2NhdGlvblwiLFwiYXJnc1wiOlwiMTA2NTA0ODU5Mzg2MjMwXCJ9In0%3D',
    }

    def buscar_persona(self, nombre, ubicacion=''):
        """Navega directo a la página de resultados de búsqueda de personas, aplicando el filtro nativo de ciudad de Facebook si se indica"""
        print(f"\n🔍 Buscando: '{nombre}'" + (f" (filtro: {ubicacion})" if ubicacion else ""))

        url = f"https://www.facebook.com/search/people/?q={quote(nombre)}"

        filtro = self.FILTROS_CIUDAD.get(ubicacion.lower().strip()) if ubicacion else None
        if filtro:
            url += f"&filters={filtro}"
        elif ubicacion:
            print(f"   ⚠️  No hay filtro configurado para '{ubicacion}', se busca sin filtro de ciudad")

        self.driver.get(url)
        time.sleep(float(self.config.get('tiempo_espera_busqueda_segundos', 5)))
        return True

    def _encontrar_resultados(self, cantidad, timeout=10, filtro_amistad='todos', evitar_duplicados=False, urls_ya_enviadas=None):
        """Localiza hasta 'cantidad' resultados, filtrando por amistad y/o duplicados si se indica (la ubicación ya viene filtrada por Facebook en la URL de búsqueda)"""
        if urls_ya_enviadas is None:
            urls_ya_enviadas = []

        xpath_articulos = "//div[@role='feed']//div[@role='article']"
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath_articulos))
            )
        except TimeoutException:
            return []

        articulos = self.driver.find_elements(By.XPATH, xpath_articulos)
        hrefs = []

        for articulo in articulos:
            try:
                link_foto = articulo.find_element(By.XPATH, ".//a[starts-with(@aria-label, 'Foto de perfil de')]")
                href = link_foto.get_attribute('href')
            except NoSuchElementException:
                continue

            if not href:
                continue

            if evitar_duplicados and href in urls_ya_enviadas:
                continue

            es_amigo = len(articulo.find_elements(By.XPATH, ".//div[@aria-label='Enviar mensaje']")) > 0

            if filtro_amistad == 'amigos' and not es_amigo:
                continue
            if filtro_amistad == 'no_amigos' and es_amigo:
                continue

            hrefs.append(href)

            if len(hrefs) >= cantidad:
                break

        return hrefs

    def abrir_perfil_por_url(self, url_perfil):
        """Navega directo a la URL del perfil"""
        self.driver.get(url_perfil)
        time.sleep(4)
        print(f"   {V}✅ Perfil abierto{X}")
        return True

    def _obtener_nombre_perfil(self):
        """Extrae el nombre real del perfil actualmente abierto (título de la página h1)"""
        try:
            elemento = self.driver.find_element(By.XPATH, "//h1")
            return elemento.text.strip()
        except NoSuchElementException:
            return ""

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

    def _encontrar_campo_mensaje(self, timeout=3):
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

    def _chat_bloqueado(self):
        """Detecta si Facebook muestra algún mensaje de bloqueo de envío a esta cuenta"""
        frases_bloqueo = [
            'No puedes enviar mensajes a esta cuenta',
            'todavía no puede acceder a este chat',
        ]
        for frase in frases_bloqueo:
            try:
                self.driver.find_element(By.XPATH, f"//*[contains(text(), '{frase}')]")
                return True
            except NoSuchElementException:
                continue
        return False

    def enviar_mensaje(self, texto):
        """Abre el chat de Messenger desde el perfil y envía el mensaje.
        Devuelve (True, False) si se envió, o (False, True) si fue bloqueo permanente (para no reintentar), o (False, False) si fue un fallo temporal"""
        btn_mensaje = self._encontrar_boton_mensaje()
        if not btn_mensaje:
            print(f"   {R}❌ No se encontró el botón 'Enviar mensaje'{X}")
            return False, False

        self.driver.execute_script("arguments[0].click();", btn_mensaje)
        time.sleep(3)

        if self._chat_bloqueado():
            print(f"   {A}⚠️  Facebook bloqueó el envío a esta cuenta{X}")
            self._cerrar_chat_activo()
            return False, True

        campo_mensaje = self._encontrar_campo_mensaje()
        if not campo_mensaje:
            print(f"   {R}❌ No se encontró el campo de texto del chat{X}")
            self._cerrar_chat_activo()
            return False, False

        campo_mensaje.click()
        time.sleep(0.5)

        pyperclip.copy(texto)
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)

        campo_mensaje.send_keys(Keys.ENTER)
        time.sleep(2)

        print(f"   {V}✅ Mensaje enviado{X}")
        self._cerrar_chat_activo()
        return True, False

    def _cerrar_chat_activo(self):
        """Cierra la ventanita de chat de Messenger para que no obstruya el siguiente perfil"""
        try:
            btn_cerrar = self.driver.find_element(By.XPATH, "//div[@aria-label='Cerrar chat']")
            self.driver.execute_script("arguments[0].click();", btn_cerrar)
            time.sleep(1)
        except NoSuchElementException:
            pass

    # ==================== ORQUESTACIÓN ====================

    def procesar_contacto(self, nombre, texto_mensaje, cantidad_resultados=1, filtro_amistad='todos', evitar_duplicados=False, urls_ya_enviadas=None, ubicacion=''):
        """Ejecuta el flujo completo: buscar (con filtro de ciudad de Facebook si aplica) → obtener hasta X resultados → enviar mensaje a cada uno"""
        if not self.buscar_persona(nombre, ubicacion=ubicacion):
            return 0, 0, [], []

        resultados = self._encontrar_resultados(
            cantidad_resultados,
            filtro_amistad=filtro_amistad,
            evitar_duplicados=evitar_duplicados,
            urls_ya_enviadas=urls_ya_enviadas
        )
        if not resultados:
            print(f"   {R}❌ No se encontró ningún resultado nuevo{X}")
            return 0, 0, [], []

        print(f"   {C}📋 {len(resultados)} resultado(s) encontrado(s) para '{nombre}'{X}")

        exitosos = 0
        enviados_ahora = []
        bloqueados_ahora = []
        for i, url_perfil in enumerate(resultados):
            print(f"\n   {N}➡️  Resultado {i + 1}/{len(resultados)}{X}")
            if not self.abrir_perfil_por_url(url_perfil):
                continue

            nombre_perfil = self._obtener_nombre_perfil()

            enviado, fue_bloqueo = self.enviar_mensaje(texto_mensaje)
            if enviado:
                exitosos += 1
                enviados_ahora.append({'nombre': nombre_perfil, 'url': url_perfil})
            elif fue_bloqueo:
                bloqueados_ahora.append({'nombre': nombre_perfil, 'url': url_perfil})

        return exitosos, len(resultados), enviados_ahora, bloqueados_ahora

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