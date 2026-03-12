import pymongo
from datetime import datetime

# Initialize MongoDB Connection
try:
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = mongo_client["siem_defense_db"]
    playbooks_collection = db["mitigation_playbooks"]
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    playbooks_collection = None

def generate_playbook(incident):
    attack_type = incident.get('attack_type', 'Unknown')
    target_endpoint = incident.get('endpoint', 'Unknown Server')
    malicious_ip = incident.get('source_ip', '0.0.0.0')

    timestamp = incident.get('timestamp', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    playbook_templates = {
        "SQL Injection": [
            "1. Attack Detection: On {TIMESTAMP}, the DefendX SIEM detected a critical SQL Injection (SQLi) attack originating from IP {IP} targeting the {ENDPOINT} endpoint. The detection engine flagged multiple suspicious HTTP payloads containing malicious SQL metacharacters (such as ' or UNION SELECT), indicating an active attempt to manipulate the backend database to exfiltrate sensitive records or bypass authentication.",
            "2. Immediate Containment: Immediately upon detection, the automated containment protocols were engaged by the SOC analyst. A strict drop rule was implemented at the Web Application Firewall (WAF) to null-route all incoming traffic from {IP}, successfully severing the attacker's connection and preventing further malicious queries from reaching the database.",
            "3. Eradication & Recovery: Following containment, the Incident Response team isolated the affected {ENDPOINT} route and purged any hung SQL queries from the database queue to restore performance. The application source code was quickly audited, and the vulnerability was eradicated by refactoring the backend to strictly use Parameterized Queries (Prepared Statements) for all database interactions, neutralizing any future SQL injection attempts.",
            "4. Post-Incident Analysis: Finally, a comprehensive database audit was conducted, reviewing all HTTP 200 responses sent to {IP} to verify that no sensitive tables were successfully dumped before containment. The incident was marked as resolved, and the SOC updated the global WAF signatures to proactively block similar SQL payloads."
        ],
        "XSS": [
            "1. Attack Detection: On {TIMESTAMP}, the SIEM triggered a high-priority alert for Cross-Site Scripting (XSS). The system detected malicious client-side JavaScript payloads being injected into the {ENDPOINT} parameter from the attacker IP {IP}. The objective was likely to execute unauthorized scripts in the browsers of legitimate users to steal session cookies or hijack accounts.",
            "2. Immediate Containment: The SOC analyst responded immediately by blocking {IP} at the network perimeter. To prevent lateral spread and protect users, the vulnerable {ENDPOINT} page was temporarily taken offline, and all active user sessions that recently interacted with the infected URL were forcibly revoked.",
            "3. Eradication & Recovery: The Incident Response team purged the injected malicious scripts directly from the database to clean the affected records. The application vulnerability was formally eradicated by enforcing strict Context-Aware HTML Output Encoding and sanitizing all user inputs through a secure framework before rendering data back to the client.",
            "4. Post-Incident Analysis: The team implemented a robust Content-Security-Policy (CSP) header across the domain to prevent inline scripts from executing in the future. Log analysis confirmed no admin session tokens were compromised, and the updated {ENDPOINT} was safely restored to production."
        ],
        "Command Injection": [
            "1. Attack Detection: On {TIMESTAMP}, a critical severity OS Command Injection attack was detected from {IP}. The SIEM identified shell metacharacters (such as ;, |, or &&) appended to legitimate web requests directed at {ENDPOINT}. This indicated a severe attempt to execute arbitrary system-level commands and potentially spawn a reverse shell on the host server.",
            "2. Immediate Containment: Due to the high risk of total system compromise, the SOC declared an emergency. The affected host server handling {ENDPOINT} was logically isolated from the internal network to prevent lateral movement. The attacker's IP {IP} was simultaneously null-routed across all internal routers and edge firewalls.",
            "3. Eradication & Recovery: The incident response team accessed the isolated machine and terminated all unauthorized bash, python, and netcat processes spawned by the web user. The filesystem was scrubbed for dropped webshells or persistence mechanisms. The application code was then patched to completely remove the use of unsafe system() calls in favor of secure, language-native APIs.",
            "4. Post-Incident Analysis: A thorough forensic review of the server's bash history and network connections confirmed the attacker failed to escalate privileges to root. The server was rebuilt from a clean image, the patched code was deployed, and strict endpoint detection and response (EDR) rules were implemented to flag unusual child processes."
        ],
        "Brute Force": [
            "1. Attack Detection: On {TIMESTAMP}, the DefendX correlation engine flagged a systemic Brute Force attack targeting the authentication gateway at {ENDPOINT}. The SIEM recorded an anomalous spike of failed login attempts originating from {IP}, pointing to an automated script attempting to guess employee passwords or utilize breached credential lists.",
            "2. Immediate Containment: The SOC team instantly deployed a hardware rate-limit and an IP-level block against {IP} at the perimeter. The targeted user accounts were temporarily locked down to prevent account takeover (ATO), and the CDN was securely placed into 'Under Attack' mode to challenge further automated bot traffic.",
            "3. Eradication & Recovery: The Incident Response team verified the integrity of the authentication service. To eradicate the threat vector, forced password resets were mandated for all targeted users. Furthermore, mandatory Multi-Factor Authentication (MFA) and strict progressive account lockout policies were structurally enforced on {ENDPOINT}.",
            "4. Post-Incident Analysis: A subsequent query of the SIEM logs confirmed that zero login attempts from {IP} resulted in a successful HTTP 200 response. The authentication perimeter was deemed secure, and the SOC implemented dynamic CAPTCHA challenges to deter future botnet activity."
        ],
        "Directory Traversal": [
            "1. Attack Detection: On {TIMESTAMP}, a Directory Traversal attempt was logged by the SIEM against {ENDPOINT}. The monitoring system detected relative file path sequences (such as ../../../etc/passwd) in the HTTP GET requests from {IP}. The attacker was attempting to break out of the web root directory to download highly sensitive OS configuration files.",
            "2. Immediate Containment: The SOC analyst immediately blocked {IP} across the network edge. The team actively restricted filesystem read permissions for the web server user on the host running {ENDPOINT}, ensuring the daemon could not access restricted directories even if the application logic failed.",
            "3. Eradication & Recovery: The engineering team eradicated the vulnerability by modifying the source code to entirely reject absolute path inputs. The endpoint was refactored to use safe direct object reference mapping (e.g., mapping an ID to a file) rather than passing raw file names, fundamentally neutralizing path traversal maneuvers.",
            "4. Post-Incident Analysis: A review of the data egress logs proved that the attacker received an HTTP 403 Forbidden on their traversal attempts and no sensitive files were successfully downloaded. Improved regex filtering for traversal encoding (like %2e%2e%2f) was deployed to the WAF."
        ],
        "DoS": [
            "1. Attack Detection: On {TIMESTAMP}, the SIEM detected a massive Denial of Service (DoS) attack originating from {IP}. The telemetry indicated an extreme volumetric spike in anomalous requests targeting {ENDPOINT}, causing server CPU and memory utilization to hit 99% and resulting in severe application latency and connection timeouts.",
            "2. Immediate Containment: The SOC commander initiated immediate containment procedures by pushing a strict TCP hardware rate-limit to the network edge, decisively dropping all inbound traffic from {IP}. Simultaneously, the cloud infrastructure was horizontally scaled up by the automated orchestration system to absorb the residual traffic spike and stabilize {ENDPOINT}.",
            "3. Eradication & Recovery: With the malicious IP null-routed, the Incident Response team restarted the hung backend services to clear the connection queue and restore normal operations. Aggressive Edge caching and rate-limiting rules were deployed around {ENDPOINT} to permanently relieve pressure on the backend application servers.",
            "4. Post-Incident Analysis: Monitoring systems confirmed that application stability was fully restored within 10 minutes of the attack. The SOC reviewed the traffic patterns to ensure it wasn't a smokescreen for data exfiltration. Automated Blackhole routing profiles were finalized to instantly mitigate future volumetric floods."
        ]
    }
    
    # Generate the formatted story
    raw_steps = playbook_templates.get(attack_type, playbook_templates["DoS"])
    
    # Inject intelligence into the string templates
    formatted_steps = []
    for step in raw_steps:
        formatted_steps.append(step.replace("{IP}", malicious_ip).replace("{ENDPOINT}", target_endpoint).replace("{TIMESTAMP}", timestamp))
    
    playbook_data = {
        "incident_id": incident.get("incident_id"),
        "attack_type": attack_type,
        "playbook_steps": formatted_steps,
        "recommended_action": "High Priority Review" if incident.get("severity") in ["HIGH", "CRITICAL"] else "Monitor Strategy"
    }
    
    # Store the generated playbook story into MongoDB for long term analytics/prevention memory
    if playbooks_collection is not None:
        try:
            mongo_doc = {
                "incident_id": playbook_data["incident_id"],
                "attack_type": playbook_data["attack_type"],
                "source_ip": malicious_ip,
                "target_endpoint": target_endpoint,
                "generated_playbook_story": formatted_steps,
                "created_at": datetime.utcnow()
            }
            playbooks_collection.insert_one(mongo_doc)
            print(f"[MongoDB] Successfully saved mitigation story for {playbook_data['incident_id']}")
        except Exception as e:
            print(f"[MongoDB Error] Could not save playbook: {e}")

    return playbook_data

