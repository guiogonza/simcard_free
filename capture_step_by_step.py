"""
Script de captura paso a paso con análisis en tiempo real
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Configuración
FREEEWAY_URL = "https://ep.freeeway.com"
LOGIN_EMAIL = "gerencia@rastrear.com.co"
LOGIN_PASSWORD = "JNYf62vz3xN9S8m"

def setup_driver():
    """Configura el driver de Chrome"""
    print("Configurando Chrome driver...")
    
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
    
    options = Options()
    options.add_argument('--window-size=1920,1080')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    return driver

def analyze_logs(driver, step_name):
    """Analiza los logs y muestra peticiones relevantes"""
    print(f"\n{'='*80}")
    print(f"ANALIZANDO PETICIONES - {step_name}")
    print("="*80)
    
    try:
        logs = driver.get_log('performance')
        print(f"Total de logs desde el inicio: {len(logs)}")
        
        api_requests = []
        all_post_requests = []
        
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                if method == 'Network.requestWillBeSent':
                    request = message.get('message', {}).get('params', {}).get('request', {})
                    url = request.get('url', '')
                    req_method = request.get('method', '')
                    
                    # Capturar TODOS los POST, PATCH, PUT, DELETE
                    if req_method in ['PATCH', 'POST', 'PUT', 'DELETE']:
                        post_data = request.get('postData', '')
                        
                        all_post_requests.append({
                            'method': req_method,
                            'url': url,
                            'postData': post_data
                        })
                        
                        # Filtrar los relevantes
                        if any(keyword in url.lower() for keyword in ['simcard', 'billing', 'status', 'portal', 'services']):
                            api_requests.append({
                                'method': req_method,
                                'url': url,
                                'headers': request.get('headers', {}),
                                'postData': post_data
                            })
            except:
                continue
        
        print(f"\nPeticiones POST/PUT/PATCH/DELETE totales: {len(all_post_requests)}")
        print(f"Peticiones API relevantes: {len(api_requests)}\n")
        
        if all_post_requests:
            print("ÚLTIMAS 10 PETICIONES POST/PUT/PATCH/DELETE:")
            for i, req in enumerate(all_post_requests[-10:], 1):
                print(f"\n  {i}. {req['method']} {req['url']}")
                if req['postData']:
                    print(f"     Payload: {req['postData'][:150]}{'...' if len(req['postData']) > 150 else ''}")
        
        if api_requests:
            print(f"\n{'='*80}")
            print("PETICIONES API RELEVANTES DETECTADAS:")
            print("="*80)
            
            for i, req in enumerate(api_requests, 1):
                print(f"\n--- PETICIÓN #{i} ---")
                print(f"Método: {req['method']}")
                print(f"URL: {req['url']}")
                
                if req.get('postData'):
                    print(f"Payload:")
                    try:
                        payload_json = json.loads(req['postData'])
                        print(json.dumps(payload_json, indent=2))
                    except:
                        print(req['postData'])
            
            # Guardar
            with open(f'captured_{step_name.replace(" ", "_").lower()}.json', 'w', encoding='utf-8') as f:
                json.dump(api_requests, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Guardado en: captured_{step_name.replace(' ', '_').lower()}.json")
        else:
            print("\n⚠ No se detectaron peticiones API relevantes en este paso")
        
        return api_requests
        
    except Exception as e:
        print(f"Error analizando logs: {e}")
        return []

def login(driver):
    """Login automático"""
    print(f"\n{'='*80}")
    print("PASO 1: LOGIN AUTOMÁTICO")
    print("="*80)
    
    print(f"Navegando a {FREEEWAY_URL}...")
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
            
            # Analizar peticiones del login
            analyze_logs(driver, "LOGIN")
            
            return True
        else:
            print("✗ No se encontraron campos de login")
            return False
    except Exception as e:
        print(f"Error en login: {e}")
        return False

def main():
    """Función principal"""
    print("="*80)
    print("SCRIPT DE CAPTURA PASO A PASO - FREEEWAY")
    print("="*80)
    
    driver = None
    
    try:
        # Setup
        driver = setup_driver()
        
        # PASO 1: Login automático
        if not login(driver):
            print("\n✗ Fallo en login")
            return
        
        # PASO 2: Usuario hace clic en SIM Cards
        print(f"\n{'='*80}")
        print("PASO 2: CLIC EN SIM CARDS")
        print("="*80)
        print("Ahora TÚ haces clic en el menú 'SIM Cards' en el navegador")
        print("Espera a que cargue la tabla completa (verás '700 SIM Cards found')")
        print("")
        input("Cuando hayas hecho clic y la tabla esté cargada, presiona Enter >>> ")
        
        # Esperar un poco más para asegurar que todas las peticiones se completaron
        time.sleep(3)
        
        # Analizar peticiones
        analyze_logs(driver, "SIM_CARDS_MENU")
        
        # PASO 3: Búsqueda
        print(f"\n{'='*80}")
        print("PASO 3: BÚSQUEDA DE SIM")
        print("="*80)
        print("Ahora busca la SIM card:")
        print("  1. En 'Search: Any text' ingresa: 436761723367528")
        print("  2. Haz clic en el botón de búsqueda o presiona Enter")
        print("  3. Espera a ver los resultados")
        print("")
        input("Cuando veas los resultados de búsqueda, presiona Enter >>> ")
        
        time.sleep(2)
        analyze_logs(driver, "SEARCH")
        
        # PASO 4: Seleccionar checkbox
        print(f"\n{'='*80}")
        print("PASO 4: SELECCIONAR SIM")
        print("="*80)
        print("Marca el checkbox de la SIM card")
        print("")
        input("Cuando hayas marcado el checkbox, presiona Enter >>> ")
        
        time.sleep(2)
        analyze_logs(driver, "SELECT_CHECKBOX")
        
        # PASO 5: Hacer clic en Change Billing Status
        print(f"\n{'='*80}")
        print("PASO 5: ABRIR MODAL DE CAMBIO DE ESTADO")
        print("="*80)
        print("Haz clic en el 4to icono (Change Billing Status)")
        print("")
        input("Cuando veas el modal abierto, presiona Enter >>> ")
        
        time.sleep(2)
        analyze_logs(driver, "OPEN_MODAL")
        
        # PASO 6: Cambiar estado
        print(f"\n{'='*80}")
        print("PASO 6: CONFIRMAR CAMBIO DE ESTADO")
        print("="*80)
        print("Realiza estos pasos:")
        print("  1. Selecciona el radio button 'Resume' (para volver a activarla)")
        print("  2. Haz clic en el botón 'Change'")
        print("  3. Espera a que el modal se cierre")
        print("")
        input("Cuando el cambio esté completo y el modal cerrado, presiona Enter >>> ")
        
        time.sleep(3)
        api_requests = analyze_logs(driver, "CHANGE_STATUS")
        
        # Resumen final
        print(f"\n{'='*80}")
        print("RESUMEN FINAL")
        print("="*80)
        
        all_files = [
            'captured_login.json',
            'captured_sim_cards_menu.json',
            'captured_search.json',
            'captured_select_checkbox.json',
            'captured_open_modal.json',
            'captured_change_status.json'
        ]
        
        print("\nArchivos generados:")
        for filename in all_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    print(f"  ✓ {filename} - {len(data)} peticiones")
            except:
                print(f"  - {filename} - no generado")
        
        if api_requests:
            print(f"\n✓ ¡Petición de cambio de estado capturada!")
            print("  Revisa el archivo: captured_change_status.json")
        else:
            print(f"\n⚠ No se capturaron peticiones en el cambio de estado")
            print("  Revisa los otros archivos para ver si se capturó en otro paso")
        
        print("\n" + "="*80)
        input("Presiona Enter para cerrar el navegador >>> ")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
