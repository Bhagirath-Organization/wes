"""Whitespace helpers (bridge acceptance demonstrator, F10 — correctly placed).

This is the honest re-placement of the PR #25 demonstrator: it lands under
backend/app/core/ so it is part of the build and importable in production.
"""
import re


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace to single spaces and strip the ends."""
    return re.sub(r"\s+", " ", text).strip()
