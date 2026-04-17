"""
NeuroVenue OS — Dashboard API Server
======================================
Serves simulation data, routing, and nudges as JSON endpoints.
Also serves the dashboard HTML file.

Cloud Services:
  - Google Cloud Logging  → structured log ingestion (real API calls)
  - Google Cloud Firestore → simulation run persistence across sessions
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import logging
import signal
import re
from functools import wraps

from simulation_engine import SimulationEngine
from routing_engine import find_best_path
from nudge_engine import generate_nudge
import gcp_services

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLOUD LOGGING — initialize once at startup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# This attaches google-cloud-logging to the Python root logger and returns
# a named NeuroVenue logger. All subsequent logging.getLogger() calls in
# this process are automatically captured and shipped to Cloud Logging.
logger = gcp_services.get_logger()

# Silence noisy Werkzeug access log (we emit structured per-request logs below)
logging.getLogger("werkzeug").disabled = True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FLASK APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = Flask(__name__)
app.logger.disabled = True
CORS(app)


@app.after_request
def log_request(response):
    """Emit a structured HTTP request log entry to Cloud Logging."""
    logger.info(
        f"{request.method} {request.path} {response.status_code}",
        extra={
            "json_fields": {
                "httpRequest": {
                    "requestMethod": request.method,
                    "requestUrl": request.url,
                    "status": response.status_code,
                    "userAgent": request.headers.get("User-Agent", ""),
                    "remoteIp": request.remote_addr,
                    "responseSize": response.calculate_content_length(),
                },
                "service": os.environ.get("K_SERVICE", "neurovenue-os-local"),
            }
        },
    )
    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLOUD RUN SIGTERM GRACEFUL SHUTDOWN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def sigterm_handler(signum, frame):
    logger.info(
        "Caught SIGTERM — graceful shutdown initiated",
        extra={"json_fields": {"event": "sigterm", "service": "neurovenue-os"}},
    )
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INPUT VALIDATION MIDDLEWARE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def validate_routing_params(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        s = request.args.get("s", "A1")
        e = request.args.get("e", "E5")

        # Strict regex — blocks XSS and path traversal
        if not re.match(r"^[A-E][1-5]$", str(s)) or not re.match(r"^[A-E][1-5]$", str(e)):
            logger.warning(
                f"SECURITY BLOCK: Malicious zone injection caught: s={s}, e={e}",
                extra={
                    "json_fields": {
                        "event": "security_block",
                        "reason": "invalid_zone_id",
                        "s": str(s),
                        "e": str(e),
                    }
                },
            )
            return jsonify(
                {
                    "error": "SECURITY BLOCK: Invalid zone identifier. Must match ^[A-E][1-5]$.",
                    "code": 400,
                }
            ), 400

        return f(*args, **kwargs)

    return decorated_function


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL SIMULATION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL SIMULATION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
engine = SimulationEngine()

# --- Recommendation Engine Cache ---
last_recommendation = {
    "action": "Analyzing venue topology and flow rates...",
    "explanation": "Initializing shadow model evaluation constraints.",
    "factors": ["Building spatial node graphs"],
    "confidence": 0
}
last_eval_tick = -10  # Evaluate immediately on first tick

logger.info(
    "SimulationEngine initialized",
    extra={
        "json_fields": {
            "event": "engine_init",
            "agents": len(engine.agents),
            "zones": len(engine.zones_list),
        }
    },
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route("/")
def index():
    """Serve the dashboard HTML."""
    return send_file("dashboard.html")


@app.route("/api/state")
@validate_routing_params
def get_state():
    """Step the simulation and return full state.
    
    Every FIRESTORE_PERSIST_EVERY_N_TICKS ticks (default: 10), the
    snapshot is asynchronously persisted to Firestore and a structured
    log entry is written to Cloud Logging.
    """
    engine.step()
    state = engine.get_state()
    zones = state["zones"]

    start = request.args.get("s", "A1")
    end = request.args.get("e", "E5")
    route = find_best_path(zones, start, end, state.get("predictions"))
    
    global last_recommendation, last_eval_tick
    if state["tick"] - last_eval_tick >= 10:
        last_recommendation = engine.analyze_recommendations()
        last_eval_tick = state["tick"]

    nudge = last_recommendation

    route_context = {
        "start": start,
        "end": end,
        "path": route["path"],
        "time_saved": route["time_saved"],
    }

    # Persist to Firestore + emit structured log (fire-and-forget thread)
    gcp_services.log_simulation_run(
        tick=state["tick"],
        phase=state["phase"],
        zones=zones,
        predictions=state.get("predictions"),
        route=route_context,
    )

    return jsonify(
        {
            "tick": state["tick"],
            "phase": state["phase"],
            "timestamp": state["timestamp"],
            "zones": zones,
            "predictions": state.get("predictions"),
            "route": route_context,
            "nudge": nudge,
        }
    )


@app.route("/api/route")
@validate_routing_params
def get_route():
    """Return the current optimal route without advancing the simulation tick."""
    start = request.args.get("s", "A1")
    end = request.args.get("e", "E5")

    state = engine.get_state()
    zones = state["zones"]
    route = find_best_path(zones, start, end, state.get("predictions"))
    nudge = last_recommendation

    return jsonify(
        {
            "path": route["path"],
            "time_saved": route["time_saved"],
            "nudge": nudge,
        }
    )


@app.route("/api/scenario", methods=["POST"])
def set_scenario():
    """Override the active simulation scenario phase."""
    data = request.get_json()
    scenario = data.get("scenario", "auto")

    # Remap legacy frontend parameters securely
    if scenario == "emergency":
        scenario = "evacuation"

    engine.manual_phase = scenario
    engine.step()

    logger.info(
        f"Scenario manually overridden to '{scenario}'",
        extra={
            "json_fields": {
                "event": "scenario_override",
                "scenario": scenario,
            }
        },
    )
    return jsonify({"status": "success", "scenario": scenario})


@app.route("/api/command", methods=["POST"])
def handle_ai_command():
    """Translate natural language text into direct engine execution."""
    data = request.get_json() or {}
    cmd = data.get("command", "").lower().strip()
    
    if not cmd:
        return jsonify({"status": "ignored", "action": "Empty command parameter", "numeric_impact": "None"})

    # Parse specific intents
    if "close gate" in cmd:
        # Expecting e.g. "close gate b"
        try:
            gate_id = cmd.split("close gate")[1].strip()[0].upper()
            success = engine.close_gate(gate_id)
            if success:
                logger.info(f"AI Command executed: Closed Gate {gate_id}")
                return jsonify({
                    "status": "executed", 
                    "action": f"Secured Gate {gate_id} from general routing", 
                    "numeric_impact": "-12.5% egress capacity"
                })
            else:
                return jsonify({"status": "failed", "action": f"Gate {gate_id} invalid or already closed", "numeric_impact": "None"})
        except Exception:
            return jsonify({"status": "failed", "action": "Failed to parse gate identifier", "numeric_impact": "None"})

    elif "simulate emergency evacuation" in cmd or "evacuate" in cmd:
        engine.manual_phase = "evacuation"
        engine.step()
        logger.warning("AI Command executed: Emergency Evacuation Triggered")
        return jsonify({
            "status": "executed",
            "action": "Triggered Emergency Evacuation Protocol",
            "numeric_impact": "+100% directional flow pressure"
        })

    elif "increase crowd density" in cmd or "increase density" in cmd:
        count = 100 # Add 100 agents (~20% increase over the base 500)
        engine.add_agents(count)
        logger.info("AI Command executed: Dynamically injected +100 agents")
        return jsonify({
            "status": "executed",
            "action": f"Injected {count} spectator entities into venue",
            "numeric_impact": f"+{count} Live Agents"
        })

    else:
        logger.info(f"AI Command ignored (unrecognized): {cmd}")
        return jsonify({
            "status": "unrecognized",
            "action": "Unrecognized operation syntax (avoid chatbot dialogue).",
            "numeric_impact": "None"
        })

@app.route("/api/whatif", methods=["POST"])
def handle_what_if():
    """Run a parallel Ghost Simulation to compute What-If deltas."""
    data = request.get_json() or {}
    crowd_delta = int(data.get("crowd_delta", 0))
    close_gates = data.get("close_gates", [])
    phase = data.get("phase", "auto")
    
    # 1. Baseline: Run Ghost forward with NO changes for 20 ticks.
    baseline_metrics = engine.run_what_if_scenario(crowd_delta=0, close_gates=[], phase="auto", ticks=20)
    
    # 2. Scenario: Run Ghost forward WITH changes for 20 ticks.
    scenario_metrics = engine.run_what_if_scenario(crowd_delta=crowd_delta, close_gates=close_gates, phase=phase, ticks=20)
    
    # Calculate deltas
    delta = {
        "peak_congestion_diff": round(scenario_metrics["peak_congestion"] - baseline_metrics["peak_congestion"], 1),
        "avg_wait_diff": round(scenario_metrics["avg_wait"] - baseline_metrics["avg_wait"], 1),
        "active_agents_diff": scenario_metrics["active_agents"] - baseline_metrics["active_agents"]
    }
    
    logger.info(
        "What-If Scenario Executed",
        extra={
            "json_fields": {
                "event": "what_if_run",
                "delta": crowd_delta,
                "gates": close_gates,
                "phase": phase
            }
        }
    )
    
    return jsonify({
        "baseline": baseline_metrics,
        "scenario": scenario_metrics,
        "delta": delta
    })


@app.route("/api/history")
def get_history():
    """Return the most recent persisted simulation runs from Firestore.
    
    Query params:
        limit (int, 1–100): number of records to return (default: 20)
    """
    try:
        limit = int(request.args.get("limit", 20))
        limit = max(1, min(100, limit))
    except (TypeError, ValueError):
        limit = 20

    runs = gcp_services.get_recent_runs(limit=limit)
    return jsonify(
        {
            "count": len(runs),
            "runs": runs,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    logger.info(
        f"NeuroVenue OS server starting on port {port}",
        extra={
            "json_fields": {
                "event": "server_start",
                "port": port,
                "persist_every_n_ticks": gcp_services.PERSIST_EVERY_N_TICKS,
            }
        },
    )
    app.run(host="0.0.0.0", port=port, debug=False)
