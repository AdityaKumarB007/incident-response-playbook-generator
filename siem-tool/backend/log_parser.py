import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, '../data/logs.json')

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def parse_single_log(log):
    ip = log.get('ip', '0.0.0.0')
    endpoint = log.get('endpoint', '/')
    method = log.get('method', 'GET')
    params = log.get('parameters', {})
    timestamp = log.get('timestamp', '')
    status = log.get('status_code', 200)
    user_agent = log.get('user_agent', 'Unknown')
    
    return {
        'source_ip': ip,
        'method': method,
        'endpoint': endpoint,
        'parameters': params,
        'timestamp': timestamp,
        'status_code': status,
        'user_agent': user_agent,
        'raw_data': json.dumps(log) # Keep for evidence
    }

def parse_logs():
    logs = load_logs()
    parsed_logs = []
    for log in logs:
        parsed_logs.append(parse_single_log(log))
    return parsed_logs

