"""
CloudSentinel Demo Workload Microservice
Provides health, heartbeat, workload simulation, and isolated fault injection.
Zero external dependencies required - standard library Python.
"""
import os
import sys
import json
import time
import math
import shutil
import hashlib
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

NODE_ID = os.environ.get("NODE_ID", "cs-node-web")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "web")
PORT = int(os.environ.get("PORT", "8001"))
CONTAINER_NAME = os.environ.get("CONTAINER_NAME", NODE_ID)

# Node state
START_TIME = time.time()
RESTART_COUNT = 0
IS_HEALTHY = True
ACTIVE_FAULTS = set()
LATENCY_MS = 0
MEMORY_LEAK_BUFFER = []
STRESS_STOP_EVENTS = []
DISK_STRESS_DIR = os.path.join(tempfile.gettempdir(), f"cs_disk_{NODE_ID}")

state_lock = threading.Lock()


def cpu_stress_worker(stop_event, intensity=0.95):
    """Generates CPU stress inside this process without blocking request handlers."""
    while not stop_event.is_set():
        t_end = time.time() + (0.1 * intensity)
        while time.time() < t_end:
            _ = hashlib.sha256(b"cloudsentinel_stress_hash_test_workload_sample" * 100).digest()
        # Sleep fraction for non-busy ratio
        sleep_time = 0.1 * (1.0 - intensity)
        if sleep_time > 0.005:
            time.sleep(sleep_time)


class NodeHandler(BaseHTTPRequestHandler):
    server_version = "CloudSentinel-DemoNode/1.0"

    def log_message(self, format, *args):
        # Keep logs clean; suppress excessive health polling logs
        if "GET /health" in args[0] or "GET /heartbeat" in args[0]:
            return
        super().log_message(format, *args)

    def _send_json(self, status_code, data):
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Artificial latency injection if active
        if LATENCY_MS > 0:
            time.sleep(LATENCY_MS / 1000.0)

        if path == "/health":
            self.handle_health()
        elif path == "/heartbeat":
            self.handle_heartbeat()
        elif path == "/status" or path == "/":
            self.handle_status()
        elif path == "/metrics":
            self.handle_metrics()
        else:
            self._send_json(404, {"error": "Not Found", "path": path})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        content_length = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_length > 0:
            try:
                raw_body = self.rfile.read(content_length)
                body = json.loads(raw_body.decode("utf-8"))
            except Exception:
                body = {}

        if path == "/fault/cpu":
            self.inject_cpu_fault(query, body)
        elif path == "/fault/memory":
            self.inject_memory_fault(query, body)
        elif path == "/fault/app_failure":
            self.inject_app_failure(query, body)
        elif path == "/fault/latency":
            self.inject_latency_fault(query, body)
        elif path == "/fault/disk":
            self.inject_disk_fault(query, body)
        elif path == "/fault/reset":
            self.reset_all_faults()
        elif path == "/restart_app":
            self.restart_application()
        else:
            self._send_json(404, {"error": "Unknown fault endpoint", "path": path})

    def handle_health(self):
        global IS_HEALTHY, ACTIVE_FAULTS
        with state_lock:
            healthy = IS_HEALTHY and ("APP_FAILURE" not in ACTIVE_FAULTS)
            uptime = time.time() - START_TIME
            data = {
                "status": "healthy" if healthy else "unhealthy",
                "service": SERVICE_NAME,
                "node_id": NODE_ID,
                "container_name": CONTAINER_NAME,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "version": "1.0",
                "uptime_seconds": round(uptime, 2),
                "restart_count": RESTART_COUNT,
                "active_faults": sorted(list(ACTIVE_FAULTS)),
                "latency_injected_ms": LATENCY_MS,
                "memory_buffers_mb": len(MEMORY_LEAK_BUFFER) * 10,
            }

        if healthy:
            self._send_json(200, data)
        else:
            self._send_json(500, {
                **data,
                "error": "Application endpoint failure: internal service degraded or exception thrown"
            })

    def handle_heartbeat(self):
        global ACTIVE_FAULTS
        if "HEARTBEAT_LOSS" in ACTIVE_FAULTS:
            self._send_json(503, {
                "status": "heartbeat_lost",
                "node_id": NODE_ID,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
            return

        self._send_json(200, {
            "status": "alive",
            "node_id": NODE_ID,
            "service": SERVICE_NAME,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })

    def handle_status(self):
        uptime = time.time() - START_TIME
        self._send_json(200, {
            "node_id": NODE_ID,
            "service_name": SERVICE_NAME,
            "container_name": CONTAINER_NAME,
            "port": PORT,
            "uptime_seconds": round(uptime, 2),
            "restart_count": RESTART_COUNT,
            "healthy": IS_HEALTHY,
            "active_faults": sorted(list(ACTIVE_FAULTS)),
            "system_description": f"CloudSentinel isolated workload node for {SERVICE_NAME}"
        })

    def handle_metrics(self):
        uptime = time.time() - START_TIME
        self._send_json(200, {
            "node_id": NODE_ID,
            "service": SERVICE_NAME,
            "uptime": round(uptime, 2),
            "memory_allocated_mb": len(MEMORY_LEAK_BUFFER) * 10,
            "active_faults": list(ACTIVE_FAULTS),
            "latency_ms": LATENCY_MS
        })

    def inject_cpu_fault(self, query, body):
        global ACTIVE_FAULTS
        duration = float(body.get("duration", query.get("duration", [60])[0]))
        intensity = float(body.get("intensity", query.get("intensity", [0.95])[0]))

        with state_lock:
            ACTIVE_FAULTS.add("CPU_STRESS")

        stop_evt = threading.Event()
        STRESS_STOP_EVENTS.append(stop_evt)

        # Launch 2 worker threads for multi-core stress
        for _ in range(2):
            t = threading.Thread(target=cpu_stress_worker, args=(stop_evt, intensity), daemon=True)
            t.start()

        def auto_expire():
            time.sleep(duration)
            stop_evt.set()
            with state_lock:
                ACTIVE_FAULTS.discard("CPU_STRESS")

        threading.Thread(target=auto_expire, daemon=True).start()

        self._send_json(200, {
            "action": "CPU_STRESS_INJECTED",
            "node_id": NODE_ID,
            "duration_seconds": duration,
            "intensity": intensity,
            "status": "active"
        })

    def inject_memory_fault(self, query, body):
        global ACTIVE_FAULTS, MEMORY_LEAK_BUFFER
        mb = int(body.get("mb", query.get("mb", [350])[0]))
        duration = float(body.get("duration", query.get("duration", [60])[0]))

        with state_lock:
            ACTIVE_FAULTS.add("MEMORY_STRESS")
            # Allocate chunks of 10MB bytearrays
            chunks_needed = max(1, mb // 10)
            for _ in range(chunks_needed):
                try:
                    MEMORY_LEAK_BUFFER.append(bytearray(10 * 1024 * 1024))
                except MemoryError:
                    break

        def auto_expire():
            time.sleep(duration)
            with state_lock:
                MEMORY_LEAK_BUFFER.clear()
                ACTIVE_FAULTS.discard("MEMORY_STRESS")

        threading.Thread(target=auto_expire, daemon=True).start()

        self._send_json(200, {
            "action": "MEMORY_STRESS_INJECTED",
            "node_id": NODE_ID,
            "allocated_mb": len(MEMORY_LEAK_BUFFER) * 10,
            "duration_seconds": duration,
            "status": "active"
        })

    def inject_app_failure(self, query, body):
        global IS_HEALTHY, ACTIVE_FAULTS
        with state_lock:
            IS_HEALTHY = False
            ACTIVE_FAULTS.add("APP_FAILURE")

        self._send_json(200, {
            "action": "APPLICATION_FAILURE_INJECTED",
            "node_id": NODE_ID,
            "note": "Health endpoint will now return HTTP 500 error",
            "status": "active"
        })

    def inject_latency_fault(self, query, body):
        global LATENCY_MS, ACTIVE_FAULTS
        delay = int(body.get("delay_ms", query.get("delay_ms", [2500])[0]))
        duration = float(body.get("duration", query.get("duration", [60])[0]))

        with state_lock:
            LATENCY_MS = delay
            ACTIVE_FAULTS.add("NETWORK_LATENCY")

        def auto_expire():
            time.sleep(duration)
            with state_lock:
                global LATENCY_MS
                LATENCY_MS = 0
                ACTIVE_FAULTS.discard("NETWORK_LATENCY")

        threading.Thread(target=auto_expire, daemon=True).start()

        self._send_json(200, {
            "action": "LATENCY_INJECTED",
            "node_id": NODE_ID,
            "delay_ms": delay,
            "duration_seconds": duration,
            "status": "active"
        })

    def inject_disk_fault(self, query, body):
        global ACTIVE_FAULTS
        size_mb = int(body.get("size_mb", query.get("size_mb", [150])[0]))
        duration = float(body.get("duration", query.get("duration", [60])[0]))

        try:
            os.makedirs(DISK_STRESS_DIR, exist_ok=True)
            chunk = b"X" * (1024 * 1024)
            file_path = os.path.join(DISK_STRESS_DIR, "stress_payload.dat")
            with open(file_path, "wb") as f:
                for _ in range(size_mb):
                    f.write(chunk)
            with state_lock:
                ACTIVE_FAULTS.add("DISK_PRESSURE")
        except Exception as e:
            self._send_json(500, {"error": str(e)})
            return

        def auto_expire():
            time.sleep(duration)
            try:
                shutil.rmtree(DISK_STRESS_DIR, ignore_errors=True)
            except Exception:
                pass
            with state_lock:
                ACTIVE_FAULTS.discard("DISK_PRESSURE")

        threading.Thread(target=auto_expire, daemon=True).start()

        self._send_json(200, {
            "action": "DISK_PRESSURE_INJECTED",
            "node_id": NODE_ID,
            "written_mb": size_mb,
            "path": DISK_STRESS_DIR,
            "duration_seconds": duration,
            "status": "active"
        })

    def reset_all_faults(self):
        global IS_HEALTHY, ACTIVE_FAULTS, LATENCY_MS, MEMORY_LEAK_BUFFER
        with state_lock:
            IS_HEALTHY = True
            ACTIVE_FAULTS.clear()
            LATENCY_MS = 0
            MEMORY_LEAK_BUFFER.clear()
            for evt in STRESS_STOP_EVENTS:
                evt.set()
            STRESS_STOP_EVENTS.clear()

        try:
            shutil.rmtree(DISK_STRESS_DIR, ignore_errors=True)
        except Exception:
            pass

        self._send_json(200, {
            "action": "ALL_FAULTS_RESET",
            "node_id": NODE_ID,
            "healthy": True,
            "status": "NORMAL"
        })

    def restart_application(self):
        """Simulates restarting the application layer without killing the Docker container."""
        global RESTART_COUNT, IS_HEALTHY, ACTIVE_FAULTS, LATENCY_MS, MEMORY_LEAK_BUFFER, START_TIME
        with state_lock:
            RESTART_COUNT += 1
            START_TIME = time.time()
            IS_HEALTHY = True
            ACTIVE_FAULTS.clear()
            LATENCY_MS = 0
            MEMORY_LEAK_BUFFER.clear()
            for evt in STRESS_STOP_EVENTS:
                evt.set()
            STRESS_STOP_EVENTS.clear()

        try:
            shutil.rmtree(DISK_STRESS_DIR, ignore_errors=True)
        except Exception:
            pass

        self._send_json(200, {
            "action": "APPLICATION_RESTARTED",
            "node_id": NODE_ID,
            "service_name": SERVICE_NAME,
            "restart_count": RESTART_COUNT,
            "status": "healthy"
        })


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), NodeHandler)
    print(f"CloudSentinel node [{NODE_ID}] for service [{SERVICE_NAME}] listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
