"""
Marketing activity narrative. Output maps to MarketingSchema (SectionContent).
Structure: SYSTEM_PROMPT = role + output rules (+ hard constraints); build_user_message = task + dynamic inputs.
"""
PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = """You are a research assistant. Write flowing narrative text. Use bold formatting only for campaign names (e.g. **Christmas Campaign 2024:**). Never output ALL CAPS. You must include inline source links in markdown format [Link Text](URL) for all verifiable information. Do not make up campaign details; use only information you find. Do not start with generic time phrases like "over the past five years"; use language that reflects the actual timeframe of the content you found."""


def build_user_message(
    company_name: str,
    region_text: str = "",
    focus_text: str = "",
) -> str:
    return f"""Research {company_name}{region_text}{focus_text} recent and current marketing activities.

Provide a detailed narrative analysis of current and recent global marketing activity. Include at least 5 specific named campaigns. For each campaign describe (where possible): campaign name, date or period, target audiences, messaging themes, measurable outcomes, creative concepts, channels used, and partnerships or collaborations.

If you cannot find 5 specific campaigns within the last 3-5 years, extend your search to find the required 5 campaigns. If a region or division was specified, include regional or division-specific marketing details with concrete examples (events, digital campaigns, key channel activations) including timing, format, target audience, and strategic rationale. Avoid vague descriptions; all examples must reference verifiable sources, initiatives, or announcements."""
