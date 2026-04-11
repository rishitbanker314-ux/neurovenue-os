import pytest
from simulation_engine import SimulationEngine
from routing_engine import find_best_path
from server import app

# ──────────────────────────────────────────────
# 1. Bounds Validation Overflows
# ──────────────────────────────────────────────
def test_engine_initialization_bounds():
    # Instantiating 0 or massively scaling variables gracefully crashes explicitly natively 
    with pytest.raises(ValueError, match="INVALID_BOUNDS_OVERFLOW"):
        SimulationEngine(num_agents=-1)
        
    with pytest.raises(ValueError, match="INVALID_BOUNDS_OVERFLOW"):
        SimulationEngine(num_agents=10000)

def test_engine_phase_security():
    engine = SimulationEngine(num_agents=50)
    # Valid assignments stringently preserved
    engine.manual_phase = "evacuation"
    
    # State injection safely drops strings avoiding engine memory manipulation
    with pytest.raises(ValueError, match="SECURITY ALERT"):
        engine.manual_phase = "malicious_undefined_phase_str"

# ──────────────────────────────────────────────
# 2. XSS & Payload Routing Safety Checks 
# ──────────────────────────────────────────────
def test_safe_zone_mirror_fallback():
    zones = [{"id": f"{r}{c}", "density": 0, "congestion_score": 0} for r in ['A'] for c in [1,2,3]]
    # Passing raw cross-site script payloads natively defaults into "A1" / "E5" fallbacks instead of echoing
    route = find_best_path(zones, start="<script>alert(1)</script>", end="E5")
    assert "<script>" not in route["path"]
    assert "A1" in route["path"]

# ──────────────────────────────────────────────
# 3. HTTP Server Endpoints Sanitization Decorator Validation!
# ──────────────────────────────────────────────
def test_server_api_get_state_parameter_malformed_denial():
    client = app.test_client()
    
    # Successful query
    response_clean = client.get('/api/state?s=A1&e=D4')
    assert response_clean.status_code == 200

    # Malicious Query 1 (OOB ID parameter)
    response_xss1 = client.get('/api/state?s=Z9&e=D4')
    assert response_xss1.status_code == 400
    assert "SECURITY BLOCK" in response_xss1.get_json()["error"]
    
    # Malicious Query 2 (Script Injection)
    response_xss2 = client.get('/api/state?s=<script>alert()</script>&e=E5')
    assert response_xss2.status_code == 400
    assert "SECURITY BLOCK" in response_xss2.get_json()["error"]
    
def test_server_api_route_parameter_malformed_denial():
    client = app.test_client()
    # SQLi simulation drops
    response_xss2 = client.get('/api/route?s=A1%27+OR+1%3D1--&e=E5')
    assert response_xss2.status_code == 400
    assert "SECURITY BLOCK" in response_xss2.get_json()["error"]
