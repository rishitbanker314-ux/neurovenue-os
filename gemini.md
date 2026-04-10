{
  "Zone": {
    "id": "string",
    "density": "number (0-100)",
    "avg_speed": "number",
    "wait_time": "number (seconds)"
  },
  "User": {
    "id": "string",
    "current_zone": "zone_id",
    "destination": "zone_id",
    "speed": "number",
    "reaction_delay": "number (seconds)"
  },
  "Suggestion": {
    "user_id": "string",
    "recommended_path": ["zone_id"],
    "time_saved": "number (seconds)"
  }
}