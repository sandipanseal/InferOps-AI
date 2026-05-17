import re
from dataclasses import dataclass


SUSPICIOUS_PATTERNS = [
    r"ignore (all )?(previous|prior) instructions",
    r"reveal (the )?(system|developer) prompt",
    r"print hidden rules",
    r"bypass (the )?(policy|security|safety)",
    r"you are now",
    r"forget your instructions",
    r"exfiltrate",
    r"send secrets",
]


@dataclass
class InjectionResult:
    risk_level: str
    blocked: bool
    reasons: list[str]


def check_prompt_injection(text: str) -> InjectionResult:
    reasons = []
    lower = text.lower()

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, lower):
            reasons.append(f"Matched suspicious pattern: {pattern}")

    if len(reasons) >= 2:
        return InjectionResult("high", True, reasons)
    if len(reasons) == 1:
        return InjectionResult("high", True, reasons)
    return InjectionResult("low", False, [])
