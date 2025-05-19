import pytest
from fastapi.testclient import TestClient
from app.app import app
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
