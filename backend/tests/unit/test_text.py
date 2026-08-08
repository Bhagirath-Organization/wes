"""Unit tests for ``app.core.text.truncate`` (TEST-MISSION-01 charter §2).

Adapted from the mission's T003 test-suite artifact (run ``aa2d84d2``, author
Dijkstra/QA), with its two flagged open questions resolved: the import path is
``app.core.text`` and the canonical name is ``truncate`` (charter shape).
Covers the charter's five acceptance criteria and the T001 spec's pinned
QA-1..4 contract: suffix counts toward ``limit``; grapheme-cluster safety
(stdlib approximation — base + combining marks); deterministic errors.

Combining sequences are written with explicit escapes (``"e\\u0301"``) so the
decomposed form is unambiguous in source.
"""

from __future__ import annotations

import pytest

from app.core.text import truncate

DEFAULT_SUFFIX = "…"
E_ACUTE = "e\u0301"  # decomposed: base + combining acute = ONE cluster


class TestTotalLengthBound:
    """AC-2 / QA-2 — the result never exceeds ``limit``, suffix included."""

    def test_result_never_exceeds_limit(self):
        text = "The quick brown fox jumps over the lazy dog"
        for limit in range(len(DEFAULT_SUFFIX), len(text) + 5):
            result = truncate(text, limit, suffix=DEFAULT_SUFFIX)
            assert len(result) <= limit, f"limit={limit}: len(result)={len(result)} exceeds bound"

    def test_truncated_result_ends_with_suffix(self):
        result = truncate("abcdefghij", 5, suffix=DEFAULT_SUFFIX)
        assert result.endswith(DEFAULT_SUFFIX) and len(result) <= 5
        assert result == "abcd…"

    def test_multichar_suffix_included_in_bound(self):
        result = truncate("abcdefghij", 6, suffix="...")
        assert result == "abc..."  # 6 total = 3 content + 3 suffix

    def test_limit_equal_to_suffix_length_yields_suffix_only(self):
        # Deterministic per QA-3/R4: the smallest valid limit returns just the suffix.
        assert truncate("abcdef", 1) == "…"
        assert truncate("abcdef", 3, suffix="...") == "..."


class TestNoTruncationNeeded:
    """AC-1 / AC-3 — text within the limit is returned unchanged, incl. the exact boundary."""

    def test_shorter_than_limit_unchanged(self):
        assert truncate("abc", 10) == "abc"

    def test_exact_boundary_unchanged(self):
        text = "abcdefghij"
        assert truncate(text, len(text)) == text

    def test_combining_marks_count_as_one_at_boundary(self):
        # "caf" + decomposed e-acute: 5 code points but 4 clusters -> fits limit=4.
        text = "caf" + E_ACUTE
        assert len(text) == 5
        assert truncate(text, 4) == text


class TestEmptyString:
    """AC-4 — empty input is handled."""

    def test_empty_returns_empty(self):
        assert truncate("", 5) == ""

    def test_empty_with_minimal_limit(self):
        assert truncate("", 1) == ""


class TestGraphemeSafety:
    """QA-1 — a base character is never separated from its combining marks."""

    def test_never_cuts_inside_a_cluster(self):
        text = ("a" + E_ACUTE + "iou") * 3  # mixed plain + combining clusters
        for limit in range(1, len(text) + 2):
            result = truncate(text, limit)
            body = result[:-1] if result.endswith(DEFAULT_SUFFIX) else result
            # The body must be a prefix of the source, and the source's next code
            # point after the cut must not be a combining mark (no cluster split).
            assert text.startswith(body)
            if len(body) < len(text):
                assert text[len(body)] != "\u0301", f"cluster split at limit={limit}"

    def test_cluster_kept_intact_across_cut(self):
        text = "xx" + E_ACUTE + "yy"  # clusters: x, x, é, y, y
        assert truncate(text, 4) == "xx" + E_ACUTE + "…"

    def test_cut_before_cluster_not_inside_it(self):
        text = "ab" + E_ACUTE + "cd"
        result = truncate(text, 3)  # head = 2 clusters + suffix
        assert result == "ab…"
        assert "\u0301" not in result


class TestErrorContract:
    """QA-3 / QA-4 — deterministic, typed errors; no silent coercion."""

    @pytest.mark.parametrize("limit", [-1, -5, -100])
    def test_negative_limit_raises_value_error(self, limit):
        with pytest.raises(ValueError):
            truncate("abc", limit)

    def test_zero_limit_raises_value_error(self):
        with pytest.raises(ValueError):
            truncate("abc", 0)

    def test_limit_smaller_than_suffix_raises_value_error(self):
        with pytest.raises(ValueError):
            truncate("abcdef", 2, suffix="...")

    @pytest.mark.parametrize("bad_text", [None, 42, b"bytes", ["a"]])
    def test_non_str_text_raises_type_error(self, bad_text):
        with pytest.raises(TypeError):
            truncate(bad_text, 5)

    @pytest.mark.parametrize("bad_limit", [None, "5", 5.0, True])
    def test_non_int_limit_raises_type_error(self, bad_limit):
        with pytest.raises(TypeError):
            truncate("abc", bad_limit)

    def test_non_str_suffix_raises_type_error(self):
        with pytest.raises(TypeError):
            truncate("abc", 5, suffix=None)


class TestPurity:
    """T001 §1 — deterministic, no side effects."""

    def test_deterministic(self):
        args = ("The quick brown fox", 10, "…")
        assert truncate(*args) == truncate(*args)

    def test_input_not_mutated(self):
        text = "immutable input"
        truncate(text, 5)
        assert text == "immutable input"
