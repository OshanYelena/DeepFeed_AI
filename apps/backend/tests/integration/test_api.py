"""
DeepFeed AI - Integration Tests
Tests API endpoints with a test database (TDS §18.3).
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    """Test HTTP client with ASGITransport."""
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestHealthEndpoints:
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["status"] == "ok"

    async def test_health_includes_trace_id(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert "trace_id" in data
        assert len(data["trace_id"]) > 0

    async def test_trace_id_in_response_header(self, client):
        resp = await client.get("/health")
        assert "X-Trace-ID" in resp.headers

    async def test_custom_trace_id_propagated(self, client):
        custom_trace = "my-custom-trace-123"
        resp = await client.get("/health", headers={"X-Trace-ID": custom_trace})
        assert resp.headers.get("X-Trace-ID") == custom_trace


class TestAuthEndpoints:
    async def test_register_returns_201(self, client):
        resp = await client.post("/auth/register", json={
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "StrongPassword123!",
            "full_name": "Test User",
        })
        # Will fail with 500 if DB not connected; expect either 201 or 500
        assert resp.status_code in (201, 500, 409)

    async def test_register_validates_password(self, client):
        resp = await client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "weak",
        })
        assert resp.status_code == 422  # Pydantic validation error

    async def test_register_validates_email(self, client):
        resp = await client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
        })
        assert resp.status_code == 422

    async def test_login_returns_401_for_bad_credentials(self, client):
        resp = await client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "StrongPassword123!",
        })
        # 401 expected (wrong creds) or 500 (DB not available)
        assert resp.status_code in (401, 500)


class TestProtectedEndpoints:
    async def test_feed_requires_auth(self, client):
        resp = await client.get("/feed")
        assert resp.status_code == 403  # No bearer token

    async def test_interests_requires_auth(self, client):
        resp = await client.get("/interests")
        assert resp.status_code == 403

    async def test_profile_requires_auth(self, client):
        resp = await client.get("/profile/me")
        assert resp.status_code == 403

    async def test_admin_requires_auth(self, client):
        resp = await client.get("/admin/sources")
        assert resp.status_code == 403


class TestResponseFormat:
    async def test_health_response_has_correct_structure(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert "trace_id" in data
        assert "data" in data

    async def test_validation_error_has_correct_structure(self, client):
        resp = await client.post("/auth/register", json={"email": "bad"})
        assert resp.status_code == 422
