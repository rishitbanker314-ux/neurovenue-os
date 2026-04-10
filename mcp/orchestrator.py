import json
import sys
import os

# Add parent directory to path so we can import the engines
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation_engine import SimulationEngine, generate_zones
from routing_engine import find_best_path
from nudge_engine import generate_nudge

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

class SimulationAgent:
    def __init__(self, name):
        self.name = name
        self.engine = SimulationEngine()
        
    def process(self, *args, **kwargs):
        self.engine.step()
        state = self.engine.get_state()
        print(f"[{self.name}] Generated {len(state['zones'])} zones for tick {state['tick']}")
        return state["zones"]

class RoutingAgent:
    def __init__(self, name):
        self.name = name
        
    def process(self, zones, start="A1", end="E5"):
        route = find_best_path(zones, start, end)
        print(f"[{self.name}] Calculated optimal path: {' -> '.join(route['path'])}")
        return route

class NudgeAgent:
    def __init__(self, name):
        self.name = name
        
    def process(self, route):
        nudge = generate_nudge(route)
        print(f"[{self.name}] Generated suggestion:")
        print(f"   {nudge.split(chr(10))[0]}") # Print first line of nudge
        return nudge

# Agent Registry mappings
AGENT_REGISTRY = {
    "simulation_agent": SimulationAgent,
    "routing_agent": RoutingAgent,
    "nudge_agent": NudgeAgent
}

def load_agents(config_path):
    """Load agents based on mcp/config.json"""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    agents = []
    for agent_config in config.get("agents", []):
        name = agent_config["name"]
        if name in AGENT_REGISTRY:
            agents.append(AGENT_REGISTRY[name](name))
        else:
            print(f"Warning: Unknown agent '{name}' in config.")
            
    return agents

def run_agent_pipeline(start_zone="A1", end_zone="E5"):
    """
    Executes the MCP agents in sequence:
    1. simulation_agent generates zone data
    2. routing_agent processes paths using the zone data
    3. nudge_agent generates suggestions using the processed path
    """
    agents = load_agents(CONFIG_PATH)
    
    if len(agents) < 3:
        raise ValueError("Pipeline requires at least 3 configured agents.")
        
    sim_agent, routing_agent, nudge_agent = agents[0], agents[1], agents[2]
    
    print("🚀 Triggering MCP Agent Pipeline\n" + "-"*40)
    
    # 1. Simulation Agent
    zones = sim_agent.process()
    
    # 2. Routing Agent
    route = routing_agent.process(zones, start=start_zone, end=end_zone)
    
    # 3. Nudge Agent
    nudge = nudge_agent.process(route)
    
    print("-" * 40)
    print("✅ Pipeline execution complete!\n")
    return {
        "zones": zones,
        "route": route,
        "nudge": nudge
    }

if __name__ == "__main__":
    run_agent_pipeline()
    run_agent_pipeline(start_zone="A5", end_zone="E1")
