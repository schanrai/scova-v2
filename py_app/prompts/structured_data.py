"""
Structured company data prompt. Output shape enforced by Pydantic StructuredDataSchema.
Structure: SYSTEM_PROMPT = role + output rules (+ hard constraints); build_user_message = task + dynamic inputs.
"""
PROMPT_VERSION = "v1.0.0"

# Role + output rules; this task has few constraints so SYSTEM_PROMPT is short.
SYSTEM_PROMPT = """You are a research assistant. You must respond with only valid JSON. Do not include any other text, explanations, or formatting. Never add explanations, dates in parentheses, or extra context to field values."""


def build_user_message(
    company_name: str,
    region_text: str = "",
    focus_text: str = "",
) -> str:
    return f"""I would like to research the company {company_name}{region_text}{focus_text}.

Retrieve the following from high-quality, verifiable sources (company website, press releases, reputable media, high-authority publishers):
- industry
- founded
- website
- headquarters
- annualRevenue (use the appropriate currency symbol for the company's primary market)
- employees

Return a single JSON object with exactly these keys: "industry", "founded", "website", "headquarters", "annualRevenue", "employees". Use plain values only; no extra commentary or formatting."""
