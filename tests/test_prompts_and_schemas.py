"""
Tests for Pydantic schemas (Task 2a) and prompts (Task 2b).
"""
import pytest
from pydantic import ValidationError

from py_app.prompts import (
    structured_data,
    overview,
    marketing,
    sponsorships,
    social_media,
    strategic_focus,
)
from py_app.schemas.research import (
    SectionWithSources,
    SectionContent,
    SocialMediaSection,
    OverviewSchema,
    MarketingSchema,
    SponsorshipsSchema,
    SocialMediaSchema,
    StructuredDataSchema,
    ResearchRequest,
    ResearchResponse,
)


# ---- Valid instantiation ----
def test_section_with_sources_valid():
    SectionWithSources(content="Overview text.", sources=["https://example.com", "https://b.com"])


def test_section_content_valid():
    SectionContent(content="Marketing narrative.")


def test_social_media_section_valid():
    SocialMediaSection(handles="@acme\n@acme_news", content="Social analysis.")


def test_overview_schema_valid():
    section = {"content": "Text", "sources": ["s1"]}
    OverviewSchema(
        companyOverview=section,
        companyBackground=section,
        financialOverview=section,
        audienceSegmentation=section,
    )


def test_marketing_schema_valid():
    MarketingSchema(marketingActivity=SectionContent(content="Campaigns."))


def test_sponsorships_schema_valid():
    SponsorshipsSchema(sponsorshipsExperiential=SectionContent(content="Sponsorships."))


def test_social_media_schema_valid():
    SocialMediaSchema(
        socialMediaPresence=SocialMediaSection(handles="@x", content="Presence."),
        strategicFocus=SectionContent(content="Strategy."),
    )


def test_structured_data_schema_valid():
    StructuredDataSchema(
        industry="Tech",
        founded="2020",
        website="https://example.com",
        headquarters="NYC",
        annualRevenue="$1M",
        employees="50",
    )


def test_research_request_valid():
    ResearchRequest(company_name="Acme", region_focus="Global")
    ResearchRequest(
        company_name="Acme",
        region_focus="NA",
        specific_region="USA",
        division_focus="Marketing",
        specific_division="Brand",
    )


def test_research_response_valid():
    structured = StructuredDataSchema(
        industry="Tech", founded="2020", website="https://x.com",
        headquarters="NYC", annualRevenue="$1M", employees="50",
    )
    ResearchResponse(
        structured_data=structured,
        detailed_analysis={"companyOverview": {"content": "x", "sources": ["s1"]}},
        metadata={"prompt_versions": {}},
    )


# ---- ValidationError: min_length on sources ----
def test_section_with_sources_empty_sources_raises():
    with pytest.raises(ValidationError):
        SectionWithSources(content="x", sources=[])


# ---- ValidationError: missing required ----
def test_research_request_missing_company_name_raises():
    with pytest.raises(ValidationError):
        ResearchRequest(region_focus="Global")  # type: ignore[call-arg]


# ---- Prompt modules (Task 2b) ----
def test_structured_data_build_user_message_contains_company():
    msg = structured_data.build_user_message("Apple", region_text="", focus_text="")
    assert "Apple" in msg
    assert "industry" in msg and "employees" in msg


def test_overview_build_user_message_no_sources_block_instructions():
    msg = overview.build_user_message("Acme", region_text="", focus_text="")
    assert "Acme" in msg
    assert "Sources:" not in msg


def test_overview_build_user_message_has_region():
    """Overview prompt uses company_name and region_text only (no focus_text, per original TSX)."""
    msg = overview.build_user_message("Nike", region_text=" in Europe", focus_text="")
    assert "Nike" in msg
    assert " in Europe" in msg


def test_marketing_build_user_message_contains_company():
    msg = marketing.build_user_message("Tesla")
    assert "Tesla" in msg


def test_sponsorships_build_user_message_contains_company():
    msg = sponsorships.build_user_message("Cisco")
    assert "Cisco" in msg


def test_social_media_build_user_message_contains_company():
    msg = social_media.build_user_message("Spotify")
    assert "Spotify" in msg


def test_strategic_focus_build_user_message_contains_company():
    msg = strategic_focus.build_user_message("Nike")
    assert "Nike" in msg


def test_all_prompt_versions_defined_and_non_empty():
    modules = [
        structured_data,
        overview,
        marketing,
        sponsorships,
        social_media,
        strategic_focus,
    ]
    for mod in modules:
        assert hasattr(mod, "PROMPT_VERSION"), f"{mod.__name__} missing PROMPT_VERSION"
        assert isinstance(getattr(mod, "PROMPT_VERSION"), str), f"{mod.__name__}.PROMPT_VERSION must be str"
        assert len(getattr(mod, "PROMPT_VERSION").strip()) > 0, f"{mod.__name__}.PROMPT_VERSION must be non-empty"
