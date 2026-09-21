from pydantic import BaseModel
from enum import Enum


class CompressStrength(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ImageConvertRequest(BaseModel):
    target_format: str
    jpeg_quality: int = 92


class SplitRequest(BaseModel):
    ranges: str


class TaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class TaskStatusResponse(BaseModel):
    task_id: str
    state: TaskStatus
    progress: float | None = None
    error: str | None = None
    download_url: str | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str


class SplitInfoResponse(BaseModel):
    page_count: int
