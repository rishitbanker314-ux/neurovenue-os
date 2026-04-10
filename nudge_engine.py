"""
NeuroVenue OS — Nudge Engine
==============================
Transforms routing engine output into human-friendly,
positive-toned suggestions with optional reward messages.

Input:  Routing result (path + time_saved)
Output: Friendly nudge string

Rules:
  - Always positive tone
  - Never warn — suggest better options instead
  - Add optional reward messages for extra motivation
"""

import random


# ──────────────────────────────────────────────
# Reward messages (randomly selected)
# ──────────────────────────────────────────────

REWARDS = [
    "You're a pro at navigating crowds! 🏆",
    "Smart move — you're ahead of the pack! 💪",
    "Smooth sailing from here! 🌊",
    "You just outsmarted the crowd! 🧠",
    "VIP-level navigation right there! ⭐",
    "That's the fastest route — nice pick! ⚡",
    "Crowd? What crowd? You breezed through! 🌬️",
    "You're earning express-lane karma! 🎯",
]

EMOJIS = ["🚀", "✨", "🎯", "⚡", "🏃", "💨", "🔥", "🌟"]


# ──────────────────────────────────────────────
# Nudge generator
# ──────────────────────────────────────────────

def generate_nudge(routing_result: dict) -> str:
    """
    Takes routing output and returns a friendly suggestion.

    Args:
        routing_result: {
            "path": ["A1", "A3", "E5"],
            "time_saved": 120
        }

    Returns:
        A human-friendly nudge string.
    """
    path = routing_result.get("path", [])
    time_saved = routing_result.get("time_saved", 0)

    # Format time in a human-friendly way
    time_str = format_time(time_saved)

    # Pick the key zone to suggest (first intermediate stop)
    if len(path) > 2:
        via_zone = path[1]
        suggestion = f"Head through Zone {via_zone} to save {time_str} {random.choice(EMOJIS)}"
    elif len(path) == 2:
        suggestion = f"Go straight to {path[1]} — clear path ahead! {random.choice(EMOJIS)}"
    else:
        suggestion = f"You're already there! Enjoy the moment 🎉"

    # Build the full nudge
    nudge = suggestion

    # Add reward message for significant time savings
    if time_saved >= 60:
        nudge += f"\n  💡 {random.choice(REWARDS)}"

    return nudge


def format_time(seconds: int) -> str:
    """Convert seconds to a friendly time string."""
    if seconds < 60:
        return f"{seconds} seconds"
    minutes = seconds // 60
    remaining = seconds % 60
    if remaining == 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return f"{minutes} min {remaining}s"


# ──────────────────────────────────────────────
# Batch nudges for multiple users
# ──────────────────────────────────────────────

def generate_batch_nudges(routing_results: list[dict]) -> list[str]:
    """Generate nudges for a list of routing results."""
    return [generate_nudge(r) for r in routing_results]


# ──────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    from simulation_engine import generate_zones
    from routing_engine import find_best_path

    print("=" * 50)
    print("  NeuroVenue OS — Nudge Engine v0.1.0")
    print("=" * 50)

    # Sample routing results
    samples = [
        {"path": ["A1", "A3", "E5"], "time_saved": 120},
        {"path": ["E1", "D1", "C3"], "time_saved": 45},
        {"path": ["B2", "B3", "D4", "E5"], "time_saved": 180},
        {"path": ["A1", "E5"], "time_saved": 10},
        {"path": ["C3"], "time_saved": 0},
    ]

    print("\n  Sample nudges:\n")
    for result in samples:
        nudge = generate_nudge(result)
        print(f"  Route: {' → '.join(result['path'])}")
        print(f"  Nudge: {nudge}")
        print()

    # Live demo with simulation data
    print("─" * 50)
    print("  Live demo with simulation data:\n")

    zones = generate_zones()
    result = find_best_path(zones, "A1", "E5")
    nudge = generate_nudge(result)

    print(f"  Route: {' → '.join(result['path'])}")
    print(f"  Nudge: {nudge}")
    print()
