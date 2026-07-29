import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.api import audit as audit_module
from app.services.cache import AuditCache


class FakeRedis:
    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        self._store[key] = value


@pytest.fixture
def fake_cache():
    return AuditCache(backend=FakeRedis(), ttl_seconds=300)


@pytest.fixture
def client(fake_cache, monkeypatch):
    monkeypatch.setattr(audit_module, "_cache", fake_cache)
    return TestClient(main_module.app)
