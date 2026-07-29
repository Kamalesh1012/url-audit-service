import httpx
import respx

GOOD_HTML = """
<html><head><title>A Well Optimized Page Title Here</title>
<meta name="description" content="A meta description sized to sit inside the recommended window for search snippets.">
<link rel="canonical" href="https://example.com/">
</head><body><h1>Hi</h1></body></html>
"""


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_audit_rejects_invalid_url(client):
    resp = client.post("/audit", json={"url": "not-a-url"})
    assert resp.status_code == 422


def test_audit_rejects_local_targets(client):
    resp = client.post("/audit", json={"url": "http://127.0.0.1:8000/admin"})
    assert resp.status_code == 422


@respx.mock
def test_audit_happy_path_returns_seo_fields(client):
    respx.get("https://example.com/").mock(return_value=httpx.Response(200, text=GOOD_HTML))

    resp = client.post("/audit", json={"url": "https://example.com/"})

    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    body = resp.json()
    assert body["title"] == "A Well Optimized Page Title Here"
    assert body["canonical_url"] == "https://example.com/"
    assert body["h1_count"] == 1
    assert "seo_score" in body
    assert isinstance(body["warnings"], list)
    assert body["from_cache"] is False


@respx.mock
def test_audit_second_call_is_served_from_cache(client):
    route = respx.get("https://example.com/").mock(return_value=httpx.Response(200, text=GOOD_HTML))

    first = client.post("/audit", json={"url": "https://example.com/"})
    second = client.post("/audit", json={"url": "https://example.com/"})

    assert first.json()["from_cache"] is False
    assert second.json()["from_cache"] is True
    assert route.call_count == 1


@respx.mock
def test_audit_upstream_timeout_returns_structured_504(client):
    respx.get("https://slow.example.com/").mock(side_effect=httpx.TimeoutException("boom"))

    resp = client.post("/audit", json={"url": "https://slow.example.com/"})

    assert resp.status_code == 504
    body = resp.json()
    assert body["error"] == "upstream_timeout"
    assert "request_id" in body
