"""
NeuroVenue OS — Simulation Engine
==================================
Simulates crowd dynamics across a 5x5 venue grid (A1–E5).
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


# ──────────────────────────────────────────────
# Constants (also used by routing_engine.py)
# ──────────────────────────────────────────────

ROWS = ["A", "B", "C", "D", "E"]
COLS = [1, 2, 3, 4, 5]
TICK_INTERVAL = 3  # seconds

GATE_ZONES = {"A1", "A5", "E1", "E5"}
FOOD_ZONES = {"B2", "B4", "D2", "D4"}


# ──────────────────────────────────────────────
# Zone generator (user-defined core logic)
# ──────────────────────────────────────────────

def generate_zones():
    zones = []
    for i in range(5):
        for j in range(5):
            zone_id = chr(65 + i) + str(j + 1)
            zones.append({
                "id": zone_id,
                "density": random.randint(0, 100),
                "avg_speed": round(random.uniform(0.5, 1.5), 2),
                "wait_time": random.randint(10, 300)
            })
    return zones


# ──────────────────────────────────────────────
# Helpers (also used by routing_engine.py)
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Spike modifiers (entry time / halftime realism)
# ──────────────────────────────────────────────

def apply_entry_spike(zones: list[dict]):
    """Simulate high density near gates during entry time."""
    for zone in zones:
        if zone["id"] in GATE_ZONES:
            zone["density"] = min(100, zone["density"] + random.randint(20, 50))
            zone["avg_speed"] = round(max(0.5, zone["avg_speed"] - 0.3), 2)
            zone["wait_time"] = zone["wait_time"] + random.randint(30, 120)


def apply_halftime_spike(zones: list[dict]):
    """Simulate high density near food areas during halftime."""
    for zone in zones:
        if zone["id"] in FOOD_ZONES:
            zone["density"] = min(100, zone["density"] + random.randint(25, 55))
            zone["avg_speed"] = round(max(0.5, zone["avg_speed"] - 0.4), 2)
            zone["wait_time"] = zone["wait_time"] + random.randint(40, 150)


def apply_emergency_spike(zones: list[dict]):
    """Simulate a sudden evacuation with extremely high densities across the board."""
    for zone in zones:
        zone["density"] = min(100, zone["density"] + random.randint(40, 80))
        zone["avg_speed"] = round(max(0.1, zone["avg_speed"] - 0.8), 2)
        zone["wait_time"] = zone["wait_time"] + random.randint(100, 300)


# ──────────────────────────────────────────────
# Simulation Engine (class interface for routing_engine.py)
# ──────────────────────────────────────────────

class SimulationEngine:
    """
    Wraps generate_zones() with tick-based state management.
    Each step regenerates zone data and applies event-phase spikes.
    """

    PHASES = ["entry", "main_event", "halftime", "second_half", "exit", "idle"]

    def __init__(self):
        self.tick: int = 0
        self.zones_list: list[dict] = generate_zones()
        self.manual_phase = "auto"

    def _get_phase(self) -> str:
        """Rotate through event phases based on tick count or manual override."""
        if self.manual_phase != "auto":
            return self.manual_phase
            
        cycle = self.tick % 30
        if cycle < 5:
            return "entry"
        elif cycle < 12:
            return "main_event"
        elif cycle < 18:
            return "halftime"
        elif cycle < 24:
            return "second_half"
        elif cycle < 28:
            return "exit"
        else:
            return "idle"

    def step(self):
        """Advance one tick: regenerate zones and apply phase-specific spikes."""
        self.zones_list = generate_zones()
        phase = self._get_phase()

        if phase == "entry" or phase == "exit":
            apply_entry_spike(self.zones_list)
        elif phase == "halftime":
            apply_halftime_spike(self.zones_list)
        elif phase == "emergency":
            apply_emergency_spike(self.zones_list)

        self.tick += 1

    def get_state(self) -> dict:
        """Return current state as JSON-serializable dict."""
        return {
            "tick": self.tick,
            "phase": self._get_phase(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "zones": self.zones_list,
        }


# ──────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────

def main():
    engine = SimulationEngine()

    print("=" * 60)
    print("  NeuroVenue OS — Simulation Engine v0.2.0")
    print("  25 Zones (A1–E5) | Tick interval: 3s")
    print("  Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        while True:
            engine.step()
            state = engine.get_state()
            print(json.dumps(state, indent=2))
            print(f"\n--- Tick {state['tick']} | Phase: {state['phase']} ---\n")
            time.sleep(TICK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n[NeuroVenue OS] Simulation stopped.")
        print(f"[NeuroVenue OS] Final tick: {engine.tick}")
        print(f"[NeuroVenue OS] Total simulated time: {engine.tick * TICK_INTERVAL}s")


if __name__ == "__main__":
    main()
