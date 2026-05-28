"""Tests for homoglyph normalization and punycode handling."""

from nerdo.homoglyphs import (
    decode_punycode,
    normalize_homoglyphs,
    normalize_leet,
    normalize_leet_variants,
)


class TestNormalizeHomoglyphs:
    """Test Unicode confusable normalization."""

    def test_ascii_passthrough(self):
        assert normalize_homoglyphs("google") == "google"

    def test_cyrillic_a(self):
        # Cyrillic 'а' (U+0430) should normalize to Latin 'a'
        assert normalize_homoglyphs("g\u043eogle") == "google"

    def test_cyrillic_full_word(self):
        # All Cyrillic letters that look like Latin
        assert normalize_homoglyphs("\u0430\u0440\u0440\u043b\u0435") == "apple"

    def test_greek_alpha(self):
        assert normalize_homoglyphs("\u03b1pple") == "apple"

    def test_mixed_scripts(self):
        # Mix of Cyrillic and Latin
        assert normalize_homoglyphs("g\u043e\u043egle") == "google"

    def test_accented_characters(self):
        assert normalize_homoglyphs("g\u00f6\u00f6gle") == "google"

    def test_case_normalization(self):
        assert normalize_homoglyphs("Google") == "google"
        assert normalize_homoglyphs("GOOGLE") == "google"

    def test_german_eszett(self):
        result = normalize_homoglyphs("\u00df")
        assert result == "ss"

    def test_empty_string(self):
        assert normalize_homoglyphs("") == ""


class TestDecodePunycode:
    """Test punycode/IDN decoding."""

    def test_ascii_passthrough(self):
        assert decode_punycode("google.com") == "google.com"

    def test_punycode_domain(self):
        # xn--e1afmapc.xn--p1ai is москва.рф
        result = decode_punycode("xn--e1afmapc.xn--p1ai")
        assert "." in result  # Should decode to something with a dot

    def test_invalid_punycode(self):
        # Should not crash on invalid input
        result = decode_punycode("xn--invalid!!!")
        assert isinstance(result, str)

    def test_mixed_punycode(self):
        # Only some labels are punycode
        result = decode_punycode("www.xn--n3h.com")
        assert result.startswith("www.")
        assert result.endswith(".com")


class TestNormalizeLeet:
    """Test leet speak (1337) normalization."""

    def test_google_leet(self):
        assert normalize_leet("g00gl3") == "google"

    def test_inditex_leet(self):
        assert normalize_leet("1nd1t3x") == "inditex"

    def test_paypal_leet(self):
        assert normalize_leet("p4yp4l") == "paypal"

    def test_apple_leet(self):
        assert normalize_leet("4ppl3") == "apple"

    def test_microsoft_leet(self):
        assert normalize_leet("m1cr0$0f7") == "microsoft"

    def test_no_leet(self):
        assert normalize_leet("google") == "google"

    def test_at_sign(self):
        assert normalize_leet("@m@zon") == "amazon"

    def test_mixed_case(self):
        assert normalize_leet("G00GL3") == "google"

    def test_empty(self):
        assert normalize_leet("") == ""

    def test_partial_leet(self):
        # Only some chars are leet
        assert normalize_leet("g0ogle") == "google"


class TestNormalizeLeetVariants:
    """Test leet speak variant generation."""

    def test_single_variant_char(self):
        # "1" can be "i" (primary) or "l" (alternate)
        variants = normalize_leet_variants("1ogin")
        assert "iogin" in variants
        assert "login" in variants

    def test_no_alternates(self):
        # No alternate-capable chars
        variants = normalize_leet_variants("google")
        assert variants == ["google"]

    def test_primary_always_first(self):
        variants = normalize_leet_variants("g00gl3")
        assert variants[0] == "google"
