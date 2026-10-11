import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.monitoring.collector import telemetry_collector
from app.monitoring.docker_monitor import DEFAULT_NODES
from app.models.node import NodeModel, NodeStatus, InfrastructureState
from app.firebase.local_fallback import local_store

# Import API Routers
from app.api.nodes import router as nodes_router
from app.api.alerts import router as alerts_router
from app.api.recovery import router as recovery_router
from app.api.diagnostics import router as diagnostics_router
from app.api.faults import router as faults_router
from app.api.predictions import router as predictions_router
from app.api.audit import router as audit_router
from app.api.reports import router as reports_router
from app.api.system import router as system_router
from app.api.websocket import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cloudsentinel.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-populate known default nodes
    logger.info("Initializing CloudSentinel Controller...")
    for defn in DEFAULT_NODES:
        node = NodeModel(
            node_id=defn["node_id"],
            container_name=defn["container_name"],
            service_name=defn["service_name"],
            port=defn["port"],
            status=NodeStatus.RUNNING,
            cpu_percent=18.5,
            memory_percent=32.0,
            disk_percent=25.0,
            network_rx_rate_kb=12.4,
            network_tx_rate_kb=8.2,
            response_time_ms=45.0,
            heartbeat=True,
            application_healthy=True,
            health_score=94.0,
            classification=InfrastructureState.HEALTHY
        )
        local_store.register_node(node)

    # Start background telemetry collector
    await telemetry_collector.start()
    logger.info("CloudSentinel Controller is fully operational.")

    yield

    # Shutdown
    logger.info("Shutting down CloudSentinel Controller...")
    await telemetry_collector.stop()


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Virtual Infrastructure Health Monitoring, Failure Detection and Self-Recovery Platform",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(nodes_router)
app.include_router(alerts_router)
app.include_router(recovery_router)
app.include_router(diagnostics_router)
app.include_router(faults_router)
app.include_router(predictions_router)
app.include_router(audit_router)
app.include_router(reports_router)
app.include_router(system_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "platform": settings.APP_NAME,
        "subtitle": "Intelligent Virtual Infrastructure Health Monitoring, Failure Detection and Self-Recovery Platform",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_status": "ONLINE",
        "mode": "DEMO_MODE" if settings.DEMO_MODE else "PRODUCTION"
    }
