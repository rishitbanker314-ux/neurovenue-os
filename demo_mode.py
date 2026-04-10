import time
from simulation_engine import SimulationEngine
from routing_engine import find_best_path
from nudge_engine import generate_nudge

def run_demo():
    print("=" * 60)
    print("  🎬 NeuroVenue OS — Automated Demo Mode")
    print("=" * 60)
    
    engine = SimulationEngine()
    
    # ─── SCENARIO 1 ───────────────────────────────
    engine.manual_phase = "idle"
    engine.step()
    
    print("\n[Scenario 1] Normal Operations")
    print("----------------------------------------")
    print("Crowds are light. Default pathing applies.")
    time.sleep(1.5)
    
    state = engine.get_state()
    route = find_best_path(state["zones"], "A1", "E5")
    nudge = generate_nudge(route)
    
    print(f"➡️ Path: {' -> '.join(route['path'])}")
    print(f"💡 Suggestion: {nudge.splitlines()[0]}")
    time.sleep(2)
    
    
    # ─── SCENARIO 2 ───────────────────────────────
    print("\n[Scenario 2] Halftime Rush")
    print("----------------------------------------")
    engine.manual_phase = "halftime"
    
    # Step a few times to build up intense density
    for _ in range(3):
        engine.step()
        
    state = engine.get_state()
    hot_zones = [z['id'] for z in state["zones"] if z['density'] > 80]
    
    print(f"⚠️ Crowd Buildup Detected in Food/Restroom Zones!")
    print(f"🔥 Critical Density Zones: {', '.join(hot_zones) if hot_zones else 'None'}")
    time.sleep(2)
    
    print("\n🔄 Recalculating dynamic routing to avoid congestion...")
    time.sleep(1.5)
    
    route2 = find_best_path(state["zones"], "A1", "E5")
    nudge2 = generate_nudge(route2)
    
    print(f"➡️ New Smart Path: {' -> '.join(route2['path'])}")
    print(f"💡 Suggestion: {nudge2.splitlines()[0]}")
    print(f"⏱️ Improvement: Saved {route2['time_saved']} seconds compared to direct route!")
    time.sleep(2.5)
    
    
    # ─── SCENARIO 3 ───────────────────────────────
    print("\n[Scenario 3] Emergency Evacuation")
    print("----------------------------------------")
    engine.manual_phase = "emergency"
    engine.step()
    
    state = engine.get_state()
    avg_density = sum(z['density'] for z in state["zones"]) / len(state["zones"])
    print(f"🚨 Evacuation triggered! Average density spiked to {int(avg_density)}/100")
    time.sleep(1.5)
    
    print("\n🔄 Routing to nearest safe exits...")
    time.sleep(1)
    
    # Example: Trying to evacuate from center (C3)
    route3 = find_best_path(state["zones"], "C3", "E5")
    nudge3 = generate_nudge(route3)
    
    print(f"➡️ Evacuation Path: {' -> '.join(route3['path'])}")
    print(f"💡 Suggestion: {nudge3.splitlines()[0]}")
    print(f"⏱️ Improvement: Saved {route3['time_saved']} seconds while bypassing deadly crush zones!")
    
    print("\n" + "=" * 60)
    print("  ✅ Demo Complete")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
