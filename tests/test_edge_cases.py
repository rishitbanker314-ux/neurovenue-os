import pytest
from simulation_engine import SimulationEngine

def test_empty_crowd_handling():
    engine = SimulationEngine(num_agents=0)
    # Ensure it doesn't crash or throw ZeroDivisionError natively
    engine.step()
    engine.step()
    for z in engine.zones_list:
        assert z["density"] == 0
        
def test_extreme_density():
    engine = SimulationEngine(num_agents=1000)
    # Force massive artificial congestion logjam entirely localized onto one specific zone metric (x=50, y=50 inside A1 hash grid)
    for a in engine.agents:
        a.position = [50, 50]
        
    engine.step()
    
    a1_zone = next(z for z in engine.zones_list if z["id"] == "A1")
    # Assert majority clustered within mapping bounds correctly scaling math equation
    assert a1_zone["density"] >= 100.0
    assert a1_zone.get("congestion_score", 0) >= 50.0 # Score scales high 
    
def test_sudden_panic_spikes():
    engine = SimulationEngine(num_agents=50)
    
    # Assert manual overriding natively hooks into the agent physics
    engine.manual_phase = "evacuation"
    engine.step()
    
    # Global surge_pressure parameter should natively scale scaling to 1.0 immediately upon phase trigger
    for a in engine.agents:
        assert a.surge_pressure > 0.8
        assert a.state == "evacuation_surge"
