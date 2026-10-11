from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MetricSnapshot(BaseModel):
    node_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    network_rx_bytes: int
    network_tx_bytes: int
    network_rx_rate_kb: float
    network_tx_rate_kb: float
    response_time_ms: float
    heartbeat: bool
    application_healthy: bool
    health_score: float
    classification: str


class MetricTimeseriesPoint(BaseModel):
    timestamp: str
    cpu: float
    memory: float
    disk: float
    network_rx_kb: float
    network_tx_kb: float
    response_time: float
    health_score: float


class AggregatedMetric(BaseModel):
    node_id: str
    window_start: str
    window_end: str
    avg_cpu: float
    max_cpu: float
    avg_memory: float
    max_memory: float
    avg_response_time: float
    avg_health_score: float
    sample_count: int
