from typing import Dict, Any
from app.config import settings
import logging

logger = logging.getLogger("cloudsentinel.health_scoring")


class HealthScoreEngine:
    """
    Intelligent multi-factor health score calculator.
    Weights:
      CPU Score        : 20%
      RAM Score        : 20%
      Network Score    : 10%
      Response Time    : 20%
      Heartbeat        : 20%
      Application      : 10%
    Total normalized score: 0 to 100
    """
    def __init__(self):
        self.w_cpu = settings.WEIGHT_CPU
        self.w_ram = settings.WEIGHT_RAM
        self.w_net = settings.WEIGHT_NETWORK
        self.w_res = settings.WEIGHT_RESPONSE_TIME
        self.w_hb = settings.WEIGHT_HEARTBEAT
        self.w_app = settings.WEIGHT_APPLICATION

    def update_weights(self, w_cpu: float = None, w_ram: float = None,
                       w_net: float = None, w_res: float = None,
                       w_hb: float = None, w_app: float = None):
        if w_cpu is not None: self.w_cpu = w_cpu
        if w_ram is not None: self.w_ram = w_ram
        if w_net is not None: self.w_net = w_net
        if w_res is not None: self.w_res = w_res
        if w_hb is not None: self.w_hb = w_hb
        if w_app is not None: self.w_app = w_app

        total = self.w_cpu + self.w_ram + self.w_net + self.w_res + self.w_hb + self.w_app
        if total > 0 and abs(total - 1.0) > 0.001:
            # Normalize to 1.0
            self.w_cpu /= total
            self.w_ram /= total
            self.w_net /= total
            self.w_res /= total
            self.w_hb /= total
            self.w_app /= total

    def calculate(
        self,
        cpu_percent: float,
        memory_percent: float,
        network_rx_rate_kb: float,
        response_time_ms: float,
        heartbeat: bool,
        application_healthy: bool,
        container_running: bool
    ) -> Dict[str, Any]:
        """
        Calculates individual sub-scores and composite health score [0 - 100].
        If container is stopped/dead or heartbeat is completely missing, penalty is applied.
        """
        if not container_running:
            return {
                "health_score": 0.0,
                "cpu_score": 0.0,
                "ram_score": 0.0,
                "network_score": 0.0,
                "response_score": 0.0,
                "heartbeat_score": 0.0,
                "application_score": 0.0,
            }

        # 1. CPU Score [0 - 100]: Normal utilization gets high score; >90% drops rapidly
        if cpu_percent <= 60.0:
            cpu_score = 100.0 - (cpu_percent * 0.25)
        elif cpu_percent <= 85.0:
            cpu_score = 85.0 - ((cpu_percent - 60.0) * 1.8)
        else:
            cpu_score = max(0.0, 40.0 - ((cpu_percent - 85.0) * 2.6))

        # 2. RAM Score [0 - 100]
        if memory_percent <= 65.0:
            ram_score = 100.0 - (memory_percent * 0.2)
        elif memory_percent <= 85.0:
            ram_score = 87.0 - ((memory_percent - 65.0) * 2.0)
        else:
            ram_score = max(0.0, 47.0 - ((memory_percent - 85.0) * 3.1))

        # 3. Network Score [0 - 100]
        # Normal traffic receives high score; excessive congestion drops score
        if network_rx_rate_kb < 10000:
            network_score = 98.0
        elif network_rx_rate_kb < 50000:
            network_score = 80.0
        else:
            network_score = 50.0

        # 4. Response Time Score [0 - 100]
        if response_time_ms <= 150.0:
            response_score = 100.0
        elif response_time_ms <= 500.0:
            response_score = 100.0 - ((response_time_ms - 150.0) / 350.0 * 25.0)
        elif response_time_ms <= 2000.0:
            response_score = 75.0 - ((response_time_ms - 500.0) / 1500.0 * 50.0)
        else:
            response_score = max(0.0, 25.0 - ((response_time_ms - 2000.0) / 2000.0 * 25.0))

        # 5. Heartbeat Score [0 - 100]
        heartbeat_score = 100.0 if heartbeat else 0.0

        # 6. Application Score [0 - 100]
        application_score = 100.0 if application_healthy else 0.0

        # Composite Weighted Score
        composite = (
            (cpu_score * self.w_cpu) +
            (ram_score * self.w_ram) +
            (network_score * self.w_net) +
            (response_score * self.w_res) +
            (heartbeat_score * self.w_hb) +
            (application_score * self.w_app)
        )

        final_score = round(max(0.0, min(100.0, composite)), 1)

        return {
            "health_score": final_score,
            "cpu_score": round(cpu_score, 1),
            "ram_score": round(ram_score, 1),
            "network_score": round(network_score, 1),
            "response_score": round(response_score, 1),
            "heartbeat_score": round(heartbeat_score, 1),
            "application_score": round(application_score, 1),
        }


health_score_engine = HealthScoreEngine()
