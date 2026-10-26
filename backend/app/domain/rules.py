"""Input normalization rules shared by API schemas (framework-independent)."""

from __future__ import annotations

import re

from app.domain.models import DESCRIPTION_MAX, MEMO_MAX

# Description is a one-line text: reject control characters including newlines. [assumption]
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_MEMO_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # newlines/tabs allowed


def normalize_description(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty or whitespace only")
    if len(value) > DESCRIPTION_MAX:
        raise ValueError(f"must be at most {DESCRIPTION_MAX} characters")
    if _CONTROL.search(value):
        raise ValueError("must be a single line without control characters")
    return value


def normalize_memo(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > MEMO_MAX:
        raise ValueError(f"must be at most {MEMO_MAX} characters")
    if _MEMO_CONTROL.search(value):
        raise ValueError("must not contain control characters")
    return value
