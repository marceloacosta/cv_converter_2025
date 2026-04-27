from pdf_generator import _sanitize_url


def test_sanitize_valid_https():
    assert _sanitize_url("https://example.com/logo.png") == "https://example.com/logo.png"


def test_sanitize_valid_http():
    assert _sanitize_url("http://example.com/logo.png") == "http://example.com/logo.png"


def test_sanitize_javascript():
    assert _sanitize_url("javascript:alert(1)") == ""


def test_sanitize_data_uri():
    assert _sanitize_url("data:text/html,<script>alert(1)</script>") == ""


def test_sanitize_empty():
    assert _sanitize_url("") == ""


def test_sanitize_with_spaces():
    assert _sanitize_url("  https://example.com/logo.png  ") == "https://example.com/logo.png"
