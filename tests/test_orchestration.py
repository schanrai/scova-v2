"""
Tests for py_app.services.orchestration (Task 2d).
Mock all 6 LLM calls via respx; assert run_research returns valid ResearchResponse.
"""
import json
import pytest
import respx
import httpx

from py_app.schemas.research import ResearchRequest
from py_app.services.orchestration import run_research

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _mk_response(body: str | dict) -> httpx.Response:
    if isinstance(body, dict):
        payload = {"choices": [{"message": {"content": json.dumps(body)}}]}
    else:
        payload = {"choices": [{"message": {"content": body}}]}
    return httpx.Response(200, json=payload)


@pytest.fixture
def settings():
    """Minimal settings for run_research (only OpenRouter fields used)."""
    class S:
        openrouter_base_url = "https://openrouter.ai/api/v1"
        openrouter_api_key = "test-key"
    return S()


@pytest.mark.asyncio
@respx.mock
async def test_run_research_returns_valid_response(settings):
    """Mock 6 LLM responses; run_research returns ResearchResponse with all sections."""
    structured_json = {
        "industry": "Tech",
        "founded": "2020",
        "website": "https://example.com",
        "headquarters": "NYC",
        "annualRevenue": "$1M",
        "employees": "50",
    }
    overview_text = """1. Company Overview (100-150 words): Acme is a global company.
https://acme.com/about

2. Company Background (150-350 words): Founded in 2020.
https://acme.com/history

3. Financial Overview (100-200 words): Strong revenue.
https://acme.com/investors

4. Audience Segmentation (50-75 words): B2B and B2C.
https://acme.com/audience
"""
    marketing_text = "Marketing narrative here."
    sponsorships_text = "Sponsorships narrative."
    social_text = "YouTube: @acme\nInstagram: @acme\n\nThen write a flowing narrative about platforms."
    strategic_text = "Strategic focus with [citation](https://example.com)."

    respx.post(OPENROUTER_URL).mock(
        side_effect=[
            _mk_response(structured_json),
            _mk_response(overview_text),
            _mk_response(marketing_text),
            _mk_response(sponsorships_text),
            _mk_response(social_text),
            _mk_response(strategic_text),
        ]
    )

    request = ResearchRequest(company_name="Acme", region_focus="Global")
    result = await run_research(request, settings)

    assert result.structured_data.industry == "Tech"
    assert result.structured_data.employees == "50"
    assert "companyOverview" in result.detailed_analysis
    assert "marketingActivity" in result.detailed_analysis
    assert "sponsorshipsExperiential" in result.detailed_analysis
    assert "socialMediaPresence" in result.detailed_analysis
    assert "strategicFocus" in result.detailed_analysis
    assert result.metadata["prompt_versions"]
    assert result.detailed_analysis["marketingActivity"]["content"] == marketing_text
    assert result.detailed_analysis["strategicFocus"]["content"] == strategic_text
