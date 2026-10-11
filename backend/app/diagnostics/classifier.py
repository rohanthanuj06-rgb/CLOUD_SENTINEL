from app.models.node import InfrastructureState, NodeStatus, NodeModel
from app.config import settings


class StateClassifier:
    """
    Intelligent node state classifier mapping multi-factor metrics,
    heartbeats, response times, and life-cycle flags into InfrastructureState.
    """
    def classify(self, node: NodeModel) -> InfrastructureState:
        # Check special overriding operational states first
        if node.status == NodeStatus.STOPPED or node.status == NodeStatus.DEAD:
            return InfrastructureState.DEAD

        if not node.heartbeat or node.missed_heartbeats >= settings.MISSED_HEARTBEATS_THRESHOLD:
            return InfrastructureState.UNRESPONSIVE

        if not node.application_healthy:
            # Container alive, but application endpoint failed
            if node.health_score <= 30.0:
                return InfrastructureState.CRITICAL
            return InfrastructureState.POOR

        # Check Overloaded conditions (severe resource bottlenecks)
        if (node.cpu_percent >= settings.CPU_CRITICAL_THRESHOLD or
                node.memory_percent >= settings.MEMORY_CRITICAL_THRESHOLD):
            return InfrastructureState.OVERLOADED

        # Check Idle / Zombie workload
        if node.cpu_percent < settings.IDLE_CPU_THRESHOLD and node.network_rx_rate_kb < 1.0:
            if node.uptime_seconds >= settings.IDLE_DURATION_SECONDS:
                return InfrastructureState.ZOMBIE
            else:
                return InfrastructureState.IDLE

        # Multi-factor Health Score bands
        score = node.health_score
        if score >= 86.0:
            return InfrastructureState.HEALTHY
        elif score >= 71.0:
            return InfrastructureState.GOOD
        elif score >= 51.0:
            return InfrastructureState.WARNING
        elif score >= 31.0:
            return InfrastructureState.POOR
        else:
            return InfrastructureState.CRITICAL


classifier = StateClassifier()
