"""
Research orchestration: 6 parallel LLM calls, then Pydantic validation (replaces 4 formatting calls).
Ported from co-pilot-interface.tsx first Promise.all; no formatting phase.
"""

import asyncio
import json
import logging
import re
from typing import Any

import httpx

from pydantic import ValidationError as PydanticValidationError

from py_app.config import Settings
from py_app.schemas.research import (
    OverviewSchema,
    MarketingSchema,
    ResearchRequest,
    ResearchResponse,
    SectionContent,
    SocialMediaSchema,
    SocialMediaSection,
    SponsorshipsSchema,
    StructuredDataSchema,
)
from py_app.prompts import (
    structured_data,
    overview,
    marketing,
    sponsorships,
    social_media,
    strategic_focus,
    collect_prompt_versions,
)
from py_app.services.llm_client import (
    get_structured_data,
    get_detailed_analysis,
    get_detailed_analysis_with_citations,
)

logger = logging.getLogger(__name__)

# Fallback source when parsing yields no URLs (OverviewSchema requires min_length=1)
_PLACEHOLDER_SOURCE = "https://example.com/source"


def _region_text(request: ResearchRequest) -> str:
    """Build region suffix for prompts (e.g. ' in North America')."""
    if request.region_focus == "specific" and request.specific_region:
        return f" in {request.specific_region}"
    return ""


def _focus_text(request: ResearchRequest) -> str:
    """Build division focus suffix for prompts (e.g. ', specifically their X division')."""
    if request.division_focus == "specific" and request.specific_division:
        return f", specifically their {request.specific_division} division"
    return ""


def _strip_json_fences(raw: str) -> str:
    """Remove markdown code fences so we can parse JSON from LLM output."""
    s = raw.strip()
    if "```json" in s:
        s = re.sub(r"^```json\s*", "", s)
    if "```" in s:
        s = re.sub(r"```\s*$", "", s)
    return s.strip()


def _extract_sources_block(block: str) -> tuple[str, list[str]]:
    """
    Split a section block into content (before "Sources:") and list of URLs (after "Sources:", one per line).
    Falls back to url_pattern findall if no "Sources:" line is found. Returns (content, urls).
    """
    url_pattern = re.compile(r"https?://[^\s\]\)]+")
    block = block.strip()
    # Look for "Sources:" (case-insensitive) on its own or at start of line
    sources_match = re.search(r"\n\s*Sources:\s*\n", block, re.IGNORECASE)
    if sources_match:
        content_part = block[: sources_match.start()].strip()
        urls_part = block[sources_match.end() :].strip()
        # Take lines that look like URLs (http/https) or extract URLs from lines
        urls = []
        for line in urls_part.splitlines():
            line = line.strip()
            if not line:
                continue
            # If whole line is a URL, use it
            if re.match(r"^https?://", line):
                urls.append(line)
            else:
                # Maybe URL is embedded (e.g. after a dash); extract
                found = url_pattern.findall(line)
                urls.extend(found)
        content = re.sub(r"\n{2,}", "\n\n", content_part).strip()
        if urls:
            return content or "(no content)", urls
        # No URLs after Sources: — fall through to regex on whole block
    # Fallback: extract all URLs from block; content is block with URLs removed
    urls = url_pattern.findall(block)
    if urls:
        content = url_pattern.sub("", block).strip()
        content = re.sub(r"\n{2,}", "\n\n", content).strip()
        return content or "(no content)", urls
    return block[:500].strip() or "(no content)", []


def _parse_overview_text(text: str) -> dict[str, Any]:
    """
    Parse overview LLM output (four sections with Sources: block) into dict for OverviewSchema.
    Sections are expected to start with "1. Company Overview", "2. Company Background", etc.
    Each section may end with "Sources:" followed by one URL per line; _extract_sources_block handles parsing.
    """
    section_headers = [
        ("1. Company Overview", "companyOverview"),
        ("2. Company Background", "companyBackground"),
        ("3. Financial Overview", "financialOverview"),
        ("4. Audience Segmentation", "audienceSegmentation"),
    ]
    result: dict[str, Any] = {}

    for i, (header, key) in enumerate(section_headers):
        start = text.find(header)
        if start == -1:
            result[key] = {"content": text[:500].strip() or "(no content)", "sources": [_PLACEHOLDER_SOURCE]}
            continue
        end = text.find(section_headers[i + 1][0], start + len(header)) if i + 1 < len(section_headers) else len(text)
        block = text[start + len(header) : end].strip()
        content, urls = _extract_sources_block(block)
        if not urls:
            urls = [_PLACEHOLDER_SOURCE]
        result[key] = {"content": content, "sources": urls}

    return result


def _parse_social_handles_and_content(text: str) -> tuple[str, str]:
    """
    Split social media LLM output into handles (first block) and narrative content (rest).
    Handles are typically short lines; content starts after a blank line or 'Then write'.
    """
    text = text.strip()
    if not text:
        return "", ""
    lower = text.lower()
    idx = lower.find("then write")
    if idx != -1:
        handles = text[:idx].strip()
        content = text[idx:].strip()
        return handles, content
    parts = re.split(r"\n\s*\n", text, maxsplit=1)
    if len(parts) == 2 and len(parts[0]) < 600:
        return parts[0].strip(), parts[1].strip()
    return "", text


async def run_research(request: ResearchRequest, settings: Settings) -> ResearchResponse:
    """
    Run the 6 research LLM calls in parallel, then build detailed_analysis via Pydantic
    (replacing the 4 formatting-agent calls). One failure fails the whole run (no partial results).
    """
    region = _region_text(request)
    focus = _focus_text(request)

    structured_prompt = structured_data.build_user_message(
        request.company_name, region_text=region, focus_text=focus
    )
    overview_prompt = overview.build_user_message(
        request.company_name, region_text=region, focus_text=focus
    )
    marketing_prompt = marketing.build_user_message(
        request.company_name, region_text=region, focus_text=focus
    )
    sponsorships_prompt = sponsorships.build_user_message(
        request.company_name, region_text=region, focus_text=focus
    )
    social_prompt = social_media.build_user_message(
        request.company_name, region_text=region, focus_text=focus
    )
    strategic_prompt = strategic_focus.build_user_message(
        request.company_name, region_text=region, focus_text=focus
    )

    base_url = settings.openrouter_base_url
    api_key = settings.openrouter_api_key

    async with httpx.AsyncClient(timeout=120.0) as client:
        results = await asyncio.gather(
            get_structured_data(structured_prompt, client, base_url, api_key),
            get_detailed_analysis(overview_prompt, client, base_url, api_key),
            get_detailed_analysis_with_citations(marketing_prompt, client, base_url, api_key),
            get_detailed_analysis_with_citations(sponsorships_prompt, client, base_url, api_key),
            get_detailed_analysis_with_citations(social_prompt, client, base_url, api_key),
            get_detailed_analysis_with_citations(strategic_prompt, client, base_url, api_key),
        )

    (
        structured_output,
        overview_output,
        marketing_output,
        sponsorships_output,
        social_output,
        strategic_output,
    ) = results

    logger.info("run_research: all 6 LLM calls done, building response")

    try:
        # Structured data: JSON string -> dict -> Pydantic
        try:
            raw = _strip_json_fences(structured_output)
            structured_dict = json.loads(raw)
            structured_data_validated = StructuredDataSchema.model_validate(structured_dict)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Structured data parse failed: %s", e)
            raise ValueError("Failed to parse structured data response") from e

        # Overview: text -> parsed dict -> Pydantic
        overview_dict = _parse_overview_text(overview_output)
        overview_validated = OverviewSchema.model_validate(overview_dict)

        # Marketing, sponsorships: raw text -> SectionContent
        marketing_validated = MarketingSchema(
            marketingActivity=SectionContent(content=marketing_output or "(no content)")
        )
        sponsorships_validated = SponsorshipsSchema(
            sponsorshipsExperiential=SectionContent(content=sponsorships_output or "(no content)")
        )

        # Social + strategic: split handles/content, then SocialMediaSchema
        handles, social_content = _parse_social_handles_and_content(social_output)
        social_validated = SocialMediaSchema(
            socialMediaPresence=SocialMediaSection(
                handles=handles or "(no handles)",
                content=social_content or "(no content)",
            ),
            strategicFocus=SectionContent(content=strategic_output or "(no content)"),
        )

        detailed_analysis = {
            **overview_validated.model_dump(),
            **marketing_validated.model_dump(),
            **sponsorships_validated.model_dump(),
            **social_validated.model_dump(),
        }

        logger.info("run_research: returning ResearchResponse")
        return ResearchResponse(
            structured_data=structured_data_validated,
            detailed_analysis=detailed_analysis,
            metadata={"prompt_versions": collect_prompt_versions()},
        )
    except PydanticValidationError as e:
        logger.exception("run_research: Pydantic validation failed: %s", e.errors())
        raise
