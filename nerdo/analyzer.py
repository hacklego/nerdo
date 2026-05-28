"""Domain analysis engine — compares newly registered domains against keywords."""

import logging
from dataclasses import dataclass, field

from .distance import damerau_levenshtein
from .homoglyphs import (
    decode_punycode,
    normalize_homoglyphs,
    normalize_leet,
    normalize_leet_variants,
)

logger = logging.getLogger(__name__)

# Confidence levels
HIGH = "high"
MEDIUM = "medium"
LOW = "low"


@dataclass
class Match:
    domain: str
    keyword: str
    confidence: str
    distance: int | None = None
    technique: str = ""


@dataclass
class AnalysisResult:
    high: list[Match] = field(default_factory=list)
    medium: list[Match] = field(default_factory=list)
    low: list[Match] = field(default_factory=list)

    def add(self, match: Match):
        getattr(self, match.confidence).append(match)

    @property
    def all_matches(self) -> list[Match]:
        return self.high + self.medium + self.low

    def __len__(self) -> int:
        return len(self.high) + len(self.medium) + len(self.low)


def _dynamic_threshold(keyword: str) -> int:
    """Calculate distance threshold based on keyword length.

    Short keywords (<=3) → 0 (exact match only via distance)
    Medium keywords (4-7) → 1
    Long keywords (8-12) → 2
    Very long keywords (13+) → 3
    """
    n = len(keyword)
    if n <= 3:
        return 0
    elif n <= 7:
        return 1
    elif n <= 12:
        return 2
    else:
        return 3


def _extract_domain_name(full_domain: str) -> str:
    """Extract the registrable domain name without TLD.

    'evil-google.co.uk' → 'evil-google'
    'paypal-login.com' → 'paypal-login'
    """
    # Remove common multi-part TLDs first, then take first part
    parts = full_domain.split(".")
    if len(parts) >= 1:
        return parts[0]
    return full_domain


def _check_typosquatting_patterns(keyword: str, domain_name: str) -> Match | None:
    """Detect common typosquatting patterns beyond edit distance.

    Patterns detected:
    - Dot omission: www + keyword (wwwgoogle)
    - Hyphen insertion/removal: pay-pal vs paypal
    - Character repetition: gooogle
    - Character omission: gogle
    - Keyword with prefix/suffix additions: mygoogle, googlelogin
    """
    clean_domain = domain_name.replace("-", "")
    clean_keyword = keyword.replace("-", "")

    # Hyphen insertion: 'pay-pal' matches 'paypal'
    if clean_domain == clean_keyword and domain_name != keyword:
        return Match(
            domain="", keyword=keyword, confidence=MEDIUM,
            technique="hyphen-manipulation",
        )

    # Prefix patterns: www, my, the, get, use, go, e-, i-
    prefixes = ("www", "my", "the", "get", "use", "go", "new", "real", "true", "official")
    for prefix in prefixes:
        if domain_name == prefix + keyword or domain_name == prefix + "-" + keyword:
            return Match(
                domain="", keyword=keyword, confidence=MEDIUM,
                technique=f"prefix-{prefix}",
            )

    # Suffix patterns: login, secure, account, verify, support, app, online, web
    suffixes = (
        "login", "secure", "security", "account", "verify", "verification",
        "support", "app", "online", "web", "site", "official", "help",
        "update", "service", "portal", "access", "center",
    )
    for suffix in suffixes:
        if domain_name == keyword + suffix or domain_name == keyword + "-" + suffix:
            return Match(
                domain="", keyword=keyword, confidence=MEDIUM,
                technique=f"suffix-{suffix}",
            )

    # Character repetition: 'gooogle' contains 'google' pattern
    # Check by deduplicating consecutive chars
    def dedup_consecutive(s):
        if not s:
            return s
        result = [s[0]]
        for c in s[1:]:
            if c != result[-1]:
                result.append(c)
        return "".join(result)

    if dedup_consecutive(domain_name) == dedup_consecutive(keyword) and domain_name != keyword:
        return Match(
            domain="", keyword=keyword, confidence=MEDIUM,
            technique="char-repetition",
        )

    return None


def analyze_domain(full_domain: str, keywords: list[str]) -> Match | None:
    """Analyze a single domain against all keywords.

    Returns the highest-confidence match found, or None.
    """
    domain_name = _extract_domain_name(full_domain.strip().lower())
    if not domain_name:
        return None

    # Prepare normalized version for homoglyph detection
    normalized_domain = normalize_homoglyphs(domain_name)

    # Also try punycode decoding
    decoded_domain = None
    if domain_name.startswith("xn--") or "xn--" in full_domain:
        try:
            decoded_full = decode_punycode(full_domain.strip().lower())
            decoded_domain = _extract_domain_name(decoded_full)
        except Exception:
            pass

    best_match = None

    for keyword in keywords:
        keyword_lower = keyword.lower()
        normalized_keyword = normalize_homoglyphs(keyword_lower)
        threshold = _dynamic_threshold(keyword_lower)

        # 1. Damerau-Levenshtein on raw domain name
        dist = damerau_levenshtein(keyword_lower, domain_name)
        if dist <= threshold:
            match = Match(
                domain=full_domain, keyword=keyword, confidence=HIGH,
                distance=dist, technique="damerau-levenshtein",
            )
            return match  # High confidence — return immediately

        # 2. Damerau-Levenshtein on homoglyph-normalized domain
        if normalized_domain != domain_name:
            norm_dist = damerau_levenshtein(normalized_keyword, normalized_domain)
            if norm_dist <= threshold:
                match = Match(
                    domain=full_domain, keyword=keyword, confidence=HIGH,
                    distance=norm_dist, technique="homoglyph+damerau-levenshtein",
                )
                return match

        # 3. Punycode-decoded domain comparison
        if decoded_domain:
            decoded_normalized = normalize_homoglyphs(decoded_domain)
            puny_dist = damerau_levenshtein(normalized_keyword, decoded_normalized)
            if puny_dist <= threshold:
                match = Match(
                    domain=full_domain, keyword=keyword, confidence=HIGH,
                    distance=puny_dist, technique="punycode+damerau-levenshtein",
                )
                return match

        # 4. Leet speak normalization (g00gl3 → google, 1nd1t3x → inditex)
        leet_domain_variants = normalize_leet_variants(domain_name)
        for leet_domain in leet_domain_variants:
            leet_dist = damerau_levenshtein(keyword_lower, leet_domain)
            if leet_dist <= threshold:
                match = Match(
                    domain=full_domain, keyword=keyword, confidence=HIGH,
                    distance=leet_dist, technique="leet+damerau-levenshtein",
                )
                return match

        # 5. Combined leet + homoglyph normalization
        leet_then_homoglyph = normalize_homoglyphs(normalize_leet(domain_name))
        if leet_then_homoglyph != domain_name and leet_then_homoglyph != normalized_domain:
            combo_dist = damerau_levenshtein(normalized_keyword, leet_then_homoglyph)
            if combo_dist <= threshold:
                match = Match(
                    domain=full_domain, keyword=keyword, confidence=HIGH,
                    distance=combo_dist, technique="leet+homoglyph+damerau-levenshtein",
                )
                return match

        # 6. Typosquatting pattern detection (medium confidence)
        typo_match = _check_typosquatting_patterns(keyword_lower, domain_name)
        if typo_match:
            typo_match.domain = full_domain
            if not best_match or best_match.confidence == LOW:
                best_match = typo_match

        # 5. Substring match (low confidence)
        if (
            not best_match
            and len(keyword_lower) >= 4
            and keyword_lower in domain_name
            and domain_name != keyword_lower
        ):
            best_match = Match(
                domain=full_domain, keyword=keyword, confidence=LOW,
                technique="substring",
            )

    return best_match


def analyze_domains(domain_file: str, keywords: list[str]) -> AnalysisResult:
    """Analyze a file of domains against a list of keywords.

    Returns an AnalysisResult with matches grouped by confidence level.
    """
    result = AnalysisResult()
    seen = set()

    with open(domain_file) as f:
        for line in f:
            full_domain = line.strip()
            if not full_domain or full_domain in seen:
                continue
            seen.add(full_domain)

            match = analyze_domain(full_domain, keywords)
            if match:
                result.add(match)

    logger.info(
        "Analysis complete: %d high, %d medium, %d low confidence matches",
        len(result.high), len(result.medium), len(result.low),
    )
    return result
