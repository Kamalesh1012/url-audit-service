from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OpenGraphTags(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None


class AuditResult(BaseModel):
    url: str
    status_code: int
    response_time_ms: int

    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: int
    canonical_url: Optional[str] = None
    robots_tag: Optional[str] = None
    og_tags: OpenGraphTags

    errors: list[str] = []
    warnings: list[str] = []
    seo_score: int

    audited_at: datetime
    from_cache: bool = False


class ErrorDetail(BaseModel):
    error: str
    message: str
    request_id: str


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
