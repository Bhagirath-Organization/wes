from app.core.whitespace import normalize_whitespace


def test_normalize_whitespace_collapses_and_strips():
    assert normalize_whitespace("  a\t b\n  c  ") == "a b c"
    assert normalize_whitespace("") == ""
