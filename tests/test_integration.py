import pytest
from simulation_engine import SimulationEngine
from server import app

def test_simulation_loop():
    engine = SimulationEngine(num_agents=10)
    assert engine.tick == 0
    engine.step()
    
    # Verify chronological integration 
    assert engine.tick == 1
    
def test_prediction_engine():
    engine = SimulationEngine(num_agents=50)
    predictions = engine.get_predictions()
    
    # Assert the Ghost Engine cloning logic preserves future interval keys cleanly
    assert "plus_5s" in predictions
    assert "plus_10s" in predictions
    assert "plus_20s" in predictions
    
def test_ui_api_state():
    client = app.test_client()
    # Test local simulated frontend state ping hitting the API
    response = client.get('/api/state?s=A1&e=E5')
    assert response.status_code == 200
    
    # Verify 100% schema compliance for UI binding mapping
    data = response.get_json()
    assert "tick" in data
    assert "predictions" in data
    assert "route" in data
    assert "nudge" in data
    assert "zones" in data

def test_server_api_route():
    client = app.test_client()
    response = client.get('/api/route?s=A1&e=D2')
    assert response.status_code == 200
    
    data = response.get_json()
    assert "path" in data
    assert "A1" in data["path"]

def test_server_api_scenario():
    client = app.test_client()
    # Ensure external configuration injections cleanly parse state transitions
    response = client.post('/api/scenario', json={"scenario": "entry"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "success"
