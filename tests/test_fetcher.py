import httpx
import pytest
import respx

from app.services.fetcher import FetchError, fetch


@pytest.mark.asyncio
@respx.mock
async def test_fetch_returns_response_and_timing():
    respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="<html></html>"))
    result = await fetch("https://example.com/")
    assert result.response.status_code == 200
    assert result.elapsed_ms >= 0


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raises_structured_error_on_timeout():
    respx.get("https://slow.example.com/").mock(side_effect=httpx.TimeoutException("boom"))
    with pytest.raises(FetchError) as exc_info:
        await fetch("https://slow.example.com/")
    assert exc_info.value.status_code == 504
    assert exc_info.value.code == "upstream_timeout"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raises_structured_error_on_connection_failure():
    respx.get("https://down.example.com/").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(FetchError) as exc_info:
        await fetch("https://down.example.com/")
    assert exc_info.value.status_code == 502
    assert exc_info.value.code == "upstream_unreachable"
