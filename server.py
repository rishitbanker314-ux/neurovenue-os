"""
NeuroVenue OS — Dashboard API Server
======================================
Serves simulation data, routing, and nudges as JSON endpoints.
Also serves the dashboard HTML file.

Endpoints:
    GET  /                  → Dashboard HTML
    GET  /api/state         → Current simulation state + route + nudge
    GET  /api/route?s=A1&e=E5  → Route between two zones

Requires: pip install flask flask-cors
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os

from simulation_engine import generate_zones, SimulationEngine
from routing_engine import find_best_path
from nudge_engine import generate_nudge

app = Flask(__name__)
CORS(app)

# Global simulation engine
engine = SimulationEngine()


@app.route("/")
def index():
    """Serve the dashboard HTML."""
    return send_file("dashboard.html")


@app.route("/api/state")
def get_state():
    """
    Returns current simulation state with a default route and nudge.
    Called every 3 seconds by the dashboard.
    """
    engine.step()
    state = engine.get_state()
    zones = state["zones"]

    # Default route
    start = request.args.get("s", "A1")
    end = request.args.get("e", "E5")
    route = find_best_path(zones, start, end)
    nudge = generate_nudge(route)

    return jsonify({
        "tick": state["tick"],
        "phase": state["phase"],
        "timestamp": state["timestamp"],
        "zones": zones,
        "route": {
            "start": start,
            "end": end,
            "path": route["path"],
            "time_saved": route["time_saved"],
        },
        "nudge": nudge,
    })


@app.route("/api/route")
def get_route():
    """
    Returns a route between two zones.
    Query params: ?s=A1&e=E5
    """
    start = request.args.get("s", "A1")
    end = request.args.get("e", "E5")

    zones = generate_zones()
    route = find_best_path(zones, start, end)
    nudge = generate_nudge(route)

    return jsonify({
        "path": route["path"],
        "time_saved": route["time_saved"],
        "nudge": nudge,
    })


@app.route("/api/scenario", methods=["POST"])
def set_scenario():
    """
    Set manual scenario/phase override.
    Expects JSON: {"scenario": "emergency" | "halftime" | "entry" | "auto"}
    """
    data = request.get_json()
    scenario = data.get("scenario", "auto")
    engine.manual_phase = scenario
    
    # Tick once to apply immediately
    engine.step()
    
    return jsonify({"status": "success", "scenario": scenario})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("=" * 55)
    print(f"  NeuroVenue OS — Dashboard Server")
    print(f"  http://localhost:{port}")
    print("=" * 55)
    app.run(host="0.0.0.0", port=port, debug=False)
