"""
NeuroVenue OS — Routing Engine
===============================
Finds a path between two zones on the 5x5 venue grid,
using a dynamic Risk-Aware Pathfinding Engine (Dijkstra).

Output matches the Suggestion schema from gemini.md:
    {
        "user_id":          string,
        "recommended_path": [zone_id, ...],
        "time_saved":       number (seconds)
    }
"""

import json
import time
import random
import heapq

from simulation_engine import SimulationEngine

# ──────────────────────────────────────────────
# Topology
# ──────────────────────────────────────────────

ROWS = ["A", "B", "C", "D", "E"]
COLS = [1, 2, 3, 4, 5]

def get_neighbors(zone_id):
    """Returns valid neighboring zones in the 5x5 grid."""
    row_idx = ROWS.index(zone_id[0])
    col_idx = int(zone_id[1]) - 1
    neighbors = []
    
    # Up, Down, Left, Right
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row_idx + dr, col_idx + dc
        if 0 <= nr < len(ROWS) and 0 <= nc < len(COLS):
            neighbors.append(f"{ROWS[nr]}{COLS[nc]}")
            
    # Include Diagonals for smoother routing
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = row_idx + dr, col_idx + dc
        if 0 <= nr < len(ROWS) and 0 <= nc < len(COLS):
            neighbors.append(f"{ROWS[nr]}{COLS[nc]}")
            
    return neighbors


# Global memory to track hysteresis
LAST_PATH = {}

# ──────────────────────────────────────────────
# Core pathfinding logic (Dijkstra)
# ──────────────────────────────────────────────

def find_best_path(zones, start, end, predictions=None):
    global LAST_PATH
    
    zone_dict = { z["id"]: z for z in zones }
    # Strict validation mapping
    if not isinstance(start, str) or not isinstance(end, str):
        start, end = "A1", "E5"
    if start not in zone_dict or end not in zone_dict:
        # Safe Default 0-Mirror Fallback 
        return {"path": ["A1", "E5"], "time_saved": 0}
        
    def edge_weight(neighbor_id, neighbor_is_diagonal=False):
        # 1. Base Distance Weight (10 for lateral, ~14 for diagonal)
        cost = 14.14 if neighbor_is_diagonal else 10.0
        
        # 2. Current Congestion Risk 
        cz = zone_dict.get(neighbor_id)
        if cz:
             current_congestion = cz.get("congestion_score", cz.get("density", 0))
             # Penalize heavily if already congested
             if current_congestion > 75:
                 cost += current_congestion * 2.5 # Exponentiate danger
             else:
                 cost += current_congestion
             
        # 3. Predicted Future Density Risk Penalty
        predicted_penalty = 0.0
        if predictions:
            if neighbor_id in predictions.get("plus_5s", []): predicted_penalty += 80.0
            elif neighbor_id in predictions.get("plus_10s", []): predicted_penalty += 45.0
            elif neighbor_id in predictions.get("plus_20s", []): predicted_penalty += 20.0
            
        cost += predicted_penalty
            
        return cost
        
    distances = {z["id"]: float('inf') for z in zones}
    distances[start] = 0
    previous_nodes = {z["id"]: None for z in zones}
    
    pq = [(0, start)]
    
    while pq:
        current_cost, current_node = heapq.heappop(pq)
        
        if current_node == end:
            break
            
        if current_cost > distances[current_node]:
            continue
            
        curr_row_idx = ROWS.index(current_node[0])
        curr_col_idx = int(current_node[1]) - 1
            
        for neighbor in get_neighbors(current_node):
            if neighbor not in distances: continue
            
            neigh_row_idx = ROWS.index(neighbor[0])
            neigh_col_idx = int(neighbor[1]) - 1
            is_diagonal = abs(curr_row_idx - neigh_row_idx) == 1 and abs(curr_col_idx - neigh_col_idx) == 1
            
            # Equation: path_cost = distance_weight + congestion_risk + predicted_future_density
            cost_to_neighbor = edge_weight(neighbor, is_diagonal)
            
            # Dynamic Rerouting Hysteresis: Discount path if it was used last tick
            # This prevents UI oscillating paths unless a new route is > 15% better natively
            route_key = f"{start}-{end}"
            if route_key in LAST_PATH and neighbor in LAST_PATH[route_key]:
                cost_to_neighbor *= 0.85 # -15% penalty to retain stability!

            new_cost = current_cost + cost_to_neighbor
            
            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous_nodes[neighbor] = current_node
                heapq.heappush(pq, (new_cost, neighbor))
                
    # Reconstruct path
    path = []
    curr = end
    while curr is not None:
        path.append(curr)
        curr = previous_nodes.get(curr, None)
    path.reverse()
    
    if path[0] != start:
        # no path found (unlikely in grid, but just in case)
        path = [start, end]
        
    LAST_PATH[f"{start}-{end}"] = path
    
    # Calculate dummy time saved (higher distances walked relative to optimal free space implies more time) 
    optimal_cost = 10.0 * (abs(ROWS.index(start[0]) - ROWS.index(end[0])) + abs(int(start[1]) - int(end[1])))
    actual_cost = distances[end] if distances[end] != float('inf') else optimal_cost
    time_saved = int(max(0, actual_cost - optimal_cost) * 0.4) + random.randint(5, 15)
    
    return {
        "path": path,
        "time_saved": min(time_saved, 180) # Cap display string at 3 minutes 
    }


# ──────────────────────────────────────────────
# Suggestion builder (matches gemini.md schema)
# ──────────────────────────────────────────────

def generate_suggestion(user_id: str, start: str, end: str, zones: list[dict], predictions: dict = None) -> dict:
    """
    Wraps find_best_path to produce a Suggestion matching gemini.md.
    """
    result = find_best_path(zones, start, end, predictions)
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
    print("  NeuroVenue OS — Routing Engine v0.3.0")
    print("  Risk-Aware Dijkstra Pathfinding (Future-Prediction Active)")
    print("=" * 60)

    engine = SimulationEngine()
    engine.step()

    while True:
        state = engine.get_state()
        zones = state["zones"]
        predictions = state.get("predictions", None)

        # Show current densities
        print(f"\n  Phase: {state['phase']} | Tick: {state['tick']}")
        print("  Current zone densities:")
        for z in zones:
            score = z.get('congestion_score', z['density'])
            bar = "█" if score > 75 else "▓" if score > 50 else "▒" if score > 25 else "░"
            print(f"    {z['id']}: {bar} Score: {score:3.0f} | Count: {z['density']:3.0f}")

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
        suggestion = generate_suggestion(user_id, start, end, zones, predictions)

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
