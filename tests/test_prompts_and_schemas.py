"""
Tests for Pydantic schemas (Task 2a). Prompt tests added in Task 2b.
"""
import pytest
from pydantic import ValidationError

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
