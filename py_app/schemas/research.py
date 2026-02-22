"""
Pydantic models for research API. Field names match CompanyData in lib/pdf-export.ts (frozen contract).
"""

from typing import List

from pydantic import BaseModel, Field


# ---- Section building blocks ----
class SectionWithSources(BaseModel):
    """Section with content and at least one source (overview, background, financial, audience)."""
    content: str
    sources: List[str] = Field(..., min_length=1)


class SectionContent(BaseModel):
    """Section with content only (marketing, sponsorships, strategic focus)."""
    content: str


class SocialMediaSection(BaseModel):
    """handles is newline-separated; content is narrative."""
    handles: str
    content: str


# ---- Detailed analysis schemas ----
# Field names are the shared contract: both the UI (brand-profile-panel) and the PDF
# (pdf-export.ts CompanyData.detailedAnalysis) read these keys. Renaming would break
# both; the PDF only renders a subset of the full company object (no contacts, etc.).
class OverviewSchema(BaseModel):
    companyOverview: SectionWithSources
    companyBackground: SectionWithSources
    financialOverview: SectionWithSources
    audienceSegmentation: SectionWithSources


class MarketingSchema(BaseModel):
    marketingActivity: SectionContent


class SponsorshipsSchema(BaseModel):
    sponsorshipsExperiential: SectionContent


class SocialMediaSchema(BaseModel):
    socialMediaPresence: SocialMediaSection
    strategicFocus: SectionContent


# ---- Structured data (LLM returns these fields; frontend may map to CompanyData) ----
class StructuredDataSchema(BaseModel):
    industry: str
    founded: str
    website: str
    headquarters: str
    annualRevenue: str
    employees: str


# ---- Request / Response ----
class ResearchRequest(BaseModel):
    company_name: str
    region_focus: str
    specific_region: str = ""
    division_focus: str = ""
    specific_division: str = ""


class ResearchResponse(BaseModel):
    structured_data: StructuredDataSchema
    detailed_analysis: dict  # Merged output from OverviewSchema, MarketingSchema, etc.; keys match CompanyData
    metadata: dict
