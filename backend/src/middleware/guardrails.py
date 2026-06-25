from __future__ import annotations

import re
from typing import Optional


PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+(instructions|prompts)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"system\s*:\s*you", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(your|the)\s+(instructions|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|above)", re.IGNORECASE),
    re.compile(r"new\s+instruction\s*:", re.IGNORECASE),
]

SENSITIVE_INFO_PATTERNS = [
    re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"(?:token|auth)\s*[:=]\s*\S+", re.IGNORECASE),
]

PII_PATTERNS = [
    re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    re.compile(r"\b\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
]


class Guardrails:
    def __init__(
        self,
        *,
        check_prompt_injection: bool = True,
        check_sensitive_info: bool = True,
        check_pii: bool = False,
        max_input_length: int = 10000,
    ):
        self._check_injection = check_prompt_injection
        self._check_sensitive = check_sensitive_info
        self._check_pii = check_pii
        self._max_input_length = max_input_length

    def validate_input(self, text: str) -> tuple[bool, Optional[str]]:
        if not text or not text.strip():
            return False, "Input is empty"

        if len(text) > self._max_input_length:
            return False, f"Input exceeds maximum length of {self._max_input_length}"

        if self._check_injection:
            for pattern in PROMPT_INJECTION_PATTERNS:
                if pattern.search(text):
                    return False, "Potential prompt injection detected"

        if self._check_sensitive:
            for pattern in SENSITIVE_INFO_PATTERNS:
                matches = pattern.findall(text)
                if matches:
                    return False, "Input contains sensitive information"

        if self._check_pii:
            for pattern in PII_PATTERNS:
                if pattern.search(text):
                    return False, "Input contains PII information"

        return True, None

    def validate_output(self, text: str) -> tuple[bool, Optional[str]]:
        if not text or not text.strip():
            return True, None

        for pattern in SENSITIVE_INFO_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                return False, "Output contains sensitive information"

        return True, None

    def sanitize_input(self, text: str) -> str:
        for pattern in SENSITIVE_INFO_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        if self._check_pii:
            for pattern in PII_PATTERNS:
                text = pattern.sub("[REDACTED]", text)
        return text