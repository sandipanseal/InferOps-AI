import re
from dataclasses import dataclass


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+\d{1,3}[\s-]?)?(\(?\d{2,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{3,6}")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
CREDIT_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
API_KEY_RE = re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")


@dataclass
class PIIResult:
    contains_pii: bool
    redacted_text: str
    detected_types: list[str]


def detect_and_redact_pii(text: str) -> PIIResult:
    detected = []
    redacted = text

    patterns = [
        ("email", EMAIL_RE, "[EMAIL_REDACTED]"),
        ("phone", PHONE_RE, "[PHONE_REDACTED]"),
        ("iban", IBAN_RE, "[IBAN_REDACTED]"),
        ("credit_card", CREDIT_RE, "[CARD_REDACTED]"),
        ("api_key", API_KEY_RE, "[SECRET_REDACTED]"),
    ]

    for name, pattern, replacement in patterns:
        if pattern.search(redacted):
            detected.append(name)
            redacted = pattern.sub(replacement, redacted)

    return PIIResult(bool(detected), redacted, detected)
