import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, Any, List
from app.models.metric import MetricTimeseriesPoint
from app.config import settings


class TrendAnalyzer:
    """
    Analyzes historical metric trajectories using Linear Regression.
    Predicts degradation trends, failure probabilities, and time-to-threshold breaches.
    """
    def predict_degradation(self, node_id: str, metrics: List[MetricTimeseriesPoint], current_health: float) -> Dict[str, Any]:
        if len(metrics) < 10:
            return {
                "node_id": node_id,
                "predicted_condition": "Stable / Insufficient Data",
                "failure_probability": 0.05,
                "prediction_confidence": 0.60,
                "cpu_trend_slope": 0.0,
                "memory_trend_slope": 0.0,
                "time_to_cpu_breach_min": None,
                "time_to_mem_breach_min": None,
                "recommended_action": "Continue monitoring normal operations",
                "explainability": "Baseline dataset still warming up."
            }

        # Window: up to last 30 samples
        recent = metrics[-30:]
        n = len(recent)
        # Time steps in minutes (based on 3s intervals)
        t = np.arange(n).reshape(-1, 1) * (settings.HEALTH_INTERVAL / 60.0)

        cpus = np.array([m.cpu for m in recent])
        mems = np.array([m.memory for m in recent])
        healths = np.array([m.health_score for m in recent])

        # Linear regression on CPU
        reg_cpu = LinearRegression().fit(t, cpus)
        cpu_slope = float(reg_cpu.coef_[0])  # % change per minute

        # Linear regression on Memory
        reg_mem = LinearRegression().fit(t, mems)
        mem_slope = float(reg_mem.coef_[0])

        # Linear regression on Health
        reg_health = LinearRegression().fit(t, healths)
        health_slope = float(reg_health.coef_[0])

        # Estimate time to breach critical threshold (90%)
        current_cpu = float(cpus[-1])
        current_mem = float(mems[-1])

        time_to_cpu_breach = None
        if cpu_slope > 0.5 and current_cpu < settings.CPU_CRITICAL_THRESHOLD:
            minutes_left = (settings.CPU_CRITICAL_THRESHOLD - current_cpu) / cpu_slope
            time_to_cpu_breach = round(max(0.5, minutes_left), 1)

        time_to_mem_breach = None
        if mem_slope > 0.5 and current_mem < settings.MEMORY_CRITICAL_THRESHOLD:
            minutes_left = (settings.MEMORY_CRITICAL_THRESHOLD - current_mem) / mem_slope
            time_to_mem_breach = round(max(0.5, minutes_left), 1)

        # Failure probability calculation
        fail_prob = 0.05
        predicted_condition = "NOMINAL_STABLE"
        action = "Monitor baseline telemetry"
        explanation = "Workload metrics remain within steady bounds."

        if cpu_slope > 2.0 or mem_slope > 2.0 or health_slope < -2.0:
            fail_prob = min(0.95, 0.40 + (max(cpu_slope, mem_slope) * 0.10))
            if time_to_mem_breach and time_to_mem_breach < 5.0:
                predicted_condition = "RAPID_MEMORY_LEAK_PREDICTED"
                action = "Prepare proactive container restart or memory scale-out"
                explanation = f"Memory increasing at +{mem_slope:.1f}%/min. Critical breach predicted in ~{time_to_mem_breach} mins."
            elif time_to_cpu_breach and time_to_cpu_breach < 5.0:
                predicted_condition = "CPU_SATURATION_TREND_PREDICTED"
                action = "Scale out additional container replicas to balance load"
                explanation = f"CPU ramping up at +{cpu_slope:.1f}%/min. Overload predicted in ~{time_to_cpu_breach} mins."
            else:
                predicted_condition = "PERFORMANCE_DEGRADATION_TREND"
                action = "Inspect container thread pool and connection limits"
                explanation = f"Health score degrading by {abs(health_slope):.1f} points/min."

        confidence = 0.88 if n >= 20 else 0.72

        return {
            "node_id": node_id,
            "predicted_condition": predicted_condition,
            "failure_probability": round(fail_prob, 2),
            "prediction_confidence": confidence,
            "cpu_trend_slope": round(cpu_slope, 2),
            "memory_trend_slope": round(mem_slope, 2),
            "health_trend_slope": round(health_slope, 2),
            "time_to_cpu_breach_min": time_to_cpu_breach,
            "time_to_mem_breach_min": time_to_mem_breach,
            "recommended_action": action,
            "explainability": explanation
        }


trend_analyzer = TrendAnalyzer()
