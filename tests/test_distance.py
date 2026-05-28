"""Tests for Damerau-Levenshtein distance implementation."""


from nerdo.distance import damerau_levenshtein


class TestDamerauLevenshtein:
    """Core distance calculation tests."""

    def test_identical_strings(self):
        assert damerau_levenshtein("google", "google") == 0

    def test_empty_strings(self):
        assert damerau_levenshtein("", "") == 0

    def test_one_empty(self):
        assert damerau_levenshtein("abc", "") == 3
        assert damerau_levenshtein("", "abc") == 3

    def test_single_insertion(self):
        assert damerau_levenshtein("google", "gooogle") == 1

    def test_single_deletion(self):
        assert damerau_levenshtein("google", "gogle") == 1

    def test_single_substitution(self):
        assert damerau_levenshtein("google", "gaogle") == 1

    def test_single_transposition(self):
        """This is the key test — standard Levenshtein would return 2."""
        assert damerau_levenshtein("google", "ogogle") == 1

    def test_transposition_ab_ba(self):
        assert damerau_levenshtein("ab", "ba") == 1

    def test_multiple_transpositions(self):
        # Two separate transpositions = distance 2
        assert damerau_levenshtein("abcd", "badc") == 2

    def test_completely_different(self):
        assert damerau_levenshtein("abc", "xyz") == 3

    def test_single_char(self):
        assert damerau_levenshtein("a", "b") == 1
        assert damerau_levenshtein("a", "a") == 0


class TestBrandProtectionCases:
    """Real-world brand protection scenarios."""

    def test_paypal_typos(self):
        assert damerau_levenshtein("paypal", "paypla") == 1  # transposition
        assert damerau_levenshtein("paypal", "paypa") == 1   # deletion
        assert damerau_levenshtein("paypal", "paypall") == 1  # insertion
        assert damerau_levenshtein("paypal", "paypaI") == 1  # substitution (l→I)

    def test_google_typos(self):
        assert damerau_levenshtein("google", "googel") == 1  # transposition
        assert damerau_levenshtein("google", "googe") == 1   # deletion
        assert damerau_levenshtein("google", "g0ogle") == 1  # substitution

    def test_microsoft_distance(self):
        # Longer keywords should allow more distance
        assert damerau_levenshtein("microsoft", "mircosoft") == 1  # transposition
        assert damerau_levenshtein("microsoft", "microsft") == 1   # deletion
        assert damerau_levenshtein("microsoft", "micorsoft") == 1  # transposition
