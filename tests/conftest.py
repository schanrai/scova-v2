# Pytest configuration and shared fixtures
import pytest
from fastapi.testclient import TestClient

from py_app.main import app
from py_app.auth import verify_jwt, get_settings

# Minimal settings for tests that hit run_research (avoids loading .env)
_mock_settings = type("_MockSettings", (), {
    "openrouter_base_url": "https://openrouter.ai/api/v1",
    "openrouter_api_key": "test-key",
})()


@pytest.fixture
def client():
    """TestClient with JWT and settings overridden so tests need no real env or token."""
    app.dependency_overrides[verify_jwt] = lambda: {"sub": "test-user-id", "email": "test@example.com"}
    app.dependency_overrides[get_settings] = lambda: _mock_settings
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth():
    """TestClient with only settings overridden; JWT still required (for 401 tests)."""
    app.dependency_overrides[get_settings] = lambda: _mock_settings
    yield TestClient(app)
    app.dependency_overrides.clear()
