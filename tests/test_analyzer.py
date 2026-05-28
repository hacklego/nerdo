"""Tests for domain analysis engine."""

import os
import tempfile

from nerdo.analyzer import (
    _check_typosquatting_patterns,
    _dynamic_threshold,
    _extract_domain_name,
    analyze_domain,
    analyze_domains,
)


class TestDynamicThreshold:

    def test_short_keyword(self):
        assert _dynamic_threshold("go") == 0
        assert _dynamic_threshold("abc") == 0

    def test_medium_keyword(self):
        assert _dynamic_threshold("google") == 1
        assert _dynamic_threshold("paypal") == 1

    def test_long_keyword(self):
        assert _dynamic_threshold("microsoft") == 2
        assert _dynamic_threshold("facebook") == 2

    def test_very_long_keyword(self):
        assert _dynamic_threshold("stackoverflow") == 3


class TestExtractDomainName:

    def test_simple_domain(self):
        assert _extract_domain_name("google.com") == "google"

    def test_subdomain_style(self):
        assert _extract_domain_name("evil-google.co.uk") == "evil-google"

    def test_no_tld(self):
        assert _extract_domain_name("localhost") == "localhost"


class TestTyposquattingPatterns:

    def test_hyphen_manipulation(self):
        match = _check_typosquatting_patterns("paypal", "pay-pal")
        assert match is not None
        assert match.technique == "hyphen-manipulation"

    def test_www_prefix(self):
        match = _check_typosquatting_patterns("google", "wwwgoogle")
        assert match is not None
        assert match.technique == "prefix-www"

    def test_login_suffix(self):
        match = _check_typosquatting_patterns("paypal", "paypallogin")
        assert match is not None
        assert match.technique == "suffix-login"

    def test_hyphen_suffix(self):
        match = _check_typosquatting_patterns("paypal", "paypal-login")
        assert match is not None
        assert match.technique == "suffix-login"

    def test_char_repetition(self):
        match = _check_typosquatting_patterns("google", "gooogle")
        assert match is not None
        assert match.technique == "char-repetition"

    def test_no_match(self):
        match = _check_typosquatting_patterns("google", "amazon")
        assert match is None


class TestAnalyzeDomain:

    def test_exact_match_distance_zero(self):
        match = analyze_domain("google.com", ["google"])
        assert match is not None
        assert match.confidence == "high"
        assert match.distance == 0

    def test_one_char_off(self):
        match = analyze_domain("googel.com", ["google"])
        assert match is not None
        assert match.confidence == "high"

    def test_substring_match(self):
        match = analyze_domain("mygooglesite.com", ["google"])
        # Could be medium (prefix pattern) or low (substring)
        assert match is not None

    def test_no_match(self):
        match = analyze_domain("totallyunrelated.com", ["google"])
        assert match is None

    def test_homoglyph_detection(self):
        # Cyrillic 'о' instead of Latin 'o'
        match = analyze_domain("g\u043e\u043egle.com", ["google"])
        assert match is not None
        assert match.confidence == "high"
        assert "homoglyph" in match.technique

    def test_leet_speak_google(self):
        match = analyze_domain("g00gl3.com", ["google"])
        assert match is not None
        assert match.confidence == "high"
        assert "leet" in match.technique

    def test_leet_speak_inditex(self):
        match = analyze_domain("1nd1t3x.com", ["inditex"])
        assert match is not None
        assert match.confidence == "high"
        assert "leet" in match.technique

    def test_leet_speak_paypal(self):
        match = analyze_domain("p4yp4l.com", ["paypal"])
        assert match is not None
        assert match.confidence == "high"

    def test_leet_partial(self):
        # Only partially leet: g0ogle (one substitution)
        match = analyze_domain("g0ogle.com", ["google"])
        assert match is not None
        assert match.confidence == "high"

    def test_short_keyword_strict(self):
        # Short keywords should only match exactly (threshold=0)
        match = analyze_domain("xyz.com", ["go"])
        # distance("go", "xyz") = 2, threshold for "go" is 0, no substring
        assert match is None


class TestAnalyzeDomains:

    def test_file_analysis(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("google.com\n")
            f.write("googel.com\n")
            f.write("totallyunrelated.xyz\n")
            f.write("mygoogle-login.com\n")
            f.name
            f.flush()
            path = f.name

        try:
            result = analyze_domains(path, ["google"])
            assert len(result.high) >= 1  # googel.com should be high
            assert len(result) >= 2  # at least high + something else
        finally:
            os.unlink(path)

    def test_deduplication(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("googel.com\n")
            f.write("googel.com\n")  # duplicate
            f.flush()
            path = f.name

        try:
            result = analyze_domains(path, ["google"])
            assert len(result.high) == 1  # Should not duplicate
        finally:
            os.unlink(path)
