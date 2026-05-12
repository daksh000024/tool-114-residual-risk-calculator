"""
services/sanitiser.py
Input sanitisation — strips HTML, detects prompt-injection patterns.
Used by all endpoints before passing input to Groq.
"""

import re
import bleach
import logging

logger = logging.getLogger("ai-service.sanitiser")

# ── Patterns that indicate prompt-injection attempts ──────────────────────────
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?instructions",
    r"you\s+are\s+now\s+(a\s+)?",
    r"act\s+as\s+(if\s+you\s+are\s+)?",
    r"pretend\s+(you\s+are|to\s+be)",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"dan\s+mode",
    r"system\s*:\s*",
    r"<\|.*?\|>",           # token-injection syntax
    r"\[INST\]",            # llama instruction injection
    r"###\s*(system|instruction|prompt)",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitise(text: str) -> tuple[str, bool]:
    """
    Sanitise a single string.
    Returns (clean_text, is_injection_detected).
    Raises ValueError if the input is empty after cleaning.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    # Strip HTML tags
    clean = bleach.clean(text, tags=[], strip=True).strip()

    if not clean:
        raise ValueError("Input is empty after sanitisation")

    # Detect prompt injection
    for pattern in _COMPILED:
        if pattern.search(clean):
            logger.warning(f"Prompt injection detected: pattern={pattern.pattern!r}")
            return clean, True

    return clean, False


def sanitise_dict(data: dict, fields: list[str]) -> tuple[dict, bool]:
    """
    Sanitise multiple fields of a dict.
    Returns (sanitised_dict, any_injection_detected).
    """
    sanitised = dict(data)
    any_injection = False

    for field in fields:
        if field in sanitised and sanitised[field]:
            clean, injected = sanitise(str(sanitised[field]))
            sanitised[field] = clean
            if injected:
                any_injection = True

    return sanitised, any_injection
