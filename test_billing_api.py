#!/usr/bin/env python3
"""
Script para descubrir el formato correcto de la API de Freeeway
para cambiar el billing status de una SIM card.
"""

import requests
from requests.auth import HTTPBasicAuth
import json

# Configuración
BASE_URL = "https://ep.freeeway.com/services/portal/v1"
USERNAME = "gerencia@rastrear.com.co"
PASSWORD = "JNYf62vz3xN9S8m"
SIM_ID = "143306"  # 89430301722110310016
ICCID = "89430301722110310016"

def test_endpoint_variations():
    """Prueba diferentes variaciones del endpoint y método HTTP"""
    
    session = requests.Session()
    session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    # Diferentes endpoints posibles
    endpoints = [
        f"/simCard/{SIM_ID}/billingStatus",
        f"/simCard/{SIM_ID}/billing-status",
        f"/simCard/{SIM_ID}/status",
        f"/simCard/{SIM_ID}",
        f"/simCards/{SIM_ID}/billingStatus",
    ]
    
    # Diferentes payloads
    payloads = [
        # Formato 1: Simple
        {
            "operation": "Suspend",
            "executionType": "Permanent"
        },
        # Formato 2: Con billingStatus key
        {
            "billingStatus": "Suspend"
        },
        # Formato 3: JSON:API con data
        {
            "data": {
                "type": "BillingStatusChange",
                "attributes": {
                    "operation": "Suspend",
                    "executionType": "Permanent"
                }
            }
        },
        # Formato 4: JSON:API completo
        {
            "data": {
                "type": "simCard",
                "id": SIM_ID,
                "attributes": {
                    "billingStatus": "Suspend"
                }
            }
        },
        # Formato 5: Action based
        {
            "action": "suspend",
            "type": "permanent"
        },
    ]
    
    # Diferentes Content-Types
    content_types = [
        "application/vnd.api+json",
        "application/json",
    ]
    
    # Métodos HTTP
    methods = ["PATCH", "POST", "PUT"]
    
    print("=" * 80)
    print("PROBANDO DIFERENTES COMBINACIONES DE ENDPOINT, PAYLOAD Y MÉTODO")
    print("=" * 80)
    
    for endpoint in endpoints:
        url = BASE_URL + endpoint
        print(f"\n{'='*80}")
        print(f"ENDPOINT: {endpoint}")
        print(f"{'='*80}")
        
        for method in methods:
            for content_type in content_types:
                for idx, payload in enumerate(payloads, 1):
                    headers = {
                        "Content-Type": content_type,
                        "Accept": content_type
                    }
                    
                    try:
                        print(f"\n[{method}] Payload #{idx} | Content-Type: {content_type}")
                        print(f"Payload: {json.dumps(payload, indent=2)}")
                        
                        if method == "PATCH":
                            response = session.patch(url, json=payload, headers=headers, timeout=10)
                        elif method == "POST":
                            response = session.post(url, json=payload, headers=headers, timeout=10)
                        elif method == "PUT":
                            response = session.put(url, json=payload, headers=headers, timeout=10)
                        
                        print(f"[OK] Status: {response.status_code}")
                        
                        if response.status_code in [200, 201, 202, 204]:
                            print(f"[EXITO] Codigo: {response.status_code}")
                            print(f"Respuesta: {response.text[:500]}")
                            print("\n" + "="*80)
                            print("CONFIGURACION EXITOSA:")
                            print(f"  Metodo: {method}")
                            print(f"  Endpoint: {endpoint}")
                            print(f"  Content-Type: {content_type}")
                            print(f"  Payload: {json.dumps(payload, indent=2)}")
                            print("="*80)
                            return True
                        else:
                            print(f"[ERROR] Error: {response.status_code} - {response.reason}")
                            if response.text:
                                try:
                                    error_data = response.json()
                                    print(f"Detalles: {json.dumps(error_data, indent=2)[:300]}")
                                except:
                                    print(f"Respuesta: {response.text[:200]}")
                    
                    except Exception as e:
                        print(f"[EXCEPCION] Excepcion: {str(e)}")
    
    return False

def check_sim_current_status():
    """Verifica el estado actual de la SIM"""
    session = requests.Session()
    session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    url = f"{BASE_URL}/simCard/{SIM_ID}?include=sessionInfo"
    headers = {
        "Accept": "application/vnd.api+json"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("\n" + "="*80)
            print("ESTADO ACTUAL DE LA SIM")
            print("="*80)
            print(json.dumps(data, indent=2)[:1000])
            print("\n")
            
            # Buscar campos relacionados con billing
            if "data" in data and "attributes" in data["data"]:
                attrs = data["data"]["attributes"]
                for key, value in attrs.items():
                    if "billing" in key.lower() or "status" in key.lower():
                        print(f"  {key}: {value}")
        else:
            print(f"Error al obtener estado: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("\nVerificando estado actual de la SIM...")
    check_sim_current_status()
    
    print("\n\nIniciando pruebas de API para cambio de billing status...")
    success = test_endpoint_variations()
    
    if not success:
        print("\nNo se encontro una combinacion exitosa.")
        print("\nRecomendaciones:")
        print("  1. Verifica en la consola web de Freeeway usando DevTools")
        print("  2. Consulta la documentacion oficial de la API")
        print("  3. Contacta al soporte tecnico de Freeeway/Kontigo")
