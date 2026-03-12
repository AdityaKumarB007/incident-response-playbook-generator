import sys
import os

# Make sure imports work properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import json
import csv
from io import StringIO

from database import init_db, get_all_incidents
from log_parser import parse_logs, parse_single_log
from detection_engine import detect_attacks
from playbook_generator import generate_playbook

app = Flask(__name__)
# Enable CORS so our frontend can make requests if served on a different port
CORS(app)

@app.route('/api/init', methods=['POST'])
def initialize_system():
    init_db()
    
    # Process logs and populate database with dummy data
    logs = parse_logs()
    incidents = detect_attacks(logs)
    
    return jsonify({
        "status": "success",
        "message": f"System initialized. Detected {len(incidents)} incidents from logs."
    })

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    incidents = get_all_incidents()
    return jsonify({
        "status": "success",
        "data": incidents
    })

BLOCKED_IPS = set()

@app.route('/api/mitigate', methods=['POST'])
def mitigate_ip():
    data = request.json
    if data and data.get("action") == "block_ip" and data.get("ip"):
        BLOCKED_IPS.add(data.get("ip"))
        return jsonify({"status": "success", "message": f"IP {data.get('ip')} successfully blocked at firewall."})
    return jsonify({"status": "error", "message": "Invalid request"}), 400

@app.route('/api/ingest', methods=['POST'])
def ingest_log():
    log_data = request.json
    if not log_data:
        return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
        
    source_ip = log_data.get("ip")
    if source_ip in BLOCKED_IPS:
        return jsonify({"status": "error", "message": "WAF drop: IP is blocked."}), 403
    
    parsed_log = parse_single_log(log_data)
    incidents = detect_attacks([parsed_log])
    
    return jsonify({
        "status": "success",
        "message": "Log ingested",
        "attack_detected": len(incidents) > 0,
        "incident": incidents[0] if incidents else None
    })

@app.route('/api/playbook/<incident_id>', methods=['GET'])
def get_playbook(incident_id):
    incidents = get_all_incidents()
    incident = next((i for i in incidents if i['incident_id'] == incident_id), None)
    
    if incident:
        playbook = generate_playbook(incident)
        return jsonify({
            "status": "success",
            "data": playbook,
            "incident": incident
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Incident not found"
        }), 404

@app.route('/api/export/csv', methods=['GET'])
def export_report_csv():
    incidents = get_all_incidents()
    si = StringIO()
    if incidents:
        writer = csv.DictWriter(si, fieldnames=incidents[0].keys())
        writer.writeheader()
        writer.writerows(incidents)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=incidents_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/api/export/json', methods=['GET'])
def export_report_json():
    incidents = get_all_incidents()
    output = make_response(jsonify(incidents))
    output.headers["Content-Disposition"] = "attachment; filename=incidents_report.json"
    output.headers["Content-type"] = "application/json"
    return output

@app.route('/api/templates', methods=['GET'])
def get_templates():
    try:
        import pymongo
        mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = mongo_client["siem_defense_db"]
        playbooks_collection = db["mitigation_playbooks"]
        
        # Get all playbooks, sort by newest first
        templates = list(playbooks_collection.find({}, {"_id": 0}).sort("created_at", -1))
        return jsonify({
            "status": "success",
            "data": templates
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend'))

@app.route('/ping')
def ping():
    return "PONG"

# Serve Frontend
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_frontend_assets(path):
    return send_from_directory(FRONTEND_DIR, path)

if __name__ == '__main__':
    # Initialize DB upon starting
    init_db()
    # Process attacks ahead of time for demo purposes
    logs = parse_logs()
    detect_attacks(logs)
    print("SIEM Backend Server executing on port 5001...")
    app.run(debug=True, port=5001)
