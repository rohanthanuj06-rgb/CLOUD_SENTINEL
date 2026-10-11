from pydantic import BaseModel, Field
from typing import Optional


class CpuFaultRequest(BaseModel):
    node_id: str = Field(..., description="Target node ID (e.g. cs-node-web)")
    duration: float = Field(60.0, description="Duration of stress in seconds")
    intensity: float = Field(0.95, description="CPU intensity between 0.1 and 1.0")


class MemoryFaultRequest(BaseModel):
    node_id: str = Field(..., description="Target node ID")
    mb: int = Field(350, description="Megabytes of memory to leak/allocate")
    duration: float = Field(60.0, description="Duration in seconds")


class AppFailureRequest(BaseModel):
    node_id: str = Field(..., description="Target node ID")


class ContainerStopRequest(BaseModel):
    node_id: str = Field(..., description="Target node ID to stop container")


class NetworkFaultRequest(BaseModel):
    node_id: str = Field(..., description="Target node ID")
    delay_ms: int = Field(2500, description="Artificial latency delay in milliseconds")
    duration: float = Field(60.0, description="Duration in seconds")


class DiskFaultRequest(BaseModel):
    node_id: str = Field(..., description="Target node ID")
    size_mb: int = Field(150, description="Disk space pressure in MB")
    duration: float = Field(60.0, description="Duration in seconds")


class FaultResetRequest(BaseModel):
    node_id: Optional[str] = Field(None, description="Target node ID or None to reset all nodes")
