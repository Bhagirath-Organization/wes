"""Unit tests for app.core.whitespace.normalize_whitespace (bridge acceptance)."""

from __future__ import annotations

import pytest

from app.core.whitespace import normalize_whitespace


def test_collapses_internal_runs():
    assert normalize_whitespace("a   b\t\tc") == "a b c"


def test_strips_ends():
    assert normalize_whitespace("  hello  ") == "hello"


def test_newlines_and_tabs_collapse():
    assert normalize_whitespace("a\n\n\tb\r\nc") == "a b c"


def test_empty_and_all_whitespace_return_empty():
    assert normalize_whitespace("") == ""
    assert normalize_whitespace("   \n\t ") == ""


def test_single_token_unchanged():
    assert normalize_whitespace("word") == "word"


def test_non_str_raises_type_error():
    with pytest.raises(TypeError):
        normalize_whitespace(None)


def test_pure_no_mutation():
    s = "x  y"
    normalize_whitespace(s)
    assert s == "x  y"
