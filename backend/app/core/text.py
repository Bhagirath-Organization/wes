"""Pure text utilities for the core layer.

Stdlib-only; no side effects, no I/O, no configuration reads.

Provenance (TEST-MISSION-01, the first live charter mission): specified by T001
(run ``2e2cae92``), implemented per T002 (run ``5824c178``), tested per T003
(run ``aa2d84d2``); landed as a human-governed SOP-CODING change per the
WES-DEC-010 roadmap. The canonical name is ``truncate`` — the Founder-approved
shape in TEST-MISSION-CHARTER §2 — reconciling T002's ``truncate_text`` draft.
"""

from __future__ import annotations

import unicodedata

__all__ = ["truncate"]


def _clusters(text: str) -> list[str]:
    """Split ``text`` into grapheme-like clusters using stdlib ``unicodedata``.

    A cluster is a base code point followed by its zero-or-more combining
    marks, so a base character is never separated from its diacritics.

    Full UAX-#29 segmentation (e.g. emoji ZWJ family sequences) would require a
    third-party library, which this task's constraints disallow (T001 escalated
    the dependency decision; T002 resolved it stdlib-only with this documented
    limitation).
    """
    clusters: list[str] = []
    for ch in text:
        if clusters and unicodedata.combining(ch):
            clusters[-1] += ch
        else:
            clusters.append(ch)
    return clusters


def truncate(text: str, limit: int, suffix: str = "…") -> str:
    """Shorten ``text`` so the result is at most ``limit`` characters, suffix included.

    Length is measured in grapheme-like clusters (see ``_clusters``): a base
    character plus its combining marks counts as one. The invariant is
    ``cluster_len(result) <= limit`` for every valid call. When truncation
    occurs the result is the longest cluster-prefix of ``text`` followed by
    ``suffix``; text already within ``limit`` is returned unchanged.

    Error contract (per the T001 spec's QA-4 pin — exact type per case, no
    silent coercion): ``TypeError`` for non-``str`` ``text``/``suffix`` or a
    non-``int`` (or ``bool``) ``limit``; ``ValueError`` for ``limit <= 0`` or
    ``limit`` smaller than the suffix length.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError(f"limit must be int, got {type(limit).__name__}")
    if not isinstance(suffix, str):
        raise TypeError(f"suffix must be str, got {type(suffix).__name__}")
    if limit <= 0:
        raise ValueError(f"limit must be positive, got {limit}")

    suffix_clusters = _clusters(suffix)
    if limit < len(suffix_clusters):
        raise ValueError(
            f"limit ({limit}) is smaller than the suffix length ({len(suffix_clusters)})"
        )

    clusters = _clusters(text)
    if len(clusters) <= limit:
        return text
    head = clusters[: limit - len(suffix_clusters)]
    return "".join(head) + suffix
