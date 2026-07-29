"""Handles only the network side: fetch a URL under a hard timeout,
with a global concurrency cap so a burst can't exhaust connections."""
import asyncio
import time

import httpx

from app.config import settings
from app.utils.logger import log

_semaphore = asyncio.Semaphore(settings.max_concurrent_audits)


class FetchError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class FetchResult:
    def __init__(self, response: httpx.Response, elapsed_ms: int):
        self.response = response
        self.elapsed_ms = elapsed_ms


async def fetch(url: str) -> FetchResult:
    async with _semaphore:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=settings.fetch_timeout_seconds,
                follow_redirects=True,
                max_redirects=settings.max_redirects,
                headers={"User-Agent": "URL-Audit-Service/1.0 (+digitalheroesco.com)"},
            ) as client:
                response = await client.get(url)
        except httpx.TimeoutException as exc:
            log.warning("fetch_timeout", url=url, error=str(exc))
            raise FetchError(504, "upstream_timeout", f"Target did not respond within {settings.fetch_timeout_seconds}s")
        except httpx.TooManyRedirects:
            raise FetchError(400, "too_many_redirects", "Target exceeded the allowed redirect chain")
        except httpx.RequestError as exc:
            log.warning("fetch_failed", url=url, error=str(exc))
            raise FetchError(502, "upstream_unreachable", f"Could not reach target: {exc}")

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return FetchResult(response=response, elapsed_ms=elapsed_ms)
