import requests
import datetime
import json
from flask import Flask, request, render_template_string

app = Flask(__name__)

# The endpoint where our SIEM is listening for logs
SIEM_INGEST_URL = "http://127.0.0.1:5001/api/ingest"

# Basic HTML template for the vulnerable login page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Employee Portal - Login</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; }
        h2 { text-align: center; color: #333; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #666; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #0056b3; }
        .warning { color: red; font-size: 12px; margin-top: 10px; text-align: center;}
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Corporate Portal</h2>
        <form action="/steal" method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        {% if message %}
        <p class="warning">{{ message }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

def send_log_to_siem(endpoint, method, status_code, params):
    """Helper formatting HTTP Request logs mimicking a real web server to pipe over to the SIEM."""
    # Capture standard web request elements
    attacker_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_payload = {
        "ip": attacker_ip,
        "method": method,
        "endpoint": endpoint,
        "parameters": params,
        "status_code": status_code,
        "user_agent": user_agent,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    try:
        # POST the parsed HTTP information covertly to SIEM Log Collector
        requests.post(SIEM_INGEST_URL, json=log_payload, timeout=2)
    except Exception as e:
        print(f"[!] Warning: Could not reach SIEM at {SIEM_INGEST_URL} - {e}")


@app.route('/login', methods=['GET'])
def login_page():
    # Send a log representing that someone accessed the GET endpoint
    send_log_to_siem("/login", "GET", 200, {})
    return render_template_string(HTML_TEMPLATE, message="")

@app.route('/steal', methods=['POST'])
def steal():
    # Vulnerable implementation capturing parameters blindly
    user = request.form.get('username', '')
    pwd = request.form.get('password', '')
    
    print(f"Captured Creds: {user} | {pwd}")
    
    # Check if this simulates an SQL Injection based purely on the password content
    if "'" in pwd or "OR" in pwd.upper():
        simulated_status = 500  # Database query broke violently
    else:
        simulated_status = 401  # Normal bad password
        
    # Forward the LIVE log directly to the SIEM Backend so it shows up in real-time
    send_log_to_siem("/login", "POST", simulated_status, {"username": user, "password": pwd})
    
    return render_template_string(HTML_TEMPLATE, message="Login failed. Invalid Credentials.")

if __name__ == "__main__":
    print("==================================================")
    print(" Starting Dummy Vulnerable Web App on port 5000 ")
    print(" WARNING: Do NOT deploy this on the public internet ")
    print("==================================================")
    
    # Run slightly separated from SIEM which is on 5001
    app.run(port=5002, debug=True)
