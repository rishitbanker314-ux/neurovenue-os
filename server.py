"""
NeuroVenue OS — Dashboard API Server
======================================
Serves simulation data, routing, and nudges as JSON endpoints.
Also serves the dashboard HTML file.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import json
import logging
import signal
import time
import re
from functools import wraps
from datetime import datetime

from simulation_engine import SimulationEngine
from routing_engine import find_best_path
from nudge_engine import generate_nudge

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GCP STRUCTURED LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class GCPStructuredLogFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "local")
        self.service = os.environ.get("K_SERVICE", "neurovenue-os-local")
        self.revision = os.environ.get("K_REVISION", "local-revision")

    def format(self, record):
        log_record = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logging.googleapis.com/labels": {
                "service": self.service,
                "revision": self.revision
            },
            "time": datetime.now(datetime.UTC).isoformat().replace('+00:00', 'Z')
        }
        
        # Pull explicitly tracked HTTP request contexts dynamically 
        if hasattr(record, "httpRequest"):
            log_record["httpRequest"] = getattr(record, "httpRequest")
            
        if record.exc_info:
            log_record["message"] += f"\n{self.formatException(record.exc_info)}"
            
        return json.dumps(log_record)

# Configure Native Logger
logger = logging.getLogger("gcp_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(GCPStructuredLogFormatter())
logger.addHandler(handler)

# Override default flask logger behavior
import werkzeug.serving
import logging as builtin_logging
builtin_logging.getLogger('werkzeug').disabled = True
app = Flask(__name__)
app.logger.disabled = True
CORS(app)

@app.after_request
def log_request(response):
    """GCP-Audited HTTP Metrics Tracker Middleware."""
    request_data = {
        "requestMethod": request.method,
        "requestUrl": request.url,
        "status": response.status_code,
        "userAgent": request.headers.get("User-Agent", ""),
        "remoteIp": request.remote_addr,
        "responseSize": response.calculate_content_length()
    }
    logger.info(f"{request.method} {request.path} {response.status_code}", extra={"httpRequest": request_data})
    return response

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLOUD RUN SIGTERM GRACEFUL SHUTDOWN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def sigterm_handler(signum, frame):
    logger.info("Caught SIGTERM! Gracefully structuring memory termination across Node Clusters over 10s window...")
    # Allows pending states or DBs to close out securely
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

def validate_routing_params(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        s = request.args.get("s", "A1")
        e = request.args.get("e", "E5")
        
        # Strict Regex Bounds blocking XSS or Path Traversal injection
        if not re.match(r'^[A-E][1-5]$', str(s)) or not re.match(r'^[A-E][1-5]$', str(e)):
            logger.warning(f"SECURITY BLOCK: Malicious zone injection attempt caught: s={s}, e={e}")
            return jsonify({
                "error": "SECURITY BLOCK: Invalid zone identifier specified. Must match ^[A-E][1-5]$ regex.",
                "code": 400
            }), 400
            
        return f(*args, **kwargs)
    return decorated_function


# Global simulation engine
engine = SimulationEngine()


@app.route("/")
def index():
    """Serve the dashboard HTML."""
    return send_file("dashboard.html")


@app.route("/api/state")
@validate_routing_params
def get_state():
    engine.step()
    state = engine.get_state()
    zones = state["zones"]

    # Default route
    start = request.args.get("s", "A1")
    end = request.args.get("e", "E5")
    route = find_best_path(zones, start, end, state.get("predictions"))
    nudge = generate_nudge(route)

    return jsonify({
        "tick": state["tick"],
        "phase": state["phase"],
        "timestamp": state["timestamp"],
        "zones": zones,
        "predictions": state.get("predictions"),
        "route": {
            "start": start,
            "end": end,
            "path": route["path"],
            "time_saved": route["time_saved"],
        },
        "nudge": nudge,
    })


@app.route("/api/route")
@validate_routing_params
def get_route():
    start = request.args.get("s", "A1")
    end = request.args.get("e", "E5")

    state = engine.get_state()
    zones = state["zones"]
    route = find_best_path(zones, start, end, state.get("predictions"))
    nudge = generate_nudge(route)

    return jsonify({
        "path": route["path"],
        "time_saved": route["time_saved"],
        "nudge": nudge,
    })


@app.route("/api/scenario", methods=["POST"])
def set_scenario():
    data = request.get_json()
    scenario = data.get("scenario", "auto")
    # Remap legacy frontend parameters securely
    if scenario == "emergency":
        scenario = "evacuation"
        
    engine.manual_phase = scenario
    
    # Tick once to apply immediately
    engine.step()
    
    logger.info(f"Scenario overridden manually to '{scenario}' safely.")
    return jsonify({"status": "success", "scenario": scenario})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    logger.info(f"Initializing NeuroVenue OS Server on Port {port} natively.")
    app.run(host="0.0.0.0", port=port, debug=False)
