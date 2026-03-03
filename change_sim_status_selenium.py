"""
Script de Selenium para cambiar el estado de billing de una SIM en Freeeway
y capturar la petición HTTP real para reverse engineering
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Configuración
FREEEWAY_URL = "https://ep.freeeway.com"
LOGIN_EMAIL = "gerencia@rastrear.com.co"
LOGIN_PASSWORD = "JNYf62vz3xN9S8m"
TARGET_MSISDN = "436761723367528"
TARGET_STATUS = "Suspend"  # El estado al que queremos cambiar

def setup_driver():
    """Configura el driver de Chrome con capacidad de capturar peticiones HTTP"""
    print("Configurando Chrome driver...")
    
    # Habilitar logging de performance para capturar peticiones HTTP
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
    
    options = Options()
    # options.add_argument('--headless')  # Comentado para ver qué pasa
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Habilitar performance logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Crear driver regular de Selenium
    driver = webdriver.Chrome(options=options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Almacenar peticiones capturadas
    driver.captured_requests = []
    
    return driver

def login(driver):
    """Inicia sesión en Freeeway"""
    print(f"\n[1/6] Navegando a {FREEEWAY_URL}...")
    driver.get(FREEEWAY_URL)
    
    wait = WebDriverWait(driver, 30)
    
    try:
        # Esperar a que la página cargue completamente
        print("Esperando a que la página cargue...")
        time.sleep(5)
        
        # Guardar screenshot para debugging
        driver.save_screenshot('step1_initial_page.png')
        print("Screenshot guardado: step1_initial_page.png")
        
        # Esperar a que Vaadin termine de cargar (buscar elementos generados dinámicamente)
        print("Esperando a que Vaadin genere el contenido...")
        time.sleep(10)  # Esperar más tiempo para que Vaadin genere los elementos
        
        # Guardar screenshot después de esperar por Vaadin
        driver.save_screenshot('step1b_after_vaadin_load.png')
        print("Screenshot guardado: step1b_after_vaadin_load.png")
        
        # Imprimir todos los inputs visibles
        print("\n=== Buscando todos los inputs en la página ===")
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Total de inputs encontrados: {len(all_inputs)}")
        for i, inp in enumerate(all_inputs):
            try:
                print(f"Input {i}: type={inp.get_attribute('type')}, "
                      f"name={inp.get_attribute('name')}, "
                      f"id={inp.get_attribute('id')}, "
                      f"class={inp.get_attribute('class')}, "
                      f"visible={inp.is_displayed()}")
            except:
                pass
        print("=" * 50)
        
        # Intentar diferentes selectores para el campo de email/username
        email_selectors = [
            (By.TAG_NAME, "input"),  # Buscar el primer input visible
            (By.CSS_SELECTOR, "input"),
            (By.CSS_SELECTOR, ".v-textfield"),  # Selectores de Vaadin
            (By.CSS_SELECTOR, ".v-textfield-focus"),
            (By.XPATH, "//input"),
            (By.ID, "username"),
            (By.ID, "email"),
            (By.ID, "user"),
            (By.ID, "login"),
            (By.NAME, "username"),
            (By.NAME, "email"),
            (By.NAME, "user"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='mail']"),
            (By.CSS_SELECTOR, "input[placeholder*='usuario']"),
            (By.CSS_SELECTOR, "input[placeholder*='user']"),
            (By.XPATH, "//input[@type='text' or @type='email']")
        ]
        
        email_field = None
        for by, selector in email_selectors:
            try:
                print(f"Intentando selector: {by} = {selector}")
                elements = driver.find_elements(by, selector)
                print(f"  Encontrados {len(elements)} elementos")
                
                # Si es un selector genérico, buscar el primer campo visible
                if by == By.TAG_NAME or (by == By.CSS_SELECTOR and selector in ["input", ".v-textfield"]):
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                email_field = elem
                                print(f"✓ Campo de email encontrado (primer input visible)")
                                break
                        except:
                            continue
                else:
                    email_field = wait.until(EC.presence_of_element_located((by, selector)))
                    if email_field.is_displayed():
                        print(f"✓ Campo de email encontrado con: {by} = {selector}")
                        break
                    else:
                        email_field = None
                
                if email_field:
                    break
            except Exception as e:
                print(f"  No encontrado con {selector}: {str(e)[:50]}")
                continue
        
        if not email_field:
            print("✗ No se encontró campo de email con ningún selector")
            return False
        
        # Intentar diferentes selectores para el campo de password
        password_selectors = [
            (By.ID, "password"),
            (By.ID, "pass"),
            (By.ID, "pwd"),
            (By.NAME, "password"),
            (By.NAME, "pass"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@type='password']")
        ]
        
        password_field = None
        for by, selector in password_selectors:
            try:
                print(f"Intentando selector: {by} = {selector}")
                password_field = driver.find_element(by, selector)
                if password_field.is_displayed():
                    print(f"✓ Campo de password encontrado con: {by} = {selector}")
                    break
            except:
                print(f"  No encontrado con {selector}")
                continue
        
        if not password_field:
            print("✗ No se encontró campo de password con ningún selector")
            return False
        
        # Llenar credenciales
        print(f"\nIngresando email: {LOGIN_EMAIL}")
        email_field.clear()
        time.sleep(0.5)
        email_field.send_keys(LOGIN_EMAIL)
        time.sleep(0.5)
        
        print("Ingresando password...")
        password_field.clear()
        time.sleep(0.5)
        password_field.send_keys(LOGIN_PASSWORD)
        time.sleep(0.5)
        
        # Guardar screenshot antes de hacer clic
        driver.save_screenshot('step2_credentials_entered.png')
        print("Screenshot guardado: step2_credentials_entered.png")
        
        # Buscar y hacer clic en el botón de login
        login_button_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.ID, "submit"),
            (By.ID, "login"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Ingresar')]"),
            (By.XPATH, "//button[contains(text(), 'Sign in')]"),
            (By.XPATH, "//input[@value='Login']"),
            (By.XPATH, "//input[@value='Ingresar']")
        ]
        
        login_button = None
        for by, selector in login_button_selectors:
            try:
                print(f"Buscando botón de login: {by} = {selector}")
                login_button = driver.find_element(by, selector)
                if login_button.is_displayed():
                    print(f"✓ Botón de login encontrado con: {by} = {selector}")
                    break
            except:
                continue
        
        if login_button:
            print("Haciendo clic en el botón de login...")
            login_button.click()
        else:
            # Intentar enviar el formulario presionando Enter
            print("No se encontró botón, intentando presionar Enter...")
            from selenium.webdriver.common.keys import Keys
            password_field.send_keys(Keys.RETURN)
        
        # Esperar a que se complete el login
        print("Esperando a que se complete el login...")
        time.sleep(8)
        
        # Guardar screenshot después del login
        driver.save_screenshot('step3_after_login.png')
        print("Screenshot guardado: step3_after_login.png")
        
        # Verificar que el login fue exitoso
        current_url = driver.current_url
        print(f"URL actual después del login: {current_url}")
        print(f"Título de la página: {driver.title}")
        
        # Verificar si hay mensajes de error
        page_text = driver.find_element(By.TAG_NAME, "body").text
        error_keywords = ['incorrect', 'invalid', 'error', 'incorrecto', 'inválido']
        
        if any(keyword in page_text.lower() for keyword in error_keywords):
            print("✗ Posible error de login detectado en la página")
            print(f"Texto de la página: {page_text[:300]}")
            return False
        
        if "login" not in current_url.lower() or len(page_text) > 200:
            print("✓ Login exitoso!")
            return True
        else:
            print("? El login puede haber fallado, aún estamos en la página de login")
            return False
            
    except Exception as e:
        print(f"✗ Error durante el login: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Guardar screenshot del error
        try:
            driver.save_screenshot('error_login.png')
            print("Screenshot de error guardado: error_login.png")
        except:
            pass
        
        print(f"URL actual: {driver.current_url}")
        print(f"Título de la página: {driver.title}")
        return False

def search_sim_by_msisdn(driver, msisdn):
    """Busca una SIM por su MSISDN"""
    print(f"\n[2/6] Buscando SIM con MSISDN: {msisdn}...")
    
    wait = WebDriverWait(driver, 30)
    
    try:
        # Hacer clic en el menú "SIM Cards"
        print("Buscando el menú 'SIM Cards'...")
        
        menu_selectors = [
            "//span[contains(text(), 'SIM Cards')]",
            "//div[contains(text(), 'SIM Cards')]",
            "//a[contains(text(), 'SIM Cards')]",
            "//*[contains(@class, 'v-menubar') and contains(., 'SIM Cards')]",
            "//*[contains(text(), 'SIM Cards')]"
        ]
        
        sim_menu = None
        for selector in menu_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"Buscando con selector: {selector} - encontrados {len(elements)}")
                
                for elem in elements:
                    if elem.is_displayed():
                        sim_menu = elem
                        print(f"✓ Menú 'SIM Cards' encontrado")
                        break
                
                if sim_menu:
                    break
            except Exception as e:
                print(f"Error con selector {selector}: {str(e)[:50]}")
                continue
        
        if sim_menu:
            print("Haciendo clic en el menú 'SIM Cards'...")
            sim_menu.click()
            
            # Esperar a que la URL cambie o que aparezca contenido específico de SIM Cards
            print("Esperando a que se cargue la página de SIM Cards...")
            time.sleep(5)
            
            # Verificar que estamos en la página correcta esperando el texto "SIM Cards found"
            for attempt in range(10):
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if "SIM Cards found" in body_text or "ICCID" in body_text:
                    print(f"✓ Página de SIM Cards cargada (intento {attempt + 1})")
                    break
                print(f"Esperando carga... intento {attempt + 1}/10")
                time.sleep(3)
            
            # Esperar adicional para que se carguen todos los datos
            time.sleep(5)
            
            driver.save_screenshot('step4_sim_cards_menu.png')
            print("Screenshot guardado: step4_sim_cards_menu.png")
        else:
            print("✗ No se encontró el menú 'SIM Cards'")
            print("Intentando navegar directamente...")
            
            # Intentar navegar directamente
            products_url = f"{FREEEWAY_URL}/#!products"
            print(f"Navegando a: {products_url}")
            driver.get(products_url)
            time.sleep(10)
        
        # Esperar a que Vaadin cargue el contenido y la tabla
        print("Esperando a que Vaadin genere el contenido completo...")
        time.sleep(8)
        
        # Guardar screenshot
        driver.save_screenshot('step5_products_page.png')
        print("Screenshot guardado: step5_products_page.png")
        
        # Verificar si estamos en la página correcta
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"\nTexto visible (primeros 500 caracteres):")
        print(body_text[:500])
        
        # Imprimir todos los inputs visibles para encontrar el campo de búsqueda
        print("\n=== Buscando campo de búsqueda 'Any text' ===")
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Total de inputs encontrados: {len(all_inputs)}")
        
        search_field = None
        for i, inp in enumerate(all_inputs):
            try:
                if inp.is_displayed() and inp.get_attribute('type') == 'text':
                    placeholder = inp.get_attribute('placeholder') or ''
                    print(f"Input visible {i}: placeholder='{placeholder}', class={inp.get_attribute('class')}")
                    
                    # Buscar el campo que tenga placeholder relacionado con búsqueda
                    if 'any text' in placeholder.lower() or i == 0:  # El primero suele ser el de búsqueda
                        search_field = inp
                        print(f"✓ Campo de búsqueda encontrado: {placeholder}")
                        break
            except:
                pass
        
        if not search_field:
            # Si no se encontró, usar el primer textfield visible
            print("Usando el primer input de texto visible...")
            for inp in all_inputs:
                try:
                    if inp.is_displayed() and inp.is_enabled() and inp.get_attribute('type') == 'text':
                        search_field = inp
                        break
                except:
                    pass
        
        if search_field:
            print(f"\nIngresando MSISDN en búsqueda: {msisdn}")
            
            # Hacer clic en el campo primero
            search_field.click()
            time.sleep(1)
            
            # Limpiar y escribir
            search_field.clear()
            time.sleep(0.5)
            search_field.send_keys(msisdn)
            time.sleep(2)
            
            # Guardar screenshot con búsqueda ingresada
            driver.save_screenshot('step6_search_entered.png')
            print("Screenshot guardado: step6_search_entered.png")
            
            # Buscar el botón de búsqueda (ícono de lupa)
            print("Buscando botón de búsqueda (ícono de lupa)...")
            search_button_found = False
            
            # Buscar botones cerca del campo de búsqueda
            buttons = driver.find_elements(By.CSS_SELECTOR, ".v-button, button, span[role='button']")
            for btn in buttons:
                try:
                    if btn.is_displayed():
                        # Buscar botón con ícono de búsqueda
                        btn_html = btn.get_attribute('outerHTML')
                        if '🔍' in btn.text or 'search' in btn_html.lower() or 'lupa' in btn_html.lower():
                            print("✓ Botón de búsqueda encontrado")
                            btn.click()
                            search_button_found = True
                            time.sleep(3)
                            break
                except:
                    pass
            
            if not search_button_found:
                # Intentar presionar Enter
                print("No se encontró botón, presionando Enter...")
                from selenium.webdriver.common.keys import Keys
                search_field.send_keys(Keys.RETURN)
                time.sleep(3)
            
            # Esperar a que se filtren los resultados
            print("Esperando resultados de búsqueda...")
            time.sleep(5)
            driver.save_screenshot('step7_search_results.png')
            print("Screenshot guardado: step7_search_results.png")
            
            print("✓ Búsqueda realizada")
            return True
        else:
            print("✗ No se encontró campo de búsqueda")
            
            # Mostrar el contenido de la página para debugging
            print("\nTexto visible en la página:")
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(body_text[:800])
            
            return False
            
    except Exception as e:
        print(f"✗ Error durante la búsqueda: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def find_and_click_sim_in_results(driver):
    """Encuentra la SIM en los resultados y selecciona el checkbox"""
    print(f"\n[3/6] Seleccionando la SIM card...")
    
    try:
        time.sleep(2)
        
        # Verificar que el MSISDN aparece en los resultados
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"¿El MSISDN {TARGET_MSISDN} aparece en la página? {TARGET_MSISDN in body_text}")
        
        if TARGET_MSISDN not in body_text:
            print("✗ El MSISDN no aparece en los resultados")
            print(f"Contenido visible: {body_text[:500]}")
            return False
        
        print("✓ MSISDN encontrado en la página")
        
        # Buscar todos los checkboxes visibles
        print("Buscando checkbox de la SIM card...")
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        print(f"Total de checkboxes encontrados: {len(checkboxes)}")
        
        checkbox_clicked = False
        for i, checkbox in enumerate(checkboxes):
            try:
                if checkbox.is_displayed() and checkbox.is_enabled():
                    # Buscar la fila que contiene este checkbox
                    parent = checkbox
                    for _ in range(10):  # Buscar hasta 10 niveles arriba
                        parent = parent.find_element(By.XPATH, "..")
                        parent_text = parent.text
                        
                        if TARGET_MSISDN in parent_text:
                            print(f"✓ Checkbox encontrado para la SIM con MSISDN {TARGET_MSISDN}")
                            
                            # Hacer clic en el checkbox
                            if not checkbox.is_selected():
                                checkbox.click()
                                print("✓ Checkbox seleccionado")
                            else:
                                print("Checkbox ya estaba seleccionado")
                            
                            time.sleep(2)
                            driver.save_screenshot('step8_checkbox_selected.png')
                            print("Screenshot guardado: step8_checkbox_selected.png")
                            
                            checkbox_clicked = True
                            break
            except Exception as e:
                continue
            
            if checkbox_clicked:
                break
        
        if not checkbox_clicked:
            # Intentar hacer clic en el primer checkbox visible (asumiendo que el filtro dejó solo una SIM)
            print("No se encontró checkbox específico, usando el primer checkbox visible...")
            for checkbox in checkboxes:
                try:
                    if checkbox.is_displayed() and checkbox.is_enabled() and not checkbox.is_selected():
                        checkbox.click()
                        print("✓ Primer checkbox seleccionado")
                        time.sleep(2)
                        driver.save_screenshot('step8_checkbox_selected.png')
                        print("Screenshot guardado: step8_checkbox_selected.png")
                        checkbox_clicked = True
                        break
                except:
                    continue
        
        if checkbox_clicked:
            print("✓ SIM card seleccionada exitosamente")
            return True
        else:
            print("✗ No se pudo seleccionar el checkbox")
            return False
        
    except Exception as e:
        print(f"✗ Error buscando la SIM en resultados: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def change_billing_status(driver, new_status):
    """Cambia el estado de billing de la SIM haciendo clic en el 4to icono"""
    print(f"\n[4/6] Cambiando el estado de billing a: {new_status}...")
    
    wait = WebDriverWait(driver, 30)
    
    try:
        time.sleep(2)
        
        # Guardar screenshot del estado actual
        driver.save_screenshot('step9_before_icon_click.png')
        print("Screenshot guardado: step9_before_icon_click.png")
        
        # Buscar todos los iconos/botones en la barra de herramientas
        print("\n=== Buscando el 4to icono (Change Billing Status) ===")
        
        # Los iconos en Vaadin suelen estar en divs con clase v-button
        toolbar_buttons = driver.find_elements(By.CSS_SELECTOR, ".v-button")
        print(f"Total de botones/iconos encontrados: {len(toolbar_buttons)}")
        
        # Filtrar solo los visibles de la barra superior (cerca de la tabla)
        visible_icons = []
        for btn in toolbar_buttons:
            try:
                if btn.is_displayed():
                    location = btn.location
                    size = btn.size
                    # Los iconos de la barra suelen estar en la parte superior
                    if location['y'] < 300 and size['width'] < 100:  # Iconos pequeños en la parte superior
                        visible_icons.append(btn)
                        print(f"Icono {len(visible_icons)}: location={location}, size={size}")
            except:
                pass
        
        print(f"\nIconos visibles en la barra: {len(visible_icons)}")
        
        # Hacer clic en el 4to icono (índice 3)
        if len(visible_icons) >= 4:
            fourth_icon = visible_icons[3]
            print("\nHaciendo clic en el 4to icono...")
            fourth_icon.click()
            time.sleep(3)
            
            driver.save_screenshot('step10_modal_opened.png')
            print("Screenshot guardado: step10_modal_opened.png")
        else:
            print(f"✗ No se encontraron suficientes iconos (se encontraron {len(visible_icons)})")
            
            # Intentar buscar por texto o descripción
            print("Buscando botón por texto alternativo...")
            for btn in toolbar_buttons:
                try:
                    if btn.is_displayed():
                        btn_html = btn.get_attribute('outerHTML')
                        btn_text = btn.text
                        
                        if 'billing' in btn_html.lower() or 'billing' in btn_text.lower() or 'status' in btn_text.lower():
                            print(f"✓ Botón encontrado: {btn_text}")
                            btn.click()
                            time.sleep(3)
                            driver.save_screenshot('step10_modal_opened.png')
                            print("Screenshot guardado: step10_modal_opened.png")
                            break
                except:
                    pass
        
        # Ahora debería estar abierto el modal "Change Billing Status"
        print("\n=== Buscando modal y opciones ===")
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"Contenido visible: {body_text[:500]}")
        
        # Verificar que el modal está abierto
        if "Change Billing Status" not in body_text and "Billing Status" not in body_text:
            print("✗ El modal no parece estar abierto")
            return False
        
        print("✓ Modal 'Change Billing Status' está abierto")
        
        # Guardar timestamp para filtrar peticiones posteriores
        driver.status_change_timestamp = time.time()
        print(f"Timestamp guardado para filtrar peticiones: {driver.status_change_timestamp}")
        
        # Buscar los radio buttons para seleccionar "Suspend"
        print("\n=== Buscando radio button 'Suspend' ===")
        
        # Buscar todos los radio buttons
        all_radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        print(f"Total de radio buttons encontrados: {len(all_radios)}")
        
        suspend_radio = None
        for radio in all_radios:
            try:
                if radio.is_displayed():
                    # Buscar el label asociado al radio button
                    radio_id = radio.get_attribute('id')
                    parent = radio.find_element(By.XPATH, "..")
                    parent_text = parent.text
                    
                    print(f"Radio button: id={radio_id}, parent_text='{parent_text}'")
                    
                    if new_status.lower() in parent_text.lower():
                        suspend_radio = radio
                        print(f"✓ Radio button '{new_status}' encontrado")
                        break
            except Exception as e:
                continue
        
        if suspend_radio:
            print(f"Seleccionando opción '{new_status}'...")
            
            # Hacer clic en el radio button
            if not suspend_radio.is_selected():
                suspend_radio.click()
                print("✓ Opción seleccionada")
            else:
                print("Opción ya estaba seleccionada")
            
            time.sleep(2)
            driver.save_screenshot('step11_suspend_selected.png')
            print("Screenshot guardado: step11_suspend_selected.png")
            
            # Buscar y hacer clic en el botón "Change"
            print("\nBuscando botón 'Change'...")
            
            change_button_selectors = [
                "//span[contains(@class, 'v-button') and contains(., 'Change')]",
                "//div[contains(@class, 'v-button') and contains(., 'Change')]",
                "//button[contains(text(), 'Change')]",
                "//input[@value='Change']"
            ]
            
            for selector in change_button_selectors:
                try:
                    change_button = driver.find_element(By.XPATH, selector)
                    if change_button.is_displayed():
                        print(f"✓ Botón 'Change' encontrado")
                        change_button.click()
                        print("✓ Haciendo clic en 'Change'...")
                        time.sleep(5)
                        
                        driver.save_screenshot('step12_after_change.png')
                        print("Screenshot guardado: step12_after_change.png")
                        
                        print("✓✓✓ Cambio de estado enviado exitosamente ✓✓✓")
                        return True
                except Exception as e:
                    continue
            
            print("✗ No se encontró el botón 'Change'")
            return False
        else:
            print(f"✗ No se encontró el radio button para '{new_status}'")
            return False
            
    except Exception as e:
        print(f"✗ Error cambiando el estado: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def capture_api_request(driver):
    """Captura la petición HTTP real que cambió el estado usando Chrome Performance Logs"""
    print(f"\n[5/6] Capturando petición HTTP desde logs de performance...")
    
    try:
        # Esperar un poco para asegurar que la petición se complete
        time.sleep(3)
        
        # Obtener logs de performance de Chrome
        print("Obteniendo logs de performance de Chrome...")
        logs = driver.get_log('performance')
        print(f"Total de logs capturados: {len(logs)}")
        
        # Filtrar y parsear logs relevantes
        api_requests = []
        
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                # Filtrar peticiones de red
                if method == 'Network.requestWillBeSent':
                    request = message.get('message', {}).get('params', {}).get('request', {})
                    request_id = message.get('message', {}).get('params', {}).get('requestId', '')
                    
                    url = request.get('url', '')
                    req_method = request.get('method', '')
                    
                    # Filtrar por métodos HTTP relevantes y URLs de API
                    if req_method in ['PATCH', 'POST', 'PUT', 'DELETE']:
                        if any(keyword in url.lower() for keyword in ['api', 'simcard', 'sim-card', 'billing', 'status', 'portal', 'services']):
                            
                            # Buscar la respuesta correspondiente
                            response_body = None
                            response_status = None
                            
                            for resp_log in logs:
                                try:
                                    resp_message = json.loads(resp_log['message'])
                                    resp_method = resp_message.get('message', {}).get('method', '')
                                    resp_params = resp_message.get('message', {}).get('params', {})
                                    
                                    if resp_method == 'Network.responseReceived' and resp_params.get('requestId') == request_id:
                                        response = resp_params.get('response', {})
                                        response_status = response.get('status')
                                        
                                        # Intentar obtener el body de la respuesta
                                        try:
                                            response_body_log = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                            response_body = response_body_log.get('body')
                                        except:
                                            pass
                                        
                                        break
                                except:
                                    continue
                            
                            api_request = {
                                'method': req_method,
                                'url': url,
                                'headers': request.get('headers', {}),
                                'postData': request.get('postData'),
                                'response_status': response_status,
                                'response_body': response_body
                            }
                            
                            api_requests.append(api_request)
                            
                            print(f"\n  Petición capturada:")
                            print(f"    Método: {req_method}")
                            print(f"    URL: {url}")
                            print(f"    Status: {response_status if response_status else 'Desconocido'}")
                            
            except Exception as e:
                continue
        
        if api_requests:
            print(f"\n✓ Encontradas {len(api_requests)} peticiones API relevantes")
            
            # Guardar detalles de todas las peticiones
            api_details = []
            
            for i, req in enumerate(api_requests, 1):
                print(f"\n--- Petición #{i} ---")
                print(f"Método: {req['method']}")
                print(f"URL: {req['url']}")
                
                details = req.copy()
                
                # Mostrar headers (sin información sensible)
                print(f"Headers:")
                for header, value in req['headers'].items():
                    if header.lower() not in ['cookie', 'authorization']:
                        print(f"  {header}: {value}")
                
                # Mostrar body
                if req.get('postData'):
                    print(f"Body: {req['postData']}")
                    
                    # Intentar parsear como JSON
                    try:
                        body_json = json.loads(req['postData'])
                        print(f"Body (JSON):")
                        print(json.dumps(body_json, indent=2))
                        details['body_json'] = body_json
                    except:
                        pass
                
                # Mostrar respuesta
                if req.get('response_status'):
                    print(f"Response Status: {req['response_status']}")
                    
                    if req.get('response_body'):
                        try:
                            response_json = json.loads(req['response_body'])
                            print(f"Response Body (JSON):")
                            print(json.dumps(response_json, indent=2)[:500])
                            details['response_json'] = response_json
                        except:
                            print(f"Response Body: {req['response_body'][:500]}")
                
                api_details.append(details)
            
            # Guardar en archivo
            output_file = 'captured_api_request.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(api_details, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Detalles guardados en: {output_file}")
            return api_details
        else:
            print("✗ No se encontraron peticiones API relevantes en los logs")
            
            # Guardar todos los logs para debugging
            with open('all_performance_logs.json', 'w', encoding='utf-8') as f:
                json.dump([json.loads(log['message']) for log in logs[-50:]], f, indent=2)
            print("Logs guardados en all_performance_logs.json para debugging")
            
            return None
            
    except Exception as e:
        print(f"✗ Error capturando petición: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def verify_status_change(driver):
    """Verifica que el cambio de estado fue exitoso"""
    print(f"\n[6/6] Verificando cambio de estado...")
    
    try:
        time.sleep(2)
        
        # Buscar elementos que muestren el estado actual
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        if TARGET_STATUS in page_text or TARGET_STATUS.upper() in page_text or TARGET_STATUS.lower() in page_text:
            print(f"✓ Estado '{TARGET_STATUS}' encontrado en la página")
            return True
        else:
            print(f"✗ No se encuentra evidencia del estado '{TARGET_STATUS}' en la página")
            print("Texto visible en la página (primeros 500 caracteres):")
            print(page_text[:500])
            return False
            
    except Exception as e:
        print(f"Error verificando el cambio: {str(e)}")
        return False

def main():
    """Función principal"""
    print("="*80)
    print("SCRIPT DE AUTOMATIZACIÓN FREEEWAY - CAMBIO DE ESTADO DE SIM")
    print("="*80)
    print(f"Target MSISDN: {TARGET_MSISDN}")
    print(f"Nuevo Estado: {TARGET_STATUS}")
    print("="*80)
    
    driver = None
    
    try:
        # 1. Configurar driver
        driver = setup_driver()
        
        # 2. Login
        if not login(driver):
            print("\n✗ FALLO: No se pudo iniciar sesión")
            return False
        
        # 3. Buscar SIM
        if not search_sim_by_msisdn(driver, TARGET_MSISDN):
            print("\n✗ FALLO: No se pudo buscar la SIM")
            # Intentar continuar de todas formas
            pass
        
        # 4. Encontrar y hacer clic en la SIM
        if not find_and_click_sim_in_results(driver):
            print("\n✗ FALLO: No se encontró la SIM en los resultados")
            # Guardar screenshot para debugging
            driver.save_screenshot('debug_search_results.png')
            print("Screenshot guardado: debug_search_results.png")
            
            # Mostrar las opciones disponibles en el menú
            print("\nExplorando el sitio manualmente...")
            print("¿Qué opciones de menú están disponibles?")
            
            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"\nEnlaces encontrados ({len(links)} total):")
            for link in links[:30]:  # Mostrar los primeros 30
                if link.is_displayed() and link.text:
                    print(f"  - {link.text} ({link.get_attribute('href')})")
        
        # 5. Cambiar estado
        if not change_billing_status(driver, TARGET_STATUS):
            print("\n✗ FALLO: No se pudo cambiar el estado")
            driver.save_screenshot('debug_change_status.png')
            print("Screenshot guardado: debug_change_status.png")
        
        # 6. Capturar petición API
        api_request = capture_api_request(driver)
        
        # 7. Verificar cambio
        status_changed = verify_status_change(driver)
        
        # Resumen final
        print("\n" + "="*80)
        print("RESUMEN")
        print("="*80)
        
        if status_changed:
            print("✓ ÉXITO: El estado de la SIM fue cambiado exitosamente")
        else:
            print("? PARCIAL: El proceso se completó pero no se pudo verificar el cambio")
        
        if api_request:
            print("✓ Petición API capturada y guardada en captured_api_request.json")
            print("\nFormato de la petición principal:")
            main_req = api_request[0]
            print(f"  Método: {main_req['method']}")
            print(f"  URL: {main_req['url']}")
            if main_req.get('body_json'):
                print(f"  Payload:")
                print(json.dumps(main_req['body_json'], indent=4))
        else:
            print("✗ No se pudo capturar la petición API")
        
        print("="*80)
        
        # Esperar un poco antes de cerrar para poder ver
        print("\nEsperando 5 segundos antes de cerrar...")
        time.sleep(5)
        
        return status_changed and api_request is not None
        
    except Exception as e:
        print(f"\n✗ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot('debug_error.png')
            print("Screenshot de error guardado: debug_error.png")
        
        return False
        
    finally:
        if driver:
            print("\nCerrando navegador...")
            driver.quit()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
