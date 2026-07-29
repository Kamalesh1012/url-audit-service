from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from app.utils.validators import is_blocked_host


class AuditRequest(BaseModel):
    url: AnyHttpUrl = Field(..., description="Publicly reachable http(s) URL to audit")

    @field_validator("url")
    @classmethod
    def block_local_targets(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        if is_blocked_host(v.host or ""):
            raise ValueError("URL host is not allowed")
        return v
