import requests
import datetime
import random
import sys

URL = "http://127.0.0.1:5001/api/ingest"

print("==================================================")
print("     INTERACTIVE LOGIN ATTACK SIMULATOR  ")
print("==================================================")
print("Type 'exit' or 'quit' as username to stop.\n")

# Assign a random IP for this session to simulate a single attacker 
session_ip = f"{random.randint(10,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
print(f"[*] Your Assigned Attacker IP: {session_ip}\n")

while True:
    try:
        username = input("Username: ")
        if username.lower() in ['exit', 'quit']:
            print("Exiting simulator...")
            break
            
        password = input("Password: ")
        
        # Build the payload mimicking a Flask/Web app log
        attack_payload = {
            "ip": session_ip,
            "method": "POST",
            "endpoint": "/login",
            "parameters": {
                "username": username,
                "password": password
            },
            # Simulate a 401 Unauthorized for most bad logins, 
            # unless the password contains typical SQL injection markers (just for fun simulation)
            "status_code": 500 if "'" in password or "OR" in password.upper() else 401,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Attack-Simulator",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        print("\n[+] Sending payload to SIEM...")
        response = requests.post(URL, json=attack_payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("attack_detected"):
                incident = result.get("incident")
                print(f"  🚨 [SIEM ALERT] Detected: {incident.get('attack_type')} | Severity: {incident.get('severity')}")
                if incident.get('attack_type') == "Brute Force":
                    print("  💡 (You triggered the 3-fail brute force threshold!)")
            else:
                print("  ❌ [SILENT] The SIEM processed the log but did not trigger an alert.")
        elif response.status_code == 403:
            print(f"  🛑 [BLOCKED] The SIEM WAF actively dropped your attack! Your IP ({session_ip}) is banned.")
        else:
            print(f"  ⚠️ Error from API: {response.status_code} - {response.text}")
            
        print("-" * 50)
            
    except KeyboardInterrupt:
        print("\nExiting simulator...")
        break
    except Exception as e:
        print(f"\n[!] Network Error: Could not reach SIEM at {URL}\nDetails: {e}")
        break

