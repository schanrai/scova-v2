"""
LLM client for OpenRouter. Port of lib/llm-client.ts (4 functions only).
getFormattedData and cleanJsonResponse are NOT ported — eliminated.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ---- Config: model names and params (not hardcoded in function bodies) ----
MODEL_STRUCTURED = "openai/gpt-4o-mini-search-preview"
MODEL_DETAILED = "openai/gpt-4o-search-preview"


@dataclass(frozen=True)
class LLMConfig:
    """Centralized model and sampling params for LLM calls."""

    structured_model: str = MODEL_STRUCTURED
    structured_temperature: float = 0.0
    structured_top_p: float = 0.0
    structured_max_tokens: int = 300

    detailed_model: str = MODEL_DETAILED
    detailed_temperature: float = 0.3
    detailed_top_p: float = 0.9
    detailed_max_tokens: int = 4000

    exa_plugin_max_results: int = 7


def classify_openrouter_error(status_code: int, response_body: Any) -> HTTPException:
    """
    Map OpenRouter error response to HTTPException.
    429 → rate limit; 500 → service error; 400 with context-length message → token limit.
    """
    body_str = ""
    if isinstance(response_body, dict):
        body_str = json.dumps(response_body)
        msg = (response_body.get("error") or {}).get("message") or ""
        if isinstance(msg, dict):
            msg = json.dumps(msg)
    elif isinstance(response_body, str):
        body_str = response_body
        msg = response_body
    else:
        msg = str(response_body)

    if status_code == 429:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    if status_code >= 500:
        raise HTTPException(
            status_code=503,
            detail="Service error",
        )
    if status_code == 400 and (
        "maximum context length" in msg.lower() or "context length exceeded" in msg.lower()
    ):
        raise HTTPException(
            status_code=400,
            detail="Maximum context length exceeded",
        )
    raise HTTPException(
        status_code=status_code,
        detail=msg or f"OpenRouter error: {status_code}",
    )


async def _post(
    client: httpx.AsyncClient,
    url: str,
    api_key: str,
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    top_p: float,
    plugins: list[dict[str, Any]] | None = None,
) -> str:
    """POST to OpenRouter chat/completions; on non-2xx call classify_openrouter_error."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
    }
    if plugins is not None:
        body["plugins"] = plugins

    response = await client.post(url, headers=headers, json=body)
    if response.status_code != 200:
        try:
            payload = response.json()
        except Exception:
            payload = response.text
        classify_openrouter_error(response.status_code, payload)

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        logger.warning("Unexpected OpenRouter response shape: %s", e)
        raise HTTPException(status_code=502, detail="Invalid response from LLM") from e


async def get_llm_research(
    prompt: str,
    model: str,
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    *,
    config: LLMConfig | None = None,
) -> str:
    """Generic research call; model is caller-supplied."""
    cfg = config or LLMConfig()
    url = f"{base_url.rstrip('/')}/chat/completions"
    return await _post(
        client,
        url,
        api_key,
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=cfg.detailed_temperature,
        max_tokens=cfg.detailed_max_tokens,
        top_p=cfg.detailed_top_p,
    )


async def get_structured_data(
    prompt: str,
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    *,
    config: LLMConfig | None = None,
) -> str:
    """Structured data call (gpt-4o-mini-search-preview, temp=0, max_tokens=300). Returns raw string; orchestration parses with Pydantic."""
    cfg = config or LLMConfig()
    url = f"{base_url.rstrip('/')}/chat/completions"
    return await _post(
        client,
        url,
        api_key,
        model=cfg.structured_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=cfg.structured_temperature,
        max_tokens=cfg.structured_max_tokens,
        top_p=cfg.structured_top_p,
    )


async def get_detailed_analysis(
    prompt: str,
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    *,
    config: LLMConfig | None = None,
) -> str:
    """Detailed analysis (gpt-4o-search-preview, temp=0.3, max_tokens=4000). No Exa plugin."""
    cfg = config or LLMConfig()
    url = f"{base_url.rstrip('/')}/chat/completions"
    return await _post(
        client,
        url,
        api_key,
        model=cfg.detailed_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=cfg.detailed_temperature,
        max_tokens=cfg.detailed_max_tokens,
        top_p=cfg.detailed_top_p,
    )


async def get_detailed_analysis_with_citations(
    prompt: str,
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    *,
    config: LLMConfig | None = None,
) -> str:
    """Citation-heavy analysis (same model as detailed + Exa plugin, max_results=7)."""
    cfg = config or LLMConfig()
    url = f"{base_url.rstrip('/')}/chat/completions"
    plugins = [
        {"id": "web", "engine": "exa", "max_results": cfg.exa_plugin_max_results}
    ]
    return await _post(
        client,
        url,
        api_key,
        model=cfg.detailed_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=cfg.detailed_temperature,
        max_tokens=cfg.detailed_max_tokens,
        top_p=cfg.detailed_top_p,
        plugins=plugins,
    )
