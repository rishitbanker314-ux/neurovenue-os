"""
NeuroVenue OS — Simulation Engine
==================================
Simulates crowd dynamics across a 5x5 venue grid (A1–E5) using a behavior-driven 
physics-inspired Agent model. Incorporates Spatial Grid Intelligence scoring.
Includes a Forward Prediction engine (Ghost Engine) to forecast congestion.
Outputs real-time zone telemetry as JSON every 3 seconds.

Zone layout:
    A1  A2  A3  A4  A5
    B1  B2  B3  B4  B5
    C1  C2  C3  C4  C5
    D1  D2  D3  D4  D5
    E1  E2  E3  E4  E5
"""

import json
import random
import time
import math
from functools import lru_cache


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

ROWS = ["A", "B", "C", "D", "E"]
COLS = [1, 2, 3, 4, 5]
TICK_INTERVAL = 3  # seconds

VENUE_SIZE = 500.0
ZONE_SIZE = 100.0

GATE_ZONES_MAPPING = {
    "A": "A3",
    "B": "A5",
    "C": "C5",
    "D": "E5",
    "E": "E3",
    "F": "E1",
    "G": "C1",
    "H": "A1"
}

FOOD_ZONES = {"B2", "B4", "D2", "D4"}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

@lru_cache(maxsize=32)
def get_neighbors(zone_id: str) -> list[str]:
    """Return adjacent zone IDs (4-directional)."""
    row_idx = ROWS.index(zone_id[0])
    col_idx = int(zone_id[1]) - 1
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row_idx + dr, col_idx + dc
        if 0 <= nr < len(ROWS) and 0 <= nc < len(COLS):
            neighbors.append(f"{ROWS[nr]}{COLS[nc]}")
    return neighbors

def get_zone_from_pos(x: float, y: float) -> str:
    """Map continuous coordinates (0-500) to grid zone ID (e.g. A1)."""
    col = min(4, max(0, int(x // ZONE_SIZE)))
    row = min(4, max(0, int(y // ZONE_SIZE)))
    return f"{ROWS[row]}{COLS[col]}"

@lru_cache(maxsize=32)
def get_zone_center(zone_id: str) -> tuple[float, float]:
    """Return ideal center coordinate of a given zone."""
    row_idx = ROWS.index(zone_id[0])
    col_idx = COLS.index(int(zone_id[1]))
    return (col_idx * ZONE_SIZE + 50.0, row_idx * ZONE_SIZE + 50.0)


# ──────────────────────────────────────────────
# Agent Model
# ──────────────────────────────────────────────

class Agent:
    def __init__(self, position: list[float]):
        self.position = position
        self.velocity = [0.0, 0.0]
        self.acceleration = [0.0, 0.0]
        self.state = 'normal'  # normal, seated, moving_to_exit, congested, waiting, evacuation_surge
        self.destination = None
        self.surge_pressure = 0.0


# ──────────────────────────────────────────────
# Simulation Engine
# ──────────────────────────────────────────────

class SimulationEngine:
    """
    Agent-based crowd simulation engine.
    Wraps the simulation logic into a 3-phase tick loop with physics interpolation,
    Spatial Grid Intelligence, and Predictive Engine capabilities.
    """

    PHASES = ["entry", "main_event", "halftime", "second_half", "exit", "idle", "evacuation"]

    def __init__(self, num_agents: int = 500):
        # Strict validation
        if not isinstance(num_agents, int) or not (0 <= num_agents <= 5000):
            raise ValueError("INVALID_BOUNDS_OVERFLOW: Crowd size must be precisely constrained between 0 and 5000 agents.")

        self.tick: int = 0
        self._manual_phase = "auto"
        self.active_gates = set(GATE_ZONES_MAPPING.values())
        
        # Physics state
        self.prev_zone_densities = {}

        # Initialize Agent Population
        self.agents = []
        for _ in range(num_agents):
            x = random.uniform(0, VENUE_SIZE)
            y = random.uniform(0, VENUE_SIZE)
            self.agents.append(Agent([x, y]))
            
        self.zones_list = self._initialize_zones()
        if num_agents > 0:
            self.updateEnvironment()

    def _initialize_zones(self) -> list[dict]:
        zones = []
        for r in ROWS:
            for c in COLS:
                zones.append({
                    "id": f"{r}{c}",
                    "density": 0,
                    "avg_speed": 1.0,
                    "wait_time": 0,
                    "congestion_score": 0.0
                })
        return zones

    def close_gate(self, gate_char: str) -> bool:
        """Close a specific gate, removing it from active_gates."""
        gate_char = gate_char.upper()
        if gate_char in GATE_ZONES_MAPPING:
            zone = GATE_ZONES_MAPPING[gate_char]
            if zone in self.active_gates:
                self.active_gates.remove(zone)
                return True
        return False

    def add_agents(self, count: int):
        """Dynamically inject more agents into the simulation."""
        for _ in range(count):
            x = random.uniform(0, VENUE_SIZE)
            y = random.uniform(0, VENUE_SIZE)
            self.agents.append(Agent([x, y]))

    @property
    def manual_phase(self):
        return self._manual_phase
        
    @manual_phase.setter
    def manual_phase(self, phase: str):
        if phase != "auto" and phase not in self.PHASES:
            raise ValueError(f"SECURITY ALERT: Non-registered phase override blocked ({phase}).")
        self._manual_phase = phase

    def _get_phase(self) -> str:
        if self._manual_phase != "auto":
            return self._manual_phase
            
        cycle = self.tick % 30
        if cycle < 5: return "entry"
        elif cycle < 12: return "main_event"
        elif cycle < 18: return "halftime"
        elif cycle < 24: return "second_half"
        elif cycle < 28: return "exit"
        else: return "idle"

    # --- Predictive Engine Logic ---

    def clone(self):
        """Create a fast, lightweight Ghost clone of the engine for predictions."""
        ghost = SimulationEngine(0) # bypass generating empty agents
        ghost.tick = self.tick
        ghost.manual_phase = self.manual_phase
        ghost.active_gates = set(self.active_gates)
        ghost.prev_zone_densities = dict(self.prev_zone_densities)
        
        # Fast deepcopy of agents
        for agent in self.agents:
            new_agent = Agent([agent.position[0], agent.position[1]])
            new_agent.velocity = [agent.velocity[0], agent.velocity[1]]
            new_agent.acceleration = [agent.acceleration[0], agent.acceleration[1]]
            new_agent.state = agent.state
            if agent.destination:
                new_agent.destination = [agent.destination[0], agent.destination[1]]
            new_agent.surge_pressure = agent.surge_pressure
            ghost.agents.append(new_agent)
            
        # Fast deepcopy of zones
        ghost.zones_list = [dict(zone) for zone in self.zones_list]
            
        return ghost

    def get_predictions(self) -> dict:
        """Forecast emerging crush hazards avoiding multi-cloning heavily."""
        # Find which zones are currently perfectly safe.
        current_safe_zones = { z["id"] for z in self.zones_list if z["congestion_score"] < 60 }
        
        predictions = {
            "plus_5s": [],
            "plus_10s": [],
            "plus_20s": []
        }
        
        # O(1) Ghost Clone Sequential Loop
        ghost_engine = self.clone()
        intervals = [
            ("plus_5s", max(1, int(5 / 2.0))),
            ("plus_10s", max(1, int(10 / 2.0))),
            ("plus_20s", max(1, int(20 / 2.0)))
        ]
        
        current_loop = 0
        for key, target_loop in intervals:
            loops_to_run = target_loop - current_loop
            for _ in range(loops_to_run):
                ghost_engine.updateAgentStates()
                ghost_engine.updateMovement()
                ghost_engine.updateEnvironment()
            
            # Predict Crush Risks (Gridlock formation) explicitly
            for fz in ghost_engine.zones_list:
                if fz["id"] in current_safe_zones and fz["congestion_score"] > 85:
                    predictions[key].append(fz["id"])
            current_loop = target_loop
                    
        return predictions

    def get_metrics(self) -> dict:
        """Calculate system-wide aggregate metrics for comparisons."""
        if not self.zones_list:
            return {"peak_congestion": 0, "avg_wait": 0, "active_agents": 0}
        
        peak_congestion = max((z.get("congestion_score", 0) for z in self.zones_list), default=0)
        avg_wait = sum(z.get("wait_time", 0) for z in self.zones_list) / len(self.zones_list)
        return {
            "peak_congestion": round(peak_congestion, 1),
            "avg_wait": round(avg_wait, 1),
            "active_agents": len(self.agents)
        }

    def run_what_if_scenario(self, crowd_delta: int, close_gates: list, phase: str, ticks: int = 20) -> dict:
        """Run an isolated future simulation with modified parameters."""
        ghost = self.clone()
        
        # Apply parameters
        if crowd_delta > 0:
            ghost.add_agents(crowd_delta)
        elif crowd_delta < 0:
            # Randomly remove agents to match delta
            to_remove = min(abs(crowd_delta), len(ghost.agents))
            ghost.agents = ghost.agents[to_remove:]
            
        for g in close_gates:
            ghost.close_gate(g)
            
        if phase and phase != "auto":
            ghost.manual_phase = phase
            
        # Fast forward
        for _ in range(ticks):
            ghost.updateAgentStates()
            ghost.updateMovement()
            ghost.updateEnvironment()
            ghost.tick += 1
            
        return ghost.get_metrics()

    def analyze_recommendations(self) -> dict:
        """Run parallel ghosts to generate an optimal operational recommendation."""
        # 1. Baseline
        baseline = self.run_what_if_scenario(0, [], "auto", ticks=15)
        baseline_cong = baseline["peak_congestion"]
        
        best_action = None
        best_explanation = ""
        best_factors = []
        best_improvement = 0
        
        # Test 1: What if we close each of the currently open gates?
        for gate in list(self.active_gates):
            ghost_metrics = self.run_what_if_scenario(0, [gate], "auto", ticks=15)
            improvement = baseline_cong - ghost_metrics["peak_congestion"]
            if improvement > best_improvement:
                best_improvement = improvement
                best_action = f"Close Gate {gate} to reduce peak congestion by {round(improvement, 1)}%"
                best_explanation = f"Simulating closure of Gate {gate} forces directional traffic away from active bottlenecks, rebalancing spatial load."
                best_factors = [
                    f"Baseline peak hazard: {baseline_cong}%",
                    f"Post-optimization hazard: {ghost_metrics['peak_congestion']}%",
                    f"Diverts traffic dynamically from active routes"
                ]
                
        # Test 2: What if we open each currently closed gate? 
        all_gates = {"A", "B", "C", "D", "E", "F", "G", "H"}
        closed_gates = all_gates - self.active_gates
        for gate in closed_gates:
            ghost = self.clone()
            ghost.active_gates.add(gate)
            # Run manually
            for _ in range(15):
                ghost.updateAgentStates()
                ghost.updateMovement()
                ghost.updateEnvironment()
                ghost.tick += 1
            metrics = ghost.get_metrics()
            improvement = baseline_cong - metrics["peak_congestion"]
            if improvement > best_improvement:
                best_improvement = improvement
                best_action = f"Open Gate {gate} to reduce peak congestion by {round(improvement, 1)}%"
                best_explanation = f"Simulating opening of Gate {gate} introduces new egress vectors, absorbing excess pressure surrounding primary chokepoints."
                best_factors = [
                    f"Baseline peak hazard: {baseline_cong}%",
                    f"Post-optimization hazard: {metrics['peak_congestion']}%",
                    f"Reduces localized agent pathing friction"
                ]
        
        if best_improvement > 2.0:
            confidence = min(99, max(75, int(65 + (best_improvement * 2))))
            return {
                "action": f"TACTICAL ALERT: {best_action}",
                "explanation": best_explanation,
                "factors": best_factors,
                "confidence": confidence
            }
        else:
            return {
                "action": "System optimal. No high-impact interventions identified.",
                "explanation": "Parallel ghost simulations evaluated all gate configurations. No modification yielded > 2.0% congestion improvement.",
                "factors": [
                    f"Current peak congestion: {baseline_cong}%",
                    "Alternative vectors sub-optimal"
                ],
                "confidence": 99
            }


    # --- Global Simulation Loop ---

    def updateAgentStates(self):
        """Update cognitive/FSM states and destinations based on global phase."""
        phase = self._get_phase()
        
        for agent in self.agents:
            agent.surge_pressure = max(0.0, agent.surge_pressure - 0.05) # Natural pressure relief

            if phase == "evacuation":
                agent.state = "evacuation_surge"
                agent.surge_pressure = 1.0
                if not self.active_gates:
                    continue # No gates available
                if not agent.destination or get_zone_from_pos(agent.destination[0], agent.destination[1]) not in self.active_gates:
                    gate = random.choice(list(self.active_gates))
                    agent.destination = get_zone_center(gate)
                    
            elif phase in ["entry", "exit"]:
                agent.state = "moving_to_exit"
                if not self.active_gates and phase == "exit":
                    continue # Nowhere to exit
                if random.random() < 0.2 or not agent.destination:
                    target = random.choice(list(self.active_gates)) if phase == "exit" else f"{random.choice(ROWS)}{random.choice(COLS)}"
                    agent.destination = get_zone_center(target)
                    
            elif phase == "halftime":
                if random.random() < 0.3:
                    agent.state = "waiting"
                    if not agent.destination:
                        agent.destination = get_zone_center(random.choice(list(FOOD_ZONES)))
                else:
                    if agent.state == "waiting": continue
                    agent.state = "normal"
                    if random.random() < 0.2 or not agent.destination: 
                         agent.destination = get_zone_center(f"{random.choice(ROWS)}{random.choice(COLS)}")
                         
            else: # main_event, idle, second_half
                if agent.state in ["evacuation_surge", "moving_to_exit"]:
                    agent.state = "normal"
                
                # Realistic Stadium "Seated" Bounds    
                if random.random() < 0.95:
                    agent.state = "seated"
                    if not agent.destination:
                        agent.destination = [max(0, min(VENUE_SIZE, agent.position[0] + random.uniform(-5, 5))), 
                                             max(0, min(VENUE_SIZE, agent.position[1] + random.uniform(-5, 5)))]
                else:
                    agent.state = "normal"
                    if random.random() < 0.05 or not agent.destination:
                        tx = max(0, min(VENUE_SIZE, agent.position[0] + random.uniform(-60, 60)))
                        ty = max(0, min(VENUE_SIZE, agent.position[1] + random.uniform(-60, 60)))
                        agent.destination = [tx, ty]

    def updateMovement(self):
        """Apply operational gridlock bottlenecking limits over fluid-game engines."""
        dt = 0.5 # sub-tick integration
        sub_steps = 4 # Smooth out movement
        
        # Build spatial intelligence lookup for repulsion forces
        zone_congestion = {z['id']: z['congestion_score'] for z in self.zones_list}

        for _ in range(sub_steps):
            for agent in self.agents:
                # Reset acceleration
                agent.acceleration = [0.0, 0.0]
                
                zid = get_zone_from_pos(agent.position[0], agent.position[1])
                local_congestion = zone_congestion.get(zid, 0)
                
                max_speed = 6.0
                max_force = 1.0
                congestion_slowdown = max(0.2, 1.0 - (local_congestion / 100.0))  # standard slowdown
                
                # GRIDLOCK CRUSH MECHANIC (Real world crush bounds)
                if local_congestion > 90.0:
                    congestion_slowdown = 0.02 # Force massive bottleneck explicitly
                
                if agent.state == "evacuation_surge" or agent.surge_pressure > 0.8:
                    max_speed = 12.0
                    max_force = 3.0
                    congestion_slowdown = max(0.1, congestion_slowdown) # Evacuating people push through harder natively
                elif agent.state in ["waiting", "seated"]:
                    max_speed = 1.0
                    max_force = 0.5
                else:
                    max_speed *= congestion_slowdown

                # Attraction force toward destinations
                if agent.destination:
                    dx = agent.destination[0] - agent.position[0]
                    dy = agent.destination[1] - agent.position[1]
                    dist = math.hypot(dx, dy)
                    
                    if dist > 3.0:
                        desired_vx = (dx / dist) * max_speed
                        desired_vy = (dy / dist) * max_speed
                        
                        steer_x = desired_vx - agent.velocity[0]
                        steer_y = desired_vy - agent.velocity[1]
                        
                        steer_mag = math.hypot(steer_x, steer_y)
                        if steer_mag > max_force:
                            steer_x = (steer_x / steer_mag) * max_force
                            steer_y = (steer_y / steer_mag) * max_force
                            
                        agent.acceleration[0] += steer_x
                        agent.acceleration[1] += steer_y
                    else:
                        if agent.state in ["waiting", "seated"]:
                            agent.destination = None
                        agent.velocity[0] *= 0.5 # decelerate
                        agent.velocity[1] *= 0.5 

                # Integrate Kinematics
                agent.velocity[0] += agent.acceleration[0] * dt
                agent.velocity[1] += agent.acceleration[1] * dt
                
                v_mag = math.hypot(*agent.velocity)
                if v_mag > max_speed:
                    agent.velocity[0] = (agent.velocity[0] / v_mag) * max_speed
                    agent.velocity[1] = (agent.velocity[1] / v_mag) * max_speed
                    
                agent.position[0] += agent.velocity[0] * dt
                agent.position[1] += agent.velocity[1] * dt
                
                # Boundary clamping
                agent.position[0] = max(0.0, min(VENUE_SIZE, agent.position[0]))
                agent.position[1] = max(0.0, min(VENUE_SIZE, agent.position[1]))


    def updateEnvironment(self):
        """Aggregate data computing surge pressures."""
        zone_counts = {f"{r}{c}": 0 for r in ROWS for c in COLS}
        zone_speeds = {f"{r}{c}": [] for r in ROWS for c in COLS}
        zone_waits = {f"{r}{c}": 0 for r in ROWS for c in COLS}
        
        for agent in self.agents:
            zid = get_zone_from_pos(agent.position[0], agent.position[1])
            zone_counts[zid] += 1
            zone_speeds[zid].append(math.hypot(agent.velocity[0], agent.velocity[1]))
            if agent.state in ['waiting', 'congested', 'seated']:
                zone_waits[zid] += 1

        max_agents_per_zone = len(self.agents) / 6.0 
        
        for zone in self.zones_list:
            zid = zone["id"]
            
            if "density" in zone:
                self.prev_zone_densities[zid] = zone.get("density", 0)
            else:
                self.prev_zone_densities[zid] = 0
            
            count = zone_counts[zid]
            density = min(100.0, (count / max_agents_per_zone) * 100.0) if max_agents_per_zone > 0 else 0.0
            zone["density"] = round(density, 2)
            
            speeds = zone_speeds[zid]
            avg_s = sum(speeds) / len(speeds) if speeds else 1.0
            zone["avg_speed"] = round(avg_s, 2)
            
            low_velocity_score = max(0.0, min(100.0, (1.0 - (avg_s / 5.0)) * 100.0))
            
            wait_t = min(100.0, zone_waits[zid] * 12.0)
            zone["wait_time"] = round(wait_t, 2)
            
            # Formulate strict LoS Congestion Rating organically mapping Gridlock
            congestion_score = (density * 0.5) + (low_velocity_score * 0.3) + (wait_t * 0.2)
            zone["congestion_score"] = round(congestion_score, 2)
            
            # Surge pressure amplification
            density_delta = density - self.prev_zone_densities[zid]
            if density_delta > 20:
                for agent in self.agents:
                    if get_zone_from_pos(*agent.position) == zid:
                        agent.surge_pressure = min(1.0, agent.surge_pressure + density_delta / 40.0)
                        if agent.surge_pressure > 0.8:
                            agent.state = 'evacuation_surge'


    def step(self):
        """Advance one tick passing through the Physics Agent Loop."""
        self.updateAgentStates()
        self.updateMovement()
        self.updateEnvironment()
        self.tick += 1

    def get_state(self) -> dict:
        """Return state payload containing zones and upcoming prediction risks."""
        return {
            "tick": self.tick,
            "phase": self._get_phase(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "zones": self.zones_list,
            "predictions": self.get_predictions(),
        }

def main():
    import sys
    engine = SimulationEngine()
    print("=" * 60)
    print("  NeuroVenue OS — Operational Simulation Framework")
    print(f"  25 Zones | {len(engine.agents)} Agents | Tick interval: {TICK_INTERVAL}s")
    print("=" * 60)
    print()

    try:
        while True:
            start_t = time.perf_counter()
            engine.step()
            state = engine.get_state()
            calc_ms = (time.perf_counter() - start_t) * 1000.0
            
            sorted_zones = sorted(state['zones'], key=lambda z: z['congestion_score'], reverse=True)
            top_zones = sorted_zones[:3]
            top_display = [f"{z['id']} (Score: {z['congestion_score']})" for z in top_zones if z['congestion_score'] > 40]
            
            print(f"--- Tick {state['tick']} | Phase: {state['phase']} | Execution: {calc_ms:.1f}ms ---")
            
            if top_display:
                print(f"🚨 Top Congestion Zones: {', '.join(top_display)}")
            else:
                print(f"✅ All Grid Cells Flowing Nominally")
                
            pred = state["predictions"]
            has_preds = any([len(p) > 0 for p in pred.values()])
            if has_preds:
                print(f"🔮 Predicted Emerging Risks: ")
                if pred["plus_5s"]: print(f"   +5s : {', '.join(pred['plus_5s'])}")
                if pred["plus_10s"]: print(f"   +10s: {', '.join(pred['plus_10s'])}")
                if pred["plus_20s"]: print(f"   +20s: {', '.join(pred['plus_20s'])}")
                
            time.sleep(TICK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n[NeuroVenue OS] Simulation stopped.")

if __name__ == "__main__":
    main()
