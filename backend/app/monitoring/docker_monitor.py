import time
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config import settings
from app.models.node import NodeModel, NodeStatus, InfrastructureState

logger = logging.getLogger("cloudsentinel.docker_monitor")

DEFAULT_NODES = [
    {"node_id": "cs-node-web", "container_name": "cs-node-web", "service_name": "web", "port": 8001},
    {"node_id": "cs-node-api", "container_name": "cs-node-api", "service_name": "api", "port": 8002},
    {"node_id": "cs-node-worker", "container_name": "cs-node-worker", "service_name": "worker", "port": 8003},
    {"node_id": "cs-node-auth", "container_name": "cs-node-auth", "service_name": "auth", "port": 8004},
    {"node_id": "cs-node-storage", "container_name": "cs-node-storage", "service_name": "storage", "port": 8005},
]


class DockerMonitor:
    def __init__(self):
        self.client = None
        self.is_docker_available = False
        self._prev_cpu_stats: Dict[str, Dict[str, Any]] = {}
        self._prev_net_stats: Dict[str, Dict[str, Any]] = {}
        self._simulated_nodes: Dict[str, Dict[str, Any]] = {}
        self._init_docker()
        self._init_simulated_nodes()

    def _init_docker(self):
        try:
            import docker
            self.client = docker.from_env()
            self.client.ping()
            self.is_docker_available = True
            logger.info("Successfully connected to local Docker Engine daemon.")
        except Exception as e:
            self.client = None
            self.is_docker_available = False
            logger.warning(f"Docker Engine daemon not accessible: {e}. Active mode: High-Fidelity Container Simulator.")

    def _init_simulated_nodes(self):
        now = time.time()
        for defn in DEFAULT_NODES:
            nid = defn["node_id"]
            self._simulated_nodes[nid] = {
                "node_id": nid,
                "container_name": defn["container_name"],
                "service_name": defn["service_name"],
                "port": defn["port"],
                "status": "running",
                "cpu_base": 22.0 + (hash(nid) % 15),
                "mem_base": 35.0 + (hash(nid) % 18),
                "disk_percent": 30.0 + (hash(nid) % 25),
                "network_rx_bytes": 102400,
                "network_tx_bytes": 51200,
                "restart_count": 0,
                "started_at": now - 3600,
                "active_faults": set(),
                "logs": [f"[{datetime.utcnow().strftime('%H:%M:%S')}] Service {defn['service_name']} started successfully."],
            }

    async def probe_node_http(self, port: int, host: str = "localhost") -> Dict[str, Any]:
        """Issues real HTTP probe to node's /health endpoint and measures latency."""
        url = f"http://{host}:{port}/health"
        start_t = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(url)
                duration_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "reachable": True,
                        "healthy": data.get("status") == "healthy",
                        "response_time_ms": duration_ms,
                        "active_faults": data.get("active_faults", []),
                        "restart_count": data.get("restart_count", 0),
                        "uptime_seconds": data.get("uptime_seconds", 0.0),
                    }
                else:
                    return {
                        "reachable": True,
                        "healthy": False,
                        "response_time_ms": duration_ms,
                        "active_faults": ["APP_FAILURE"],
                        "restart_count": 0,
                        "uptime_seconds": 0.0,
                    }
        except httpx.ConnectError:
            return {"reachable": False, "healthy": False, "response_time_ms": 2500.0, "active_faults": []}
        except httpx.TimeoutException:
            return {"reachable": False, "healthy": False, "response_time_ms": 3000.0, "active_faults": ["TIMEOUT"]}
        except Exception:
            return {"reachable": False, "healthy": False, "response_time_ms": 3000.0, "active_faults": []}

    def _calc_docker_cpu_percent(self, node_id: str, stats: Dict[str, Any]) -> float:
        try:
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            cpu_usage = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            precpu_usage = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_cpu = cpu_stats.get("system_cpu_usage", 0)
            system_precpu = precpu_stats.get("system_cpu_usage", 0)
            online_cpus = cpu_stats.get("online_cpus", 1) or 1

            cpu_delta = cpu_usage - precpu_usage
            system_delta = system_cpu - system_precpu

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                return round(min(100.0, cpu_percent), 2)
        except Exception:
            pass
        return 5.0

    async def get_node_telemetry(self, node_def: Dict[str, Any]) -> Dict[str, Any]:
        node_id = node_def["node_id"]
        container_name = node_def["container_name"]
        port = node_def["port"]
        service_name = node_def["service_name"]

        # First, attempt live probe on localhost:port
        http_probe = await self.probe_node_http(port)

        # 1. LIVE DOCKER MODE
        if self.is_docker_available and self.client:
            try:
                container = self.client.containers.get(container_name)
                container.reload()
                is_running = container.status == "running"
                restart_count = container.attrs.get("RestartCount", 0)
                
                # Uptime calculation
                created_str = container.attrs.get("State", {}).get("StartedAt", "")
                uptime = 0.0
                if is_running and created_str:
                    try:
                        # e.g. 2026-10-08T04:15:20.123456Z
                        t_started = datetime.fromisoformat(created_str.replace("Z", "+00:00")).timestamp()
                        uptime = round(time.time() - t_started, 1)
                    except Exception:
                        uptime = 100.0

                cpu_pct = 5.0
                mem_pct = 15.0
                mem_used = 120.0
                mem_limit = 1024.0
                rx_bytes = 10240
                tx_bytes = 8192
                rx_rate = 5.0
                tx_rate = 4.0

                if is_running:
                    try:
                        stats = container.stats(stream=False)
                        cpu_pct = self._calc_docker_cpu_percent(node_id, stats)
                        memory_stats = stats.get("memory_stats", {})
                        mem_used = round(memory_stats.get("usage", 120 * 1024 * 1024) / (1024 * 1024), 2)
                        mem_limit = round(memory_stats.get("limit", 1024 * 1024 * 1024) / (1024 * 1024), 2)
                        mem_pct = round((mem_used / mem_limit) * 100.0, 2) if mem_limit > 0 else 10.0

                        networks = stats.get("networks", {})
                        if networks:
                            eth0 = list(networks.values())[0]
                            rx_bytes = eth0.get("rx_bytes", 10240)
                            tx_bytes = eth0.get("tx_bytes", 8192)
                            prev = self._prev_net_stats.get(node_id, {"rx": rx_bytes, "tx": tx_bytes, "time": time.time()})
                            dt = max(0.1, time.time() - prev["time"])
                            rx_rate = round(max(0.0, (rx_bytes - prev["rx"]) / 1024.0 / dt), 2)
                            tx_rate = round(max(0.0, (tx_bytes - prev["tx"]) / 1024.0 / dt), 2)
                            self._prev_net_stats[node_id] = {"rx": rx_bytes, "tx": tx_bytes, "time": time.time()}
                    except Exception as err:
                        logger.debug(f"Could not read detailed Docker stats for {node_id}: {err}")

                # Combine with HTTP probe
                app_healthy = http_probe["healthy"] if http_probe["reachable"] else (is_running and False)
                heartbeat = is_running and http_probe["reachable"]
                resp_time = http_probe["response_time_ms"] if http_probe["reachable"] else 2000.0
                active_faults = http_probe.get("active_faults", [])

                return {
                    "node_id": node_id,
                    "container_name": container_name,
                    "container_id": container.id[:12],
                    "service_name": service_name,
                    "port": port,
                    "status": NodeStatus.RUNNING if is_running else NodeStatus.STOPPED,
                    "cpu_percent": cpu_pct,
                    "memory_percent": mem_pct,
                    "memory_used_mb": mem_used,
                    "memory_limit_mb": mem_limit,
                    "disk_percent": 25.0,
                    "network_rx_bytes": rx_bytes,
                    "network_tx_bytes": tx_bytes,
                    "network_rx_rate_kb": rx_rate,
                    "network_tx_rate_kb": tx_rate,
                    "response_time_ms": resp_time,
                    "heartbeat": heartbeat,
                    "application_healthy": app_healthy,
                    "restart_count": restart_count,
                    "uptime_seconds": uptime,
                    "active_faults": active_faults,
                    "is_simulated": False,
                }
            except Exception as e:
                logger.debug(f"Container {container_name} not found in Docker: {e}. Falling back to simulation.")

        # 2. HIGH-FIDELITY SIMULATED / HYBRID MODE
        sim = self._simulated_nodes.get(node_id)
        is_running = sim["status"] == "running"
        active_faults = list(sim["active_faults"])

        # If HTTP probe succeeded, honor live endpoint data
        if http_probe["reachable"]:
            app_healthy = http_probe["healthy"]
            resp_time = http_probe["response_time_ms"]
            if http_probe.get("active_faults"):
                active_faults = list(set(active_faults + http_probe["active_faults"]))
        else:
            app_healthy = is_running and ("APP_FAILURE" not in active_faults)
            resp_time = 35.0 + (hash(node_id + str(time.time() // 5)) % 40)
            if "NETWORK_LATENCY" in active_faults:
                resp_time += 2500.0

        # CPU calculation with jitter
        import math
        jitter = math.sin(time.time() / 10.0 + hash(node_id)) * 4.0
        cpu_val = max(1.0, min(99.0, sim["cpu_base"] + jitter))
        if "CPU_STRESS" in active_faults:
            cpu_val = 94.5 + (hash(str(time.time())) % 4)

        # RAM calculation
        mem_val = sim["mem_base"] + (math.cos(time.time() / 15.0) * 2.0)
        if "MEMORY_STRESS" in active_faults:
            mem_val = 95.8

        disk_val = sim["disk_percent"]
        if "DISK_PRESSURE" in active_faults:
            disk_val = 96.0

        if not is_running:
            cpu_val = 0.0
            mem_val = 0.0
            resp_time = 3000.0
            heartbeat = False
            app_healthy = False
        else:
            heartbeat = "HEARTBEAT_LOSS" not in active_faults and ("CONTAINER_STOP" not in active_faults)

        uptime = round(time.time() - sim["started_at"], 1) if is_running else 0.0

        return {
            "node_id": node_id,
            "container_name": container_name,
            "container_id": f"sim-{hash(node_id) & 0xffffff:06x}",
            "service_name": service_name,
            "port": port,
            "status": NodeStatus.RUNNING if is_running else NodeStatus.STOPPED,
            "cpu_percent": round(cpu_val, 1),
            "memory_percent": round(mem_val, 1),
            "memory_used_mb": round((mem_val / 100.0) * 1024, 1),
            "memory_limit_mb": 1024.0,
            "disk_percent": round(disk_val, 1),
            "network_rx_bytes": sim["network_rx_bytes"] + int(time.time() * 100) % 50000,
            "network_tx_bytes": sim["network_tx_bytes"] + int(time.time() * 80) % 40000,
            "network_rx_rate_kb": round(15.0 + abs(jitter * 2), 2),
            "network_tx_rate_kb": round(10.0 + abs(jitter), 2),
            "response_time_ms": round(resp_time, 1),
            "heartbeat": heartbeat,
            "application_healthy": app_healthy,
            "restart_count": sim["restart_count"],
            "uptime_seconds": uptime,
            "active_faults": active_faults,
            "is_simulated": True,
        }

    async def execute_container_action(self, node_id: str, action: str) -> Dict[str, Any]:
        """
        Executes Docker container action (restart, stop, start, recreate)
        using Docker SDK if live container exists, otherwise simulator.
        """
        sim = self._simulated_nodes.get(node_id)
        node_def = next((n for n in DEFAULT_NODES if n["node_id"] == node_id), None)
        container_name = node_def["container_name"] if node_def else node_id

        # Live Docker Action Execution
        if self.is_docker_available and self.client:
            try:
                container = self.client.containers.get(container_name)
                if action == "restart":
                    container.restart(timeout=5)
                    return {"success": True, "action": "restart", "target": container_name, "message": "Docker container restarted successfully."}
                elif action == "stop":
                    container.stop(timeout=5)
                    return {"success": True, "action": "stop", "target": container_name, "message": "Docker container stopped."}
                elif action == "start":
                    container.start()
                    return {"success": True, "action": "start", "target": container_name, "message": "Docker container started."}
                elif action == "recreate":
                    image = container.image.tags[0] if container.image.tags else "python:3.11-slim"
                    ports = container.attrs.get("HostConfig", {}).get("PortBindings", {})
                    container.stop(timeout=3)
                    container.remove()
                    # Recreate container with same name
                    self.client.containers.run(image, name=container_name, ports=ports, detach=True)
                    return {"success": True, "action": "recreate", "target": container_name, "message": "Container recreated fresh."}
            except Exception as e:
                logger.warning(f"Docker action {action} on {container_name} failed: {e}. Executing in simulator.")

        # Simulator action
        if not sim:
            return {"success": False, "error": f"Node {node_id} not found"}

        if action == "restart":
            sim["status"] = "running"
            sim["started_at"] = time.time()
            sim["restart_count"] += 1
            sim["active_faults"].clear()
            sim["logs"].append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Container restarted via recovery engine.")
            return {"success": True, "action": "restart", "target": node_id, "message": "Container restarted."}
        elif action == "stop":
            sim["status"] = "stopped"
            sim["logs"].append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Container stopped.")
            return {"success": True, "action": "stop", "target": node_id, "message": "Container stopped."}
        elif action == "start":
            sim["status"] = "running"
            sim["started_at"] = time.time()
            sim["logs"].append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Container started.")
            return {"success": True, "action": "start", "target": node_id, "message": "Container started."}
        elif action == "recreate":
            sim["status"] = "running"
            sim["started_at"] = time.time()
            sim["restart_count"] += 1
            sim["active_faults"].clear()
            sim["logs"].append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Container recreated from clean image.")
            return {"success": True, "action": "recreate", "target": node_id, "message": "Container recreated fresh."}

        return {"success": False, "error": f"Unsupported action {action}"}

    async def get_container_logs(self, node_id: str, tail: int = 50) -> List[str]:
        node_def = next((n for n in DEFAULT_NODES if n["node_id"] == node_id), None)
        container_name = node_def["container_name"] if node_def else node_id

        if self.is_docker_available and self.client:
            try:
                container = self.client.containers.get(container_name)
                raw_logs = container.logs(tail=tail).decode("utf-8", errors="replace")
                return [line for line in raw_logs.split("\n") if line.strip()]
            except Exception:
                pass

        sim = self._simulated_nodes.get(node_id)
        if sim:
            return sim.get("logs", [])[-tail:]
        return ["No logs available."]


docker_monitor = DockerMonitor()
