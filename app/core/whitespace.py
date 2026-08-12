"""Pure whitespace utilities for the core layer.

Stdlib-only; no side effects, no I/O. Companion to ``app.core.text``.

Provenance: authored by the WES execution→PR bridge (F10) acceptance run — the
utility mission run #2 (TEST-MISSION-01-R2) designed but never shipped as code.
"""

from __future__ import annotations

import re

__all__ = ["normalize_whitespace"]

_WHITESPACE_RUN = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse every run of whitespace to a single space and strip the ends.

    Any run of whitespace (spaces, tabs, newlines, carriage returns, form feeds,
    vertical tabs) becomes a single space; leading/trailing whitespace is
    removed. Empty or all-whitespace input returns an empty string. Pure and
    deterministic.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    return _WHITESPACE_RUN.sub(" ", text).strip()
