"""
Social media presence and handles. Output maps to SocialMediaSection (handles + content).
Structure: SYSTEM_PROMPT = role + output rules (+ hard constraints); build_user_message = task + dynamic inputs.
"""
PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = """You are a research assistant. Identify official or verified social media handles where available. Write continuous prose for the narrative; no bullet points or subheadings in the analysis. Do not include links to third-party blogs or specific post URLs; only official social media handles. Focus on high-level, aggregate insights from the last 6-12 months. Do not make up platform details; use only information you find."""


def build_user_message(
    company_name: str,
    region_text: str = "",
    focus_text: str = "",
) -> str:
    return f"""Research {company_name}{region_text} social media presence.

Social Media (250-350 words):

First, list the official or verified handles for each platform where you can find them (e.g. YouTube: [handle or link], Instagram: [handle or link], TikTok, Facebook, LinkedIn, X/Twitter). Omit platforms where no official handle was found.

Then write a flowing narrative analysis focusing on the 2-3 most active platforms (by follower count). Describe content style and tone, posting frequency, audience engagement, visual identity and brand voice, and strategic role in their overall social presence."""
