"""
Input validation for research API. Port of lib/input-validator.ts (597 lines).
Provides validation for company name, region, division, and full prompt.
"""

import re
from typing import List, Literal

from pydantic import BaseModel, Field

ValidationContext = Literal["company", "region", "division", "numeric"]


class ValidationResult(BaseModel):
    """Result of validating user input."""

    is_valid: bool
    sanitized: str
    issues: List[str] = Field(default_factory=list)
    blocked: bool = False  # True if input was completely rejected


# =============================================================================
# PRIORITY #1: SQL INJECTION PROTECTION
# =============================================================================

SQL_PATTERNS = [
    re.compile(r"\b(drop|delete|insert|update|select|union|alter|create|truncate|exec|execute)\b", re.I),
    re.compile(r"--\s*$", re.M),
    re.compile(r"/\*[\s\S]*?\*/"),
    re.compile(r"['\"]\s*;\s*"),
    re.compile(r";\s*(drop|delete|insert|update|select|union)", re.I),
    re.compile(r"'?\s*or\s+'?\d+='?\d+", re.I),
    re.compile(r"'?\s*and\s+'?\d+='?\d+", re.I),
    re.compile(r"union\s+select", re.I),
    re.compile(r"\b(load_file|into\s+outfile|into\s+dumpfile)\b", re.I),
    re.compile(r"\b(mysql|postgresql|sqlite|mssql|oracle)\b", re.I),
]


def detect_sql_injection(input_str: str) -> bool:
    """Detects SQL injection attempts in user input."""
    return any(p.search(input_str) for p in SQL_PATTERNS)


# =============================================================================
# XSS PROTECTION
# =============================================================================

XSS_PATTERNS = [
    re.compile(r"<script[\s\S]*?>[\s\S]*?</script>", re.I),
    re.compile(r"<script", re.I),
    re.compile(r"on\w+\s*=", re.I),
    re.compile(r"javascript\s*:", re.I),
    re.compile(r"data\s*:\s*text/html", re.I),
    re.compile(r"<iframe[\s\S]*?>[\s\S]*?</iframe>", re.I),
    re.compile(r"<object[\s\S]*?>[\s\S]*?</object>", re.I),
    re.compile(r"<embed[\s\S]*?>", re.I),
    re.compile(r"<form[\s\S]*?>[\s\S]*?</form>", re.I),
    re.compile(r'onclick\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onload\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onerror\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onfocus\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onblur\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onchange\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onsubmit\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onreset\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onselect\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onkeydown\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onkeyup\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onkeypress\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onmousedown\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onmouseup\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onmouseover\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onmouseout\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onmousemove\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onmouseenter\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onmouseleave\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'ondblclick\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'oncontextmenu\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onwheel\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'oninput\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'oninvalid\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'onsearch\s*=\s*["\'][^"\']*["\']', re.I),
    re.compile(r'style\s*=\s*["\'][^"\']*javascript[^"\']*["\']', re.I),
    re.compile(r'style\s*=\s*["\'][^"\']*expression\s*\([^"\']*["\']', re.I),
    re.compile(r'style\s*=\s*["\'][^"\']*url\s*\([^"\']*javascript[^"\']*["\']', re.I),
    re.compile(r"<svg[\s\S]*?onload[\s\S]*?>", re.I),
    re.compile(r"<svg[\s\S]*?onerror[\s\S]*?>", re.I),
    re.compile(r"<svg[\s\S]*?onclick[\s\S]*?>", re.I),
    re.compile(r"<img[\s\S]*?onerror[\s\S]*?>", re.I),
    re.compile(r"<img[\s\S]*?onload[\s\S]*?>", re.I),
    re.compile(r"<link[\s\S]*?onload[\s\S]*?>", re.I),
    re.compile(r"<link[\s\S]*?onerror[\s\S]*?>", re.I),
    re.compile(r"<meta[\s\S]*?onload[\s\S]*?>", re.I),
    re.compile(r"<meta[\s\S]*?onerror[\s\S]*?>", re.I),
    re.compile(r"<input[\s\S]*?onfocus[\s\S]*?>", re.I),
    re.compile(r"<input[\s\S]*?onblur[\s\S]*?>", re.I),
    re.compile(r"<input[\s\S]*?onchange[\s\S]*?>", re.I),
    re.compile(r"<body[\s\S]*?onload[\s\S]*?>", re.I),
    re.compile(r"<body[\s\S]*?onunload[\s\S]*?>", re.I),
    re.compile(r'<a[\s\S]*?href\s*=\s*["\']?javascript:', re.I),
    re.compile(r"<a[\s\S]*?onclick[\s\S]*?>", re.I),
    re.compile(r"vbscript\s*:", re.I),
    re.compile(r"data\s*:\s*text/plain", re.I),
    re.compile(r"data\s*:\s*application/javascript", re.I),
    re.compile(r"expression\s*\(", re.I),
    re.compile(r"eval\s*\(", re.I),
    re.compile(r"setTimeout\s*\(", re.I),
    re.compile(r"setInterval\s*\(", re.I),
]


def detect_xss(input_str: str) -> bool:
    """Detects XSS (Cross-Site Scripting) attempts in user input."""
    return any(p.search(input_str) for p in XSS_PATTERNS)


# =============================================================================
# TEMPLATE INJECTION PROTECTION
# =============================================================================

TEMPLATE_PATTERNS = [
    re.compile(r"\$\{[^}]*\}"),
    re.compile(r"<%[\s\S]*?%>"),
    re.compile(r"\{\{[\s\S]*?\}\}"),
    re.compile(r"\{%[\s\S]*?%\}"),
    re.compile(r"<\?php[\s\S]*?\?>", re.I),
    re.compile(r"<%=[\s\S]*?%>"),
    re.compile(r"#\{[\s\S]*?\}"),
]


def detect_template_injection(input_str: str) -> bool:
    """Detects template injection attempts that could execute server-side code."""
    return any(p.search(input_str) for p in TEMPLATE_PATTERNS)


# =============================================================================
# PROMPT INJECTION PROTECTION
# =============================================================================

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous\s+)?instructions", re.I),
    re.compile(r"forget\s+(previous\s+)?instructions", re.I),
    re.compile(r"disregard\s+(previous\s+)?instructions", re.I),
    re.compile(r"(show|tell|display|reveal|print)\s+(me\s+)?(your\s+)?(system\s+)?prompt", re.I),
    re.compile(r"what\s+are\s+(your\s+)?(initial\s+)?instructions", re.I),
    re.compile(r"you\s+are\s+now\s+(a\s+)?(different|new)\s+", re.I),
    re.compile(r"act\s+as\s+(if\s+)?you\s+are", re.I),
    re.compile(r"pretend\s+(to\s+be|that\s+you\s+are)", re.I),
    re.compile(r"(jailbreak|developer\s+mode|debug\s+mode)", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"additional\s+instructions?\s*:", re.I),
    re.compile(r"(leak|extract|reveal)\s+(the\s+)?(prompt|instructions?)", re.I),
]


def detect_prompt_injection(input_str: str) -> bool:
    """Detects prompt injection attempts that could manipulate LLM behavior."""
    return any(p.search(input_str) for p in PROMPT_INJECTION_PATTERNS)


# =============================================================================
# JSON INJECTION PROTECTION
# =============================================================================

JSON_PATTERNS = [
    re.compile(r"^\s*\{[\s\S]*\}\s*$"),
    re.compile(r"^\s*\[[\s\S]*\]\s*$"),
    re.compile(r'\{[^}]*"[^"]*"\s*:\s*"[^"]*"'),
    re.compile(r'\{[^}]*"[^"]*"\s*:\s*\d+'),
    re.compile(r'\{[^}]*"[^"]*"\s*:\s*(true|false|null)'),
    re.compile(r'"test"\s*:\s*"value"', re.I),
    re.compile(r'"TEST"\s*:\s*"VALUE"', re.I),
]


def detect_json_injection(input_str: str) -> bool:
    """Detects JSON-like input that could cause parsing issues."""
    return any(p.search(input_str) for p in JSON_PATTERNS)


# =============================================================================
# PATTERN DETECTION
# =============================================================================

REPEATED_CHARS = re.compile(r"(.)\1{2,}")


def detect_repeated_characters(input_str: str) -> bool:
    """Detects 3+ same characters in a row (e.g. 'aaaaaaaaaa') that could cause LLM hallucinations."""
    return bool(REPEATED_CHARS.search(input_str))


def _contains_vowels(input_str: str) -> bool:
    """Helper: check if input contains vowels (basic gibberish detection)."""
    return bool(re.search(r"[aeiou]", input_str, re.I))


def detect_gibberish(input_str: str) -> bool:
    """Detects gibberish patterns that could cause LLM hallucinations."""
    trimmed = input_str.strip()
    if len(trimmed) < 2:
        return True
    if re.match(r"^\d+$", trimmed):
        return True
    if REPEATED_CHARS.search(trimmed):
        return True
    if re.match(r"^[a-z]{3,}$", trimmed, re.I) and not _contains_vowels(trimmed):
        return True
    return False


def detect_invalid_length(input_str: str) -> bool:
    """Detects if input is only whitespace or very short (< 2 chars after trim)."""
    trimmed = input_str.strip()
    return len(trimmed) == 0 or len(trimmed) < 2


# =============================================================================
# SANITIZATION HELPERS
# =============================================================================

def normalize_whitespace(input_str: str) -> str:
    """Normalizes whitespace by trimming and collapsing multiple spaces."""
    return " ".join(input_str.strip().split())


def sanitize_input(input_str: str, context: ValidationContext) -> str:
    """Sanitizes input based on context, removing dangerous characters."""
    sanitized = input_str
    sanitized = re.sub(r"[<>'\"`;]", "", sanitized)
    if context == "company":
        sanitized = re.sub(r"[^a-zA-Z0-9\s.,&'\-()]", "", sanitized)
    elif context == "region":
        sanitized = re.sub(r"[^a-zA-Z0-9\s\-]", "", sanitized)
    elif context == "division":
        sanitized = re.sub(r"[^a-zA-Z0-9\s/&]", "", sanitized)
    elif context == "numeric":
        sanitized = ""
    return normalize_whitespace(sanitized)


# =============================================================================
# CONTEXT-AWARE VALIDATION
# =============================================================================

def validate_company_name(input_str: str) -> ValidationResult:
    """Validates company names with appropriate rules."""
    issues: List[str] = []
    sanitized = input_str.strip()

    if not sanitized:
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Company name cannot be empty"], blocked=False
        )
    if detect_invalid_length(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Company name too short"], blocked=True
        )
    if detect_gibberish(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Please enter a valid company name"], blocked=True
        )
    if detect_repeated_characters(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Please enter a valid company name"], blocked=True
        )
    if detect_sql_injection(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Invalid input detected"], blocked=True
        )
    if detect_xss(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Invalid input detected"], blocked=True
        )
    if detect_template_injection(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Invalid input detected"], blocked=True
        )
    if detect_prompt_injection(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Invalid input detected"], blocked=True
        )
    if detect_json_injection(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Invalid input detected"], blocked=True
        )

    if len(sanitized) > 200:
        issues.append("Company name too long")
        sanitized = sanitized[:200]

    blocked = sanitized == "" and input_str.strip() != ""
    is_valid = not blocked and len(sanitized) > 0
    return ValidationResult(is_valid=is_valid, sanitized=sanitized, issues=issues, blocked=blocked)


def validate_region_name(input_str: str) -> ValidationResult:
    """Validates region names with appropriate rules."""
    issues: List[str] = []
    sanitized = input_str.strip()

    if not sanitized:
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Region name cannot be empty"], blocked=False
        )
    if detect_invalid_length(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Region name too short"], blocked=True
        )
    if detect_gibberish(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Please enter a valid region name"], blocked=True
        )
    if detect_repeated_characters(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Please enter a valid region name"], blocked=True
        )

    if (
        detect_sql_injection(sanitized)
        or detect_xss(sanitized)
        or detect_template_injection(sanitized)
        or detect_prompt_injection(sanitized)
    ):
        issues.append("Invalid characters detected")
        sanitized = sanitize_input(sanitized, "region")

    if len(sanitized) > 100:
        issues.append("Region name too long")
        sanitized = sanitized[:100]

    blocked = sanitized == "" and input_str.strip() != ""
    is_valid = not blocked and len(sanitized) > 0
    return ValidationResult(is_valid=is_valid, sanitized=sanitized, issues=issues, blocked=blocked)


def validate_division_name(input_str: str) -> ValidationResult:
    """Validates division names with appropriate rules."""
    issues: List[str] = []
    sanitized = input_str.strip()

    if not sanitized:
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Division name cannot be empty"], blocked=False
        )
    if detect_invalid_length(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Division name too short"], blocked=True
        )
    if detect_gibberish(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Please enter a valid division name"], blocked=True
        )
    if detect_repeated_characters(sanitized):
        return ValidationResult(
            is_valid=False, sanitized="", issues=["Please enter a valid division name"], blocked=True
        )

    if (
        detect_sql_injection(sanitized)
        or detect_xss(sanitized)
        or detect_template_injection(sanitized)
        or detect_prompt_injection(sanitized)
    ):
        issues.append("Invalid characters detected")
        sanitized = sanitize_input(sanitized, "division")

    if len(sanitized) > 100:
        issues.append("Division name too long")
        sanitized = sanitized[:100]

    blocked = sanitized == "" and input_str.strip() != ""
    is_valid = not blocked and len(sanitized) > 0
    return ValidationResult(is_valid=is_valid, sanitized=sanitized, issues=issues, blocked=blocked)


def validate_numeric_choice(input_str: str, valid_choices: List[str]) -> ValidationResult:
    """Validates numeric choices (e.g. menu options)."""
    sanitized = input_str.strip()
    if sanitized not in valid_choices:
        return ValidationResult(
            is_valid=False,
            sanitized="",
            issues=[f"Please choose one of: {', '.join(valid_choices)}"],
            blocked=False,
        )
    return ValidationResult(is_valid=True, sanitized=sanitized, issues=[], blocked=False)


# =============================================================================
# COMPREHENSIVE VALIDATION
# =============================================================================

def validate_prompt(prompt: str) -> ValidationResult:
    """Comprehensive validation for complete prompts (all injection types)."""
    issues: List[str] = []
    sanitized = prompt

    if detect_sql_injection(prompt):
        issues.append("SQL injection attempt detected")
    if detect_xss(prompt):
        issues.append("XSS attempt detected")
    if detect_template_injection(prompt):
        issues.append("Template injection attempt detected")
    if detect_prompt_injection(prompt):
        issues.append("Prompt injection attempt detected")
    if len(prompt) > 5000:
        issues.append("Prompt too long")
        sanitized = prompt[:5000]

    blocked = len(issues) > 0
    is_valid = not blocked
    return ValidationResult(is_valid=is_valid, sanitized=sanitized, issues=issues, blocked=blocked)


# =============================================================================
# QUICK CHECK FOR ROUTER
# =============================================================================

def is_input_safe(input_str: str) -> bool:
    """Quick validation for backend use — returns True only if input passes all checks."""
    return not (
        detect_sql_injection(input_str)
        or detect_xss(input_str)
        or detect_template_injection(input_str)
        or detect_prompt_injection(input_str)
        or detect_repeated_characters(input_str)
        or detect_gibberish(input_str)
        or detect_invalid_length(input_str)
        or detect_json_injection(input_str)
    )


def validate_research_request(company_name: str, region_focus: str, specific_region: str, division_focus: str, specific_division: str) -> str | None:
    """
    Validates all string fields of a research request. Returns None if valid,
    or an error message string to return as 400 detail if invalid.
    """
    if not is_input_safe(company_name):
        return "Invalid company name"
    if not is_input_safe(region_focus):
        return "Invalid region focus"
    if specific_region and not is_input_safe(specific_region):
        return "Invalid specific region"
    if division_focus and not is_input_safe(division_focus):
        return "Invalid division focus"
    if specific_division and not is_input_safe(specific_division):
        return "Invalid specific division"
    return None
