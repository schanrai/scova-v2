"""
Research prompt modules. Each exports SYSTEM_PROMPT, build_user_message, PROMPT_VERSION.
No formatting_agent — eliminated; Pydantic validation replaces it.

Post-migration: Reorganize and optimize prompt content per OpenAI prompting best practices
(https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively).
"""
from py_app.prompts import (
    structured_data,
    overview,
    marketing,
    sponsorships,
    social_media,
    strategic_focus,
)

__all__ = [
    "structured_data",
    "overview",
    "marketing",
    "sponsorships",
    "social_media",
    "strategic_focus",
]


def collect_prompt_versions() -> dict[str, str]:
    """Return prompt name -> PROMPT_VERSION for telemetry."""
    return {
        "structured_data": structured_data.PROMPT_VERSION,
        "overview": overview.PROMPT_VERSION,
        "marketing": marketing.PROMPT_VERSION,
        "sponsorships": sponsorships.PROMPT_VERSION,
        "social_media": social_media.PROMPT_VERSION,
        "strategic_focus": strategic_focus.PROMPT_VERSION,
    }
