import os
import json
import csv
from fpdf import FPDF

# Output Folder Configuration
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../reports/playbooks/')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 4. Playbook Generation Templates
playbook_templates = {
    "SQL Injection": [
        "Identify the vulnerable endpoint",
        "Check database query logs",
        "Block attacker IP address",
        "Use parameterized queries",
        "Implement input validation",
        "Deploy Web Application Firewall rule",
        "Monitor for repeated attacks"
    ],
    "XSS": [
        "Identify vulnerable input fields",
        "Sanitize user input",
        "Implement output encoding",
        "Apply Content Security Policy",
        "Patch frontend validation",
        "Block attacker IP"
    ],
    "Brute Force": [
        "Identify login endpoint",
        "Check authentication logs",
        "Enable account lockout",
        "Enable rate limiting",
        "Enable multi-factor authentication",
        "Block attacker IP"
    ],
    "Directory Traversal": [
        "Check file access logs",
        "Validate file paths",
        "Restrict directory permissions",
        "Implement allow-listing",
        "Patch vulnerable endpoints"
    ],
    "Command Injection": [
        "Identify vulnerable command execution",
        "Sanitize user inputs",
        "Use safe APIs instead of shell commands",
        "Restrict system permissions",
        "Block attacker IP"
    ]
}

def generate_playbook_steps(attack_type):
    """Returns the steps for a given attack type, or a default list if unknown."""
    return playbook_templates.get(attack_type, [
        "Investigate logs", 
        "Quarantine affected system", 
        "Block malicious IP",
        "Patch resulting vulnerability"
    ])

def export_playbook_pdf(incident):
    """
    Generate and export the incident response playbook as a professionally formatted PDF.
    """
    inci_id = incident.get("incident_id", "UNKNOWN")
    attack_type = incident.get("attack_type", "Unknown Attack")
    source_ip = incident.get("source_ip", "0.0.0.0")
    timestamp = incident.get("timestamp", "N/A")
    endpoint = incident.get("endpoint", "N/A")
    severity = incident.get("severity", "Medium")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)

    # Title
    pdf.cell(200, 10, txt="Incident Response Playbook", ln=True, align='C')
    pdf.ln(10)

    # Section: Incident Details
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Incident Details", ln=True)
    pdf.set_font("Arial", '', 12)
    
    details = [
        ("Incident ID", str(inci_id)),
        ("Attack Type", str(attack_type)),
        ("Timestamp", str(timestamp)),
        ("Source IP", str(source_ip)),
        ("Endpoint", str(endpoint)),
        ("Severity", str(severity))
    ]
    
    for key, val in details:
        pdf.cell(40, 8, txt=f"{key}:")
        pdf.cell(150, 8, txt=val, ln=True)
        
    pdf.ln(10)

    # Section: Response Playbook
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Response Steps:", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", '', 12)

    steps = generate_playbook_steps(attack_type)
    for step in steps:
        pdf.cell(10, 8, txt="[ ]")
        pdf.cell(180, 8, txt=step, ln=True)

    # File Naming
    filename = f"playbook_{inci_id}.pdf"
    file_path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(file_path)
    
    print(f"[+] PDF Exported successfully to: {file_path}")
    return file_path

# ==========================================
# Bonus Feature (Optional): Export JSON/CSV
# ==========================================

def export_playbook_json(incident, filepath=None):
    """Export the playbook out as a structured JSON file."""
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, f"playbook_{incident.get('incident_id', 'Unknown')}.json")
    
    data = {
        "Incident Details": incident,
        "Response Playbook": generate_playbook_steps(incident.get("attack_type"))
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[+] JSON Exported successfully to: {filepath}")
    return filepath

def export_playbook_csv(incident, filepath=None):
    """Export the playbook out as a CSV security checklist."""
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, f"playbook_{incident.get('incident_id', 'Unknown')}.csv")
    
    with open(filepath, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Field", "Value"])
        for k, v in incident.items():
            writer.writerow([k, v])
        
        writer.writerow([])
        writer.writerow(["Checklist", "Status"])
        for step in generate_playbook_steps(incident.get("attack_type")):
            writer.writerow([step, "Pending"])
            
    print(f"[+] CSV Exported successfully to: {filepath}")
    return filepath

if __name__ == "__main__":
    # Example execution code to immediately test the script
    print("Simulating incident playbook generation...")
    
    sample_incident = {
        "incident_id": "INC-001",
        "attack_type": "SQL Injection",
        "source_ip": "192.168.1.5",
        "endpoint": "/login",
        "timestamp": "2026-03-12 18:30",
        "severity": "High"
    }
    
    export_playbook_pdf(sample_incident)
    export_playbook_json(sample_incident)
    export_playbook_csv(sample_incident)

