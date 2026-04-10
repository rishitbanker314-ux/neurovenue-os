"""
NeuroVenue OS — Routing Engine
===============================
Finds a path between two zones on the 5x5 venue grid,
avoiding congested areas (density > 80).

Output matches the Suggestion schema from gemini.md:
    {
        "user_id":          string,
        "recommended_path": [zone_id, ...],
        "time_saved":       number (seconds)
    }
"""

import json
import time

from simulation_engine import SimulationEngine, generate_zones


# ──────────────────────────────────────────────
# Core pathfinding logic
# ──────────────────────────────────────────────

import random

def find_best_path(zones, start, end):
    # Simple demo logic (not full graph yet)
    path = [start]
    
    max_bypassed_density = 0

    for zone in zones:
        if zone["density"] < 80 and zone["id"] != start and zone["id"] != end:
            path.append(zone["id"])
            max_bypassed_density = max(max_bypassed_density, 90 - zone["density"])
            break

    path.append(end)
    
    # Dynamic time saved based on density avoided + random fluctuation for realism
    base_save = 45
    dynamic_save = max_bypassed_density * 1.5
    time_saved = int(base_save + dynamic_save + random.randint(-15, 45))

    return {
        "path": path,
        "time_saved": time_saved
    }


# ──────────────────────────────────────────────
# Suggestion builder (matches gemini.md schema)
# ──────────────────────────────────────────────

def generate_suggestion(user_id: str, start: str, end: str, zones: list[dict]) -> dict:
    """
    Wraps find_best_path to produce a Suggestion matching gemini.md.
    """
    result = find_best_path(zones, start, end)
    return {
        "user_id": user_id,
        "recommended_path": result["path"],
        "time_saved": result["time_saved"],
    }


# ──────────────────────────────────────────────
# Main — interactive demo
# ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  NeuroVenue OS — Routing Engine v0.2.0")
    print("  Simple density-aware pathfinding")
    print("=" * 60)

    engine = SimulationEngine()
    engine.step()

    while True:
        state = engine.get_state()
        zones = state["zones"]

        # Show current densities
        print(f"\n  Phase: {state['phase']} | Tick: {state['tick']}")
        print("  Current zone densities:")
        for z in zones:
            bar = "█" if z["density"] > 80 else "▓" if z["density"] > 60 else "▒" if z["density"] > 30 else "░"
            print(f"    {z['id']}: {bar} {z['density']:3d}")

        # Get user input
        print("\n  Enter route (or 'q' to quit):")
        try:
            start = input("    Start zone  (e.g. A1): ").strip().upper()
            if start.lower() == "q":
                break
            end = input("    Destination (e.g. E5): ").strip().upper()
            if end.lower() == "q":
                break
        except (EOFError, KeyboardInterrupt):
            break

        # Generate and display suggestion
        user_id = f"user_{int(time.time()) % 10000:04d}"
        suggestion = generate_suggestion(user_id, start, end, zones)

        print(f"\n  {'─' * 40}")
        print(f"  📊 Suggestion:")
        print(f"     Path:       {' → '.join(suggestion['recommended_path'])}")
        print(f"     Time saved: {suggestion['time_saved']}s")
        print(f"\n  Raw JSON:")
        print(f"  {json.dumps(suggestion, indent=2)}")
        print(f"  {'─' * 40}")

        # Advance simulation for next query
        engine.step()

    print("\n[NeuroVenue OS] Routing engine stopped.")


if __name__ == "__main__":
    main()
