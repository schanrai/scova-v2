"""
Tests for POST /api/research and GET /api/health (Task 2e).
Uses conftest client (JWT + settings overridden) and respx to mock LLM calls.
"""
import json
import pytest
import respx
import httpx


def _mk_response(body: str | dict) -> httpx.Response:
    if isinstance(body, dict):
        payload = {"choices": [{"message": {"content": json.dumps(body)}}]}
    else:
        payload = {"choices": [{"message": {"content": body}}]}
    return httpx.Response(200, json=payload)


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def test_health(client):
    """GET /api/health returns 200 and status ok."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.respx
def test_post_research_requires_auth(client_no_auth, respx_mock):
    """POST /api/research without JWT returns 401 (no override)."""
    r = client_no_auth.post(
        "/api/research",
        json={"company_name": "Acme", "region_focus": "Global"},
    )
    assert r.status_code == 401


def test_post_research_rejects_unsafe_input(client):
    """POST /api/research with injection in company_name returns 400 (input validation)."""
    r = client.post(
        "/api/research",
        json={
            "company_name": "Company'; DROP TABLE users--",
            "region_focus": "Global",
        },
    )
    assert r.status_code == 400
    assert "Invalid" in (r.json().get("detail") or "")


@pytest.mark.respx
def test_post_research_success(client, respx_mock):
    """POST /api/research with JWT override and mocked LLM returns 200 and full response."""
    structured_json = {
        "industry": "Tech",
        "founded": "2020",
        "website": "https://example.com",
        "headquarters": "NYC",
        "annualRevenue": "$1M",
        "employees": "50",
    }
    overview_text = """1. Company Overview (100-150 words): Acme is global.
https://acme.com/about

2. Company Background (150-350 words): Founded in 2020.
https://acme.com/history

3. Financial Overview (100-200 words): Strong revenue.
https://acme.com/investors

4. Audience Segmentation (50-75 words): B2B and B2C.
https://acme.com/audience
"""
    respx_mock.post(OPENROUTER_URL).mock(
        side_effect=[
            _mk_response(structured_json),
            _mk_response(overview_text),
            _mk_response("Marketing narrative."),
            _mk_response("Sponsorships narrative."),
            _mk_response("YouTube: @acme\n\nThen write narrative."),
            _mk_response("Strategic focus [cite](https://example.com)."),
        ]
    )
    r = client.post(
        "/api/research",
        json={
            "company_name": "Acme",
            "region_focus": "Global",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "structured_data" in data
    assert data["structured_data"]["industry"] == "Tech"
    assert "detailed_analysis" in data
    assert "metadata" in data
    assert "prompt_versions" in data["metadata"]
