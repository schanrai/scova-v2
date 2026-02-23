"""
Tests for py_app.services.llm_client (Task 2c).
- Pure function: classify_openrouter_error(429/500/400 with context-length message).
- Mocked httpx (respx): 4 client functions send correct model, temperature, Authorization; 429 propagates.
"""
import json
import pytest
import respx
import httpx
from fastapi import HTTPException

from py_app.services.llm_client import (
    classify_openrouter_error,
    get_llm_research,
    get_structured_data,
    get_detailed_analysis,
    get_detailed_analysis_with_citations,
    LLMConfig,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = "test-api-key"


# ---- classify_openrouter_error ----
def test_classify_openrouter_error_429_raises():
    with pytest.raises(HTTPException) as exc_info:
        classify_openrouter_error(429, {})
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Rate limit exceeded"


def test_classify_openrouter_error_500_raises_503():
    with pytest.raises(HTTPException) as exc_info:
        classify_openrouter_error(500, {"error": {"message": "Internal error"}})
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Service error"


def test_classify_openrouter_error_400_context_length_raises():
    with pytest.raises(HTTPException) as exc_info:
        classify_openrouter_error(
            400,
            {"error": {"message": "maximum context length exceeded"}},
        )
    assert exc_info.value.status_code == 400
    assert "context length" in str(exc_info.value.detail).lower()


def test_classify_openrouter_error_400_other_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        classify_openrouter_error(400, {"error": {"message": "Bad request"}})
    assert exc_info.value.status_code == 400


# ---- Mocked LLM client: 4 functions ----
def _make_ok_response(content: str = "test") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": content}}],
        },
    )


@pytest.mark.asyncio
@respx.mock
async def test_get_llm_research_sends_model_and_auth():
    route = respx.post(OPENROUTER_URL).mock(return_value=_make_ok_response())
    async with httpx.AsyncClient() as client:
        await get_llm_research(
            "prompt",
            "openai/gpt-4o",
            client,
            "https://openrouter.ai/api/v1",
            API_KEY,
        )
    assert route.called
    req = route.calls.last.request
    assert req.headers.get("Authorization") == f"Bearer {API_KEY}"
    body = json.loads(req.content)
    assert body["model"] == "openai/gpt-4o"
    assert body["messages"] == [{"role": "user", "content": "prompt"}]


@pytest.mark.asyncio
@respx.mock
async def test_get_structured_data_sends_correct_model_and_temperature():
    route = respx.post(OPENROUTER_URL).mock(return_value=_make_ok_response())
    async with httpx.AsyncClient() as client:
        await get_structured_data(
            "prompt",
            client,
            "https://openrouter.ai/api/v1",
            API_KEY,
        )
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["model"] == "openai/gpt-4o-mini-search-preview"
    assert body["temperature"] == 0.0
    assert body["max_tokens"] == 300
    assert route.calls.last.request.headers.get("Authorization") == f"Bearer {API_KEY}"


@pytest.mark.asyncio
@respx.mock
async def test_get_detailed_analysis_sends_correct_params():
    route = respx.post(OPENROUTER_URL).mock(return_value=_make_ok_response())
    async with httpx.AsyncClient() as client:
        await get_detailed_analysis(
            "prompt",
            client,
            "https://openrouter.ai/api/v1",
            API_KEY,
        )
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["model"] == "openai/gpt-4o-search-preview"
    assert body["temperature"] == 0.3
    assert body["max_tokens"] == 4000
    assert "plugins" not in body


@pytest.mark.asyncio
@respx.mock
async def test_get_detailed_analysis_with_citations_sends_plugins():
    route = respx.post(OPENROUTER_URL).mock(return_value=_make_ok_response())
    async with httpx.AsyncClient() as client:
        await get_detailed_analysis_with_citations(
            "prompt",
            client,
            "https://openrouter.ai/api/v1",
            API_KEY,
        )
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["model"] == "openai/gpt-4o-search-preview"
    assert body.get("plugins") == [{"id": "web", "engine": "exa", "max_results": 7}]


@pytest.mark.asyncio
@respx.mock
async def test_429_response_propagates_http_exception():
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(429, json={"error": {"message": "Too many requests"}}),
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(HTTPException) as exc_info:
            await get_structured_data(
                "prompt",
                client,
                "https://openrouter.ai/api/v1",
                API_KEY,
            )
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Rate limit exceeded"


@pytest.mark.asyncio
@respx.mock
async def test_get_llm_research_returns_content():
    respx.post(OPENROUTER_URL).mock(
        return_value=_make_ok_response("custom content"),
    )
    async with httpx.AsyncClient() as client:
        out = await get_llm_research(
            "q",
            "openai/gpt-4o",
            client,
            "https://openrouter.ai/api/v1",
            API_KEY,
        )
    assert out == "custom content"
