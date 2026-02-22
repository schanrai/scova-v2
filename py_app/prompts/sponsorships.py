"""
Sponsorships and experiential initiatives. Output maps to SponsorshipsSchema (SectionContent).
Structure: SYSTEM_PROMPT = role + output rules (+ hard constraints); build_user_message = task + dynamic inputs.
"""
PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = """You are a research assistant. Write flowing narrative text. Use bold formatting only for sponsorship and experiential initiative names (e.g. **Cisco Live:**). Do not use headings, lists, or title case; keep normal paragraph text in sentence case. Never output ALL CAPS. You must include inline source links in markdown format [Link Text](URL) for all verifiable information. Do not make up details; use only information you find. Do not start with generic time phrases like "over the past five years"; use language that reflects the actual timeframe found. Avoid vague statements like "supports local events"; reference named events, partners, or programs with verifiable details."""


def build_user_message(
    company_name: str,
    region_text: str = "",
    focus_text: str = "",
) -> str:
    return f"""Research {company_name}{region_text}{focus_text} recent and current sponsorship portfolio and experiential initiatives.

Provide a detailed narrative analysis of at least 5 specific named sponsorships in sports, arts, culture, entertainment, or lifestyle. For each sponsorship include (if available): start/end dates, geographic location, event/partner name, activation channels, budget or scale indicators, strategic fit with brand goals, measurable outcomes (audience reach, media coverage, ROI, engagement metrics).

For experiential initiatives, identify and describe at least 3 named initiatives (e.g. VIP events, curated experiences, global tours, museum tie-ins). For each initiative include (if available): dates and location, purpose/context, audience profile, unique experiential elements, cultural or thought leadership integration, measurable impact.

If you cannot find 5 sponsorships or 3 experiential initiatives within the last 3-5 years, extend your search. If a region or division was specified, include regional or division-specific sponsorship details with concrete examples including timing, format, target audience, and strategic rationale."""
