"""
Script simplificado - permite navegación manual con pausa
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Configuración
FREEEWAY_URL = "https://ep.freeeway.com"
LOGIN_EMAIL = "gerencia@rastrear.com.co"
LOGIN_PASSWORD = "JNYf62vz3xN9S8m"
TARGET_MSISDN = "436761723367528"

def setup_driver():
    """Configura el driver de Chrome"""
    print("Configurando Chrome driver...")
    
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
    
    options = Options()
    options.add_argument('--window-size=1920,1080')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    driver.captured_requests = []
    
    return driver

def login(driver):
    """Login automático"""
    print(f"\\nNavegando a {FREEEWAY_URL}...")
    driver.get(FREEEWAY_URL)
    
    time.sleep(10)
    
    try:
        # Buscar campos de login
        inputs = driver.find_elements(By.TAG_NAME, "input")
        
        email_field = None
        password_field = None
        
        for inp in inputs:
            if inp.is_displayed() and inp.get_attribute('type') == 'text':
                email_field = inp
            elif inp.is_displayed() and inp.get_attribute('type') == 'password':
                password_field = inp
        
        if email_field and password_field:
            print(f"Ingresando credenciales...")
            email_field.send_keys(LOGIN_EMAIL)
            time.sleep(1)
            password_field.send_keys(LOGIN_PASSWORD)
            time.sleep(1)
            password_field.send_keys(Keys.RETURN)
            
            time.sleep(10)
            print("✓ Login completado")
            return True
        else:
            print("✗ No se encontraron campos de login")
            return False
    except Exception as e:
        print(f"Error en login: {e}")
        return False

def wait_for_user():
    """Pausa para que el usuario navegue manualmente"""
    print("\\n" + "="*80)
    print("PAUSA PARA NAVEGACIÓN MANUAL")
    print("="*80)
    print("El navegador está ABIERTO y el script está CAPTURANDO peticiones HTTP.")
    print("")
    print("Por favor, realiza los siguientes pasos MANUALMENTE en el navegador:")
    print("")
    print("  1. Haz clic en el menú 'SIM Cards'")
    print("  2. Espera a que cargue la tabla completa (700 SIM Cards found)")
    print(f"  3. En 'Search: Any text', ingresa: {TARGET_MSISDN}")
    print("  4. Haz clic en el botón de búsqueda (🔍) o presiona Enter")
    print("  5. Espera a que aparezcan los resultados filtrados")
    print("  6. Marca el checkbox de la SIM card")
    print("  7. Haz clic en el 4to icono de la barra (Change Billing Status)")
    print("  8. En el modal, selecciona el radio button 'Suspend'")
    print("  9. Haz clic en el botón 'Change' para CONFIRMAR")
    print("  10. Espera a que el modal se cierre")
    print("")
    print("ℹ️  El script está capturando TODAS las peticiones HTTP en segundo plano.")
    print("")
    print("Cuando hayas COMPLETADO todos los pasos, presiona Enter aquí...")
    print("="*80)
    
    input("\\n>>> Presiona Enter cuando hayas terminado: ")
    
    print("\\nContinuando...")
    time.sleep(2)

def capture_api_requests(driver):
    """Captura las peticiones HTTP del log"""
    print("\\n" + "="*80)
    print("ANALIZANDO PETICIONES HTTP CAPTURADAS")
    print("="*80)
    
    try:
        logs = driver.get_log('performance')
        print(f"\\nTotal de logs de performance: {len(logs)}")
        
        all_requests = []
        api_requests = []
        
        print("\\nAnalizando todas las peticiones...")
        for i, log in enumerate(logs):
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                if method == 'Network.requestWillBeSent':
                    request = message.get('message', {}).get('params', {}).get('request', {})
                    url = request.get('url', '')
                    req_method = request.get('method', '')
                    
                    all_requests.append({
                        'method': req_method,
                        'url': url
                    })
                    
                    # Mostrar todas las peticiones POST, PUT, PATCH, DELETE
                    if req_method in ['PATCH', 'POST', 'PUT', 'DELETE']:
                        print(f"\\n  [{i+1}/{len(logs)}] {req_method} detectado:")
                        print(f"    URL: {url}")
                        
                        # Mostrar payload si existe
                        if request.get('postData'):
                            print(f"    Payload: {request.get('postData')[:200]}...")
                        
                        # Si parece relevante, guardarlo
                        if any(keyword in url.lower() for keyword in ['simcard', 'billing', 'status', 'portal', 'services']):
                            print(f"    >>> RELEVANTE PARA API <<<")
                            
                            api_request = {
                                'method': req_method,
                                'url': url,
                                'headers': request.get('headers', {}),
                                'postData': request.get('postData')
                            }
                            
                            api_requests.append(api_request)
            except Exception as e:
                continue
        
        print(f"\\n\\nRESUMEN:")
        print(f"  Total peticiones analizadas: {len(all_requests)}")
        print(f"  Peticiones POST/PUT/PATCH/DELETE: {len([r for r in all_requests if r['method'] in ['POST', 'PUT', 'PATCH', 'DELETE']])}")
        print(f"  Peticiones API relevantes: {len(api_requests)}")
        
        # Mostrar TOP 20 URLs más recientes (para debugging)
        print("\\n\\nÚltimas 20 peticiones (todas):")
        for i, req in enumerate(all_requests[-20:], 1):
            print(f"  {i}. {req['method']:6s} {req['url'][:80]}")
        
        if api_requests:
            # Guardar en archivo
            with open('captured_requests_manual.json', 'w', encoding='utf-8') as f:
                json.dump(api_requests, f, indent=2, ensure_ascii=False)
            
            print(f"\\n\\n{'='*80}")
            print(f"✓ {len(api_requests)} PETICIONES API GUARDADAS")
            print("="*80)
            
            # Mostrar todas las peticiones capturadas
            for i, req in enumerate(api_requests, 1):
                print(f"\\nPETICIÓN #{i}:")
                print(f"  Método: {req['method']}")
                print(f"  URL: {req['url']}")
                
                if req.get('postData'):
                    print(f"  Payload:")
                    try:
                        payload_json = json.loads(req['postData'])
                        print(json.dumps(payload_json, indent=4))
                    except:
                        print(f"    {req['postData']}")
                print("-" * 80)
            
            return api_requests
        else:
            print("\\n✗ No se capturaron peticiones API relevantes")
            print("\\nPosibles razones:")
            print("  1. El cambio se realizó antes de ejecutar este script")
            print("  2. Las peticiones usan una URL diferente a la esperada")
            print("  3. El navegador no está capturando los logs correctamente")
            return None
            
    except Exception as e:
        print(f"Error capturando peticiones: {e}")
        return None

def main():
    """Función principal"""
    print("="*80)
    print("SCRIPT DE CAPTURA MANUAL DE API - FREEEWAY")
    print("="*80)
    
    driver = None
    
    try:
        # Setup
        driver = setup_driver()
        
        # Login automático
        if not login(driver):
            print("\\n✗ Fallo en login automático")
            print("Por favor, inicia sesión manualmente y luego presiona Enter")
            input(">>> ")
        
        # Pausa para navegación manual
        wait_for_user()
        
        # Capturar peticiones
        api_requests = capture_api_requests(driver)
        
        # Verificar en la página  
        print("\\nVerificando estado en la página...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "Suspend" in body_text:
            print("✓ ¡El texto 'Suspend' aparece en la página!")
        else:
            print("? No se ve 'Suspend' en la página")
        
        driver.save_screenshot('manual_final_state.png')
        print("Screenshot guardado: manual_final_state.png")
        
        # Resumen
        print("\\n" + "="*80)
        print("COMPLETADO")
        print("="*80)
        
        if api_requests:
            print(f"\\n✓ Se capturaron {len(api_requests)} peticiones API")
            print("✓ Detalles guardados en: captured_requests_manual.json")
            print("")
            print("Próximos pasos:")
            print("  1. Revisa el archivo JSON para ver el formato exacto")
            print("  2. Usa ese formato para actualizar app.py")
            print("  3. Prueba el endpoint con el nuevo formato")
        else:
            print("\\n✗ No se capturaron peticiones API")
            print("")
            print("Posibles causas:")
            print("  - El cambio se hizo antes de que iniciara la captura")
            print("  - La URL de la API no coincide con los filtros")
            print("  - Verifica manualmente en el DevTools del navegador")
        
        print("\\n" + "="*80)
        print("Presiona Enter para cerrar el navegador...")
        input(">>> ")
        
    except Exception as e:
        print(f"\\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
