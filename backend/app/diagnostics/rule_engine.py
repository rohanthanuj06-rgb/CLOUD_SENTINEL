from typing import Dict, Any, List, Optional
from app.models.node import NodeModel, InfrastructureState, NodeStatus
from app.models.alert import AlertSeverity
from app.config import settings


class DiagnosticEngine:
    """
    Rule-based intelligent root-cause diagnostic engine.
    Analyzes telemetry, error states, and threshold breaches to isolate
    infrastructure failures from application crashes.
    """
    def diagnose(self, node: NodeModel) -> Optional[Dict[str, Any]]:
        evidence: List[str] = []
        cause = None
        severity = AlertSeverity.INFO
        confidence = 0.50
        recommended_action = "MONITOR"

        # Case 1: Container Stopped or Dead
        if node.status in (NodeStatus.STOPPED, NodeStatus.DEAD):
            cause = "CONTAINER_STOPPED"
            confidence = 0.99
            severity = AlertSeverity.CRITICAL
            evidence.append(f"Container status is '{node.status.value}'")
            evidence.append("Heartbeat lost completely")
            recommended_action = "RESTART_CONTAINER"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "Container daemon process has terminated unexpectedly."
            }

        # Case 2: Heartbeat Lost / Unresponsive Network
        if not node.heartbeat or node.missed_heartbeats >= settings.MISSED_HEARTBEATS_THRESHOLD:
            cause = "CONTAINER_NETWORK_FAILURE"
            confidence = 0.92
            severity = AlertSeverity.CRITICAL
            evidence.append(f"Heartbeat lost ({node.missed_heartbeats} consecutive missed intervals)")
            evidence.append("TCP connection / socket probe timed out")
            recommended_action = "RESTART_CONTAINER"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "Node network stack or process is completely unresponsive to telemetry probes."
            }

        # Case 3: Application Failure (Container running, but HTTP endpoint returns 500)
        if not node.application_healthy:
            cause = "APPLICATION_FAILURE"
            confidence = 0.95
            severity = AlertSeverity.CRITICAL
            evidence.append("Container is running and responsive on Docker socket")
            evidence.append("HTTP /health probe returned status code 500 (Internal Server Error)")
            evidence.append(f"Response latency measured at {node.response_time_ms}ms")
            recommended_action = "RESTART_APPLICATION"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "Application layer crashed while container OS environment remains active."
            }

        # Case 4: Memory Exhaustion
        if node.memory_percent >= settings.MEMORY_CRITICAL_THRESHOLD:
            cause = "MEMORY_EXHAUSTION"
            confidence = 0.94
            severity = AlertSeverity.CRITICAL
            evidence.append(f"Memory utilization at {node.memory_percent}% (threshold: {settings.MEMORY_CRITICAL_THRESHOLD}%)")
            evidence.append(f"Active memory used: {node.memory_used_mb}MB of {node.memory_limit_mb}MB limit")
            if node.response_time_ms > settings.RESPONSE_TIME_WARNING_MS:
                evidence.append(f"GC pressure causing elevated response latency: {node.response_time_ms}ms")
            recommended_action = "RESTART_CONTAINER"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "RAM allocation approaching container cgroup limit; risk of OOM-kill."
            }

        # Case 5: CPU Overload
        if node.cpu_percent >= settings.CPU_CRITICAL_THRESHOLD:
            cause = "CPU_OVERLOAD"
            confidence = 0.91
            severity = AlertSeverity.WARNING if node.health_score > 40 else AlertSeverity.CRITICAL
            evidence.append(f"CPU utilization sustained at {node.cpu_percent}%")
            if node.response_time_ms > settings.RESPONSE_TIME_WARNING_MS:
                evidence.append(f"High CPU saturation degrading response time ({node.response_time_ms}ms)")
            recommended_action = "SCALE_WORKLOAD"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "Severe CPU starvation impacting thread scheduler and query execution."
            }

        # Case 6: Disk Exhaustion Risk
        if node.disk_percent >= 90.0:
            cause = "DISK_EXHAUSTION_RISK"
            confidence = 0.88
            severity = AlertSeverity.WARNING
            evidence.append(f"Volume disk utilization is {node.disk_percent}%")
            evidence.append("Persistent logs or temporary buffer directory near capacity")
            recommended_action = "CLEAR_TEMP_BUFFERS"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "Container write layer or mounted volume running out of space."
            }

        # Case 7: Potential Zombie Workload
        if node.classification == InfrastructureState.ZOMBIE:
            cause = "POTENTIAL_ZOMBIE_WORKLOAD"
            confidence = 0.85
            severity = AlertSeverity.INFO
            evidence.append(f"CPU usage sustained below {settings.IDLE_CPU_THRESHOLD}%")
            evidence.append(f"Near-zero network activity for over {settings.IDLE_DURATION_SECONDS}s")
            evidence.append("Container holding system resources without processing traffic")
            recommended_action = "REAP_OR_CONSOLIDATE"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "Workload appears abandoned or deadlocked without terminating."
            }

        # Case 8: Elevated Warning
        if node.health_score < 70.0:
            cause = "PERFORMANCE_DEGRADATION"
            confidence = 0.75
            severity = AlertSeverity.WARNING
            if node.cpu_percent >= settings.CPU_WARNING_THRESHOLD:
                evidence.append(f"Elevated CPU at {node.cpu_percent}%")
            if node.memory_percent >= settings.MEMORY_WARNING_THRESHOLD:
                evidence.append(f"Elevated RAM at {node.memory_percent}%")
            if node.response_time_ms >= settings.RESPONSE_TIME_WARNING_MS:
                evidence.append(f"Response latency elevated ({node.response_time_ms}ms)")
            recommended_action = "MONITOR_CLOSELY"
            return {
                "cause": cause,
                "confidence": confidence,
                "severity": severity.value,
                "evidence": evidence,
                "recommended_action": recommended_action,
                "summary": "Infrastructure showing multiple stress indicators."
            }

        return None


diagnostic_engine = DiagnosticEngine()
