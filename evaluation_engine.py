import logging
import random
from collections import defaultdict
from simulation_engine import SimulationEngine
from routing_engine import find_best_path

# Configure robust logging exactly as requested
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

class EvaluationEngine:
    def __init__(self, ticks_to_evaluate=300):
        self.ticks = ticks_to_evaluate
        self.engine = SimulationEngine()
        
        # Multi-stage trackers
        self.predictions_5s = defaultdict(set)
        
        # True Positive / False Positive tracking
        self.TP_congestion = 0
        self.FP_congestion = 0

        # Routing checks
        self.route_successes = 0
        self.route_failures = 0
        
        # Physics checking
        self.physics_violations = 0
        
    def evaluate(self):
        logging.info(f"Starting Predictive Engine Evaluation Loop over {self.ticks} ticks...")
        
        for t in range(self.ticks):
            # Artificially force congestion waves so the system actually gets stressed
            if t % 50 == 0:
                self.engine.manual_phase = random.choice(["entry", "halftime", "emergency"])
                logging.info(f"--- Simulating Phase Shift: {self.engine.manual_phase.upper()} ---")
            elif t % 50 == 25:
                self.engine.manual_phase = "auto"

            self.engine.step()
            state = self.engine.get_state()
            current_tick = state["tick"]
            
            # ──────────────────────────────────────────────
            # 1. Evaluate Routing Correctness
            # ──────────────────────────────────────────────
            start = f"{random.choice(['A','B','C','D','E'])}{random.randint(1,5)}"
            end = f"{random.choice(['A','B','C','D','E'])}{random.randint(1,5)}"
            
            # Pass predictions explicitly to use the fully weighted Risk-Aware engine!
            route = find_best_path(state["zones"], start, end, state["predictions"])
            path = route["path"]
            
            failed_route = False
            for z_id in path[1:-1]:
                zone_data = next((z for z in state["zones"] if z["id"] == z_id), None)
                if zone_data and zone_data.get("congestion_score", 0) > 75:
                    failed_route = True
                    break
                    
            if failed_route:
                self.route_failures += 1
                logging.debug(f"[Tick {current_tick}] Route failure constraint: {start}->{end} routed via critical zone!")
            else:
                self.route_successes += 1
                
            # ──────────────────────────────────────────────
            # 2. Track Simulation Realism (Bounds checks)
            # ──────────────────────────────────────────────
            for agent in self.engine.agents:
                x, y = agent.position
                if x < 0 or x > 500 or y < 0 or y > 500:
                    self.physics_violations += 1
                    logging.debug(f"[Tick {current_tick}] Physics Violation: Agent transported OOB at {(x,y)}")
            
            # ──────────────────────────────────────────────
            # 3. Track Predictions (vs Real Outputs)
            # ──────────────────────────────────────────────
            true_congested = {z["id"] for z in state["zones"] if z.get("congestion_score", 0) > 75}
            
            # Check 5s predictions made ~3 ticks ago (= 6 seconds of sim physics)
            check_tick_5s = current_tick - 3
            if check_tick_5s in self.predictions_5s:
                predicted = self.predictions_5s[check_tick_5s]
                # Hit scanning
                for p_zone in predicted:
                    if p_zone in true_congested:
                        self.TP_congestion += 1
                        logging.debug(f"[Tick {current_tick}] Accurate +5s Prediction Hit: {p_zone} jammed as expected.")
                    else:
                        self.FP_congestion += 1
                        logging.debug(f"[Tick {current_tick}] +5s False Positive: {p_zone} predicted to jam but did not.")
                        
            # Buffer current predictions for evaluation in exactly 3 ticks 
            preds = state["predictions"]
            self.predictions_5s[current_tick] = set(preds.get("plus_5s", []))
            
        return self.calculate_score()
        
    def calculate_score(self):
        logging.info("\n" + "=" * 55)
        logging.info("  EVALUATION MATRIX RUN COMPLETE")
        logging.info("  Normalizing Accuracies (0-100% scale)...")
        logging.info("=" * 55)
        
        # 1. Congestion Accuracy (35%)
        # Hit rate logic
        total_predictions_made = self.TP_congestion + self.FP_congestion
        if total_predictions_made > 0:
            hit_rate = self.TP_congestion / total_predictions_made
        else:
            hit_rate = 1.0 # Awarded if zero errors
            
        acc_score = hit_rate * 35.0
        logging.info(f" [1] Congestion Prediction Hit Rate:   {hit_rate*100:6.1f}%  | Weighted: {acc_score:5.2f}/35.0")
        
        # 2. False Positive Reduction (25%)
        fp_rate = self.FP_congestion / total_predictions_made if total_predictions_made > 0 else 0
        fp_score = (1.0 - fp_rate) * 25.0
        logging.info(f" [2] False Positive Optimization:      {(1.0-fp_rate)*100:6.1f}%  | Weighted: {fp_score:5.2f}/25.0")
        
        # 3. Routing Correctness (25%)
        route_acc = self.route_successes / max(1, self.route_successes + self.route_failures)
        route_score = route_acc * 25.0
        logging.info(f" [3] Dijkstra Bypass Correctness:      {route_acc*100:6.1f}%  | Weighted: {route_score:5.2f}/25.0")
        
        # 4. Simulation Realism (15%)
        # Base multiplier deducting scaled error percentiles per OOB clipping 
        realism_acc = max(0.0, 1.0 - (self.physics_violations * 0.05))
        realism_score = realism_acc * 15.0
        logging.info(f" [4] Physics Validation Envelope:      {realism_acc*100:6.1f}%  | Weighted: {realism_score:5.2f}/15.0")
        
        final_score = acc_score + fp_score + route_score + realism_score
        
        logging.info("-" * 55)
        logging.info(f"  FINAL PIPELINE ACCURACY RATING:      {final_score:5.2f}%")
        logging.info("-" * 55)

if __name__ == "__main__":
    evaluator = EvaluationEngine(ticks_to_evaluate=300)
    evaluator.evaluate()
