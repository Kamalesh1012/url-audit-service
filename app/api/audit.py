from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.models.request import AuditRequest
from app.models.response import AuditResult
from app.services import analyzer
from app.services.analyzer import AnalysisError
from app.services.cache import AuditCache, RedisCache
from app.services.fetcher import fetch
from app.utils.logger import log

router = APIRouter()
_cache = AuditCache(backend=RedisCache())


@router.post("/audit", response_model=AuditResult)
async def audit(request: Request, payload: AuditRequest):
    url = str(payload.url)

    cached = await _cache.get(url)
    if cached is not None:
        log.info("audit_cache_hit", url=url)
        return cached

    fetch_result = await fetch(url)

    try:
        analysis = analyzer.analyze(fetch_result.response.text, fetch_result.response.status_code)
    except AnalysisError as exc:
        raise exc  # re-raised, handled by the app-level exception handler

    result = AuditResult(
        url=str(fetch_result.response.url),
        status_code=fetch_result.response.status_code,
        response_time_ms=fetch_result.elapsed_ms,
        title=analysis.title,
        meta_description=analysis.meta_description,
        h1_count=analysis.h1_count,
        canonical_url=analysis.canonical_url,
        robots_tag=analysis.robots_tag,
        og_tags=analysis.og_tags,
        errors=analysis.errors,
        warnings=analysis.warnings,
        seo_score=analysis.seo_score,
        audited_at=datetime.now(timezone.utc),
        from_cache=False,
    )

    await _cache.set(url, result)

    log.info(
        "audit_completed",
        url=url,
        status_code=result.status_code,
        seo_score=result.seo_score,
        elapsed_ms=fetch_result.elapsed_ms,
    )
    return result
