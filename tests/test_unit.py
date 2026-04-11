import pytest
from simulation_engine import SimulationEngine

def test_agent_movement_logic():
    engine = SimulationEngine(num_agents=1)
    agent = engine.agents[0]
    initial_pos = tuple(agent.position)
    
    # Force direct destination mapping
    agent.destination = (initial_pos[0] + 100, initial_pos[1] + 100)
    engine.updateMovement()
    
    # Assert kinematics update X/Y position over sub-steps natively 
    assert tuple(agent.position) != initial_pos

def test_congestion_scoring_math():
    engine = SimulationEngine(num_agents=10)
    # Stuff all agents into Zone A1
    for agent in engine.agents:
        agent.position = [20, 20]
        agent.velocity = [0.0, 0.0]
        agent.state = 'waiting'
        
    engine.updateEnvironment()
    
    # Formula calculates high density and low velocity -> >25 minimum score threshold
    score = engine.zones_list[0].get("congestion_score", 0)
    assert score >= 25.0

from routing_engine import find_best_path, get_neighbors

def test_routing_decisions_dijkstra():
    # Construct base mock nodes
    zones = [{"id": f"{r}{c}", "density": 0, "congestion_score": 0} for r in ['A','B','C','D','E'] for c in [1,2,3,4,5]]
    
    # Construct an artificial massive logjam preventing linear path traversal
    for z in zones:
        if z["id"] in ["B1", "C1", "D1"]:
            z["congestion_score"] = 90  # > 75 Critical Block
            
    route = find_best_path(zones, "A1", "E1")
    path = route["path"]
    
    # A rigid Dijkstra algorithm heavily penalizes (Score * 2.5) == 225 weight -> it MUST reroute!
    assert "C1" not in path

def test_topology_neighbors():
    n = get_neighbors("A1")
    assert "B1" in n
    assert "A2" in n
    assert "B2" in n  # Diagonal neighbor verification
    assert "C1" not in n

from routing_engine import generate_suggestion
def test_generate_suggestion():
    zones = [{"id": f"{r}{c}", "density": 0, "congestion_score": 0} for r in ['A','B','C','D','E'] for c in [1,2,3,4,5]]
    suggestion = generate_suggestion("user_123", "A1", "E5", zones)
    
    assert suggestion["user_id"] == "user_123"
    assert "recommended_path" in suggestion
    assert "time_saved" in suggestion

from nudge_engine import generate_nudge, format_time, generate_batch_nudges

def test_nudge_generation():
    res = {"path": ["A1", "A3", "E5"], "time_saved": 120}
    nudge = generate_nudge(res)
    assert "Head through Zone A3" in nudge
    assert "2 minutes" in nudge
    assert "💡" in nudge # Checking conditional rendering for 120s saved
    
def test_nudge_short():
    res = {"path": ["A1", "B1"], "time_saved": 10}
    nudge = generate_nudge(res)
    assert "Go straight to B1" in nudge
    assert "💡" not in nudge # Too low threshold for reward
    
def test_format_time():
    assert format_time(45) == "45 seconds"
    assert format_time(60) == "1 minute"
    assert format_time(125) == "2 min 5s"
    
def test_batch_nudges():
    in_arr = [{"path": ["A1", "A2"]}, {"path": ["B1", "B2"]}]
    out = generate_batch_nudges(in_arr)
    assert len(out) == 2

from routing_engine import find_best_path
def test_find_best_path_invalid_zones():
    # Test safe default boundary bounds triggering when supplied invalid start or end sequences 
    res = find_best_path([], start="Z99", end="X99")
    assert res["path"] == ["A1", "E5"]
    
def test_find_best_path_type_error_fallbacks():
    # Test strict int / array array constraints being bypassed default to A1->E5 mappings
    res = find_best_path([], start=123, end=["E5"])
    assert res["path"] == ["A1", "E5"]

from simulation_engine import get_zone_from_pos, get_zone_center
def test_spatial_grid_helpers():
    # Test bounding logic
    assert get_zone_from_pos(0, 0) == "A1"
    assert get_zone_from_pos(250, 250) == "C3"
    assert get_zone_from_pos(499, 499) == "E5"
    assert get_zone_from_pos(1000, -100) == "A5" # Test clamping! 
    assert get_zone_center("C3") == (250.0, 250.0)
