import requests
from requests.auth import HTTPBasicAuth
import json

# Consultar el estado actual de la SIM
url = "https://ep.freeeway.com/services/portal/v1/simCards"
params = {
    "filters": json.dumps({"msisdn": "436761723367528"})
}
headers = {
    "Accept": "application/vnd.api+json"
}
auth = HTTPBasicAuth("gerencia@rastrear.com.co", "JNYf62vz3xN9S8m")

try:
    response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            sim = data['data'][0]
            attributes = sim.get('attributes', {})
            
            print("\n" + "="*80)
            print("ESTADO ACTUAL DE LA SIM")
            print("="*80)
            print(f"ICCID: {attributes.get('iccid')}")
            print(f"MSISDN: {attributes.get('msisdn')}")
            print(f"IMSI: {attributes.get('imsi')}")
            print(f"Billing Status: {attributes.get('billingStatus')}")
            print(f"PS: {attributes.get('ps')}")
            print(f"Data Session: {attributes.get('dataSession')}")
            print("="*80)
            
            # Mostrar JSON completo
            print("\nJSON completo:")
            print(json.dumps(data, indent=2))
        else:
            print("No se encontró la SIM")
            print(json.dumps(data, indent=2))
    else:
        print(f"\nError: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
