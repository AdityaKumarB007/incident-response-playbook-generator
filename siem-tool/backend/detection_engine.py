import uuid
from database import insert_incident

# State for Brute Force tracking
failed_logins = {}

def detect_attacks(parsed_logs):
    incidents = []
    
    for log in parsed_logs:
        ip = log['source_ip']
        params_original = str(log.get('parameters', ''))
        params_upper = params_original.upper()
        
        attack_detected = None
        severity = "LOW"
        evidence = ""
        
        # State tracking for DOS/DDOS
        global request_counts
        if 'request_counts' not in globals():
            request_counts = {}
            
        current_time_bucket = log['timestamp'][:16] # Group by minute for rate limiting
        ip_bucket = f"{ip}_{current_time_bucket}"
        
        request_counts[ip_bucket] = request_counts.get(ip_bucket, 0) + 1

        # 1. SQL Injection
        sqli_patterns = ["OR 1=1", "'--", "UNION SELECT", "' OR '1'='1", "1' OR '1'='1", "DROP TABLE", "SELECT IF"]
        if any(p in params_upper for p in sqli_patterns) and not attack_detected:
            attack_detected = "SQL Injection"
            severity = "HIGH"
            evidence = f"Matched SQLi pattern in parameters: {params_original}"
            
        # 2. XSS
        elif ("<script>" in params_original.lower() or "javascript:" in params_original.lower() or "onerror" in params_original.lower() or "<img src=x" in params_original.lower()) and not attack_detected:
            attack_detected = "XSS"
            severity = "MEDIUM"
            evidence = f"Matched XSS HTML/JS tag in parameters: {params_original}"
            
        # 3. Directory Traversal
        elif ("../" in params_original or "..\\" in params_original or "/etc/passwd" in params_original) and not attack_detected:
            attack_detected = "Directory Traversal"
            severity = "HIGH"
            evidence = f"Matched Directory Traversal pattern: {params_original}"
            
        # 4. Command Injection
        cmd_patterns = ["; ls", "| cat", "&&", ";ls", "|cat", "; cat", "$(whoami)", "`whoami`"]
        if any(p in params_original for p in cmd_patterns) and not attack_detected:
            attack_detected = "Command Injection"
            severity = "CRITICAL"
            evidence = f"Matched OS Command Injection pattern: {params_original}"
            
        # 5. Phishing / Open Redirect
        elif ("http://" in params_original or "https://" in params_original) and any(kw in params_original.lower() for kw in ["login", "verify", "secure", "update", "account"]) and not attack_detected:
            attack_detected = "Phishing / Open Redirect"
            severity = "HIGH"
            evidence = f"Detected external URL redirect containing suspicious keywords: {params_original}"

        # 6. Denial of Service (DoS) / DDoS
        elif request_counts[ip_bucket] > 50 and not attack_detected:
            attack_detected = "DDoS" if len([k for k in request_counts if current_time_bucket in k]) > 10 else "DoS"
            severity = "CRITICAL"
            evidence = f"Abnormal request volume detected ({request_counts[ip_bucket]} requests/min) from IP: {ip}"
            
        # 7. Generic Security Anomaly (Catch-all for suspicious payloads)
        elif len(params_original) > 500 and not attack_detected:
            attack_detected = "Buffer Overflow / Large Payload Anomaly"
            severity = "MEDIUM"
            evidence = f"Extremely large payload size ({len(params_original)} chars) detected on endpoint {log.get('endpoint')}"

        # 8. Brute Force Login
        if log.get('endpoint') == '/login' and log.get('status_code') in [401, 500] and not attack_detected:
            failed_logins[ip] = failed_logins.get(ip, 0) + 1
            if failed_logins[ip] >= 4:
                attack_detected = "Brute Force"
                severity = "HIGH"
                evidence = f"Detected 4 or more failed login attempts from IP: {ip}"
                failed_logins[ip] = 0 # reset counter after detection
        else:
            # If successful login, reset counter
            if log.get('endpoint') == '/login' and log.get('status_code') == 200:
                failed_logins[ip] = 0

        # Create Incident if attack found
        if attack_detected:
            incident = {
                'incident_id': str(uuid.uuid4()),
                'attack_type': attack_detected,
                'timestamp': log['timestamp'],
                'source_ip': ip,
                'endpoint': log['endpoint'],
                'severity': severity,
                'evidence': evidence
            }
            incidents.append(incident)
            insert_incident(incident)
            
    return incidents
