"""
Company overview (four sections with sources). Output parsed into OverviewSchema.
Structure: SYSTEM_PROMPT = role + output rules (+ hard constraints); build_user_message = task + dynamic inputs.
"""
PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = """You are a research assistant. Focus on factual information from company press releases, financial reports, and reputable business sources. For each section, use only the sources you cite; prefer primary sources and high-authority media."""


def build_user_message(
    company_name: str,
    region_text: str = "",
    focus_text: str = "",
) -> str:
    return f"""Research {company_name}{region_text} and provide four sections.

1. Company Overview (100-150 words): Global footprint, core business divisions and brands, primary service lines, main offices.
2. Company Background (150-350 words): Brief history, key milestones, organisational structure, defining values.
3. Financial Overview (100-200 words): Key financial performance with specific datapoints, stability indicators, ownership structure, funding and recent acquisitions.
4. Audience Segmentation (50-75 words): Target audiences, current customer types, emerging segments.

For each section, after the section content list 2–8 source URLs that were actually used to write that section. One URL per line. Do not reuse URLs across sections unless the same source was genuinely used for both. Include only direct, verifiable URLs."""
