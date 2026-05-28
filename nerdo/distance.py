"""Damerau-Levenshtein distance implementation."""


def damerau_levenshtein(s1: str, s2: str) -> int:
    """Compute the Damerau-Levenshtein distance between two strings.

    Unlike standard Levenshtein, this handles transpositions of adjacent
    characters as a single operation (cost 1 instead of 2).

    Uses the optimal string alignment variant (restricted edit distance).
    """
    len1, len2 = len(s1), len(s2)

    # Short-circuit trivial cases
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1
    if s1 == s2:
        return 0

    # Use a simple 2D list instead of numpy for this small-scale computation
    d = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        d[i][0] = i
    for j in range(len2 + 1):
        d[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            d[i][j] = min(
                d[i - 1][j] + 1,        # deletion
                d[i][j - 1] + 1,        # insertion
                d[i - 1][j - 1] + cost,  # substitution
            )

            # Transposition of two adjacent characters
            if (
                i > 1
                and j > 1
                and s1[i - 1] == s2[j - 2]
                and s1[i - 2] == s2[j - 1]
            ):
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)

    return d[len1][len2]
