from simulation_engine import generate_zones
from routing_engine import find_best_path
import time

while True:
    zones = generate_zones()
    result = find_best_path(zones, "A1", "E5")

    print("Best Path:", result)
    time.sleep(3)
