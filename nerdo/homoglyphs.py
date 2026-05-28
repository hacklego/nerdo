"""Unicode homoglyph normalization and punycode handling for domain analysis.

Covers the most common confusable characters used in domain squatting attacks.
Based on Unicode TR39 confusables and common IDN homoglyph abuse patterns.
"""

import unicodedata

# Mapping of visually confusable characters to their ASCII equivalents.
# Covers Cyrillic, Greek, Latin extended, and other common substitutions.
CONFUSABLES: dict[str, str] = {
    # Cyrillic → Latin
    "\u0430": "a",  # а → a
    "\u0435": "e",  # е → e
    "\u043e": "o",  # о → o
    "\u0440": "p",  # р → p
    "\u0441": "c",  # с → c
    "\u0443": "y",  # у → y
    "\u0445": "x",  # х → x
    "\u043a": "k",  # к → k
    "\u043b": "l",  # л → l (visually similar in some fonts)
    "\u043c": "m",  # м → m (lowercase)
    "\u0442": "t",  # т → t
    "\u0456": "i",  # і → i (Ukrainian)
    "\u0458": "j",  # ј → j (Serbian)
    "\u0455": "s",  # ѕ → s (Macedonian)
    "\u044a": "b",  # ъ → b (visually similar in some fonts)
    "\u0432": "b",  # в → b
    "\u043d": "h",  # н → h
    "\u0433": "r",  # г → r (visually similar in some fonts)
    "\u04bb": "h",  # һ → h (Bashkir)
    "\u0410": "A",  # А → A
    "\u0412": "B",  # В → B
    "\u0415": "E",  # Е → E
    "\u041a": "K",  # К → K
    "\u041c": "M",  # М → M
    "\u041d": "H",  # Н → H
    "\u041e": "O",  # О → O
    "\u0420": "P",  # Р → P
    "\u0421": "C",  # С → C
    "\u0422": "T",  # Т → T
    "\u0425": "X",  # Х → X
    "\u0423": "Y",  # У → Y
    # Greek → Latin
    "\u03b1": "a",  # α → a
    "\u03b5": "e",  # ε → e
    "\u03b9": "i",  # ι → i
    "\u03bf": "o",  # ο → o
    "\u03c1": "p",  # ρ → p
    "\u03c4": "t",  # τ → t (visually similar in sans-serif)
    "\u03ba": "k",  # κ → k
    "\u03bd": "v",  # ν → v
    "\u03c5": "u",  # υ → u
    "\u0391": "A",  # Α → A
    "\u0392": "B",  # Β → B
    "\u0395": "E",  # Ε → E
    "\u0396": "Z",  # Ζ → Z
    "\u0397": "H",  # Η → H
    "\u0399": "I",  # Ι → I
    "\u039a": "K",  # Κ → K
    "\u039c": "M",  # Μ → M
    "\u039d": "N",  # Ν → N
    "\u039f": "O",  # Ο → O
    "\u03a1": "P",  # Ρ → P
    "\u03a4": "T",  # Τ → T
    "\u03a7": "X",  # Χ → X
    "\u03a5": "Y",  # Υ → Y
    "\u03a9": "W",  # Ω → W (loose but used in attacks)
    # Latin extended / special
    "\u0131": "i",  # ı → i (Turkish dotless i)
    "\u00f0": "d",  # ð → d
    "\u0111": "d",  # đ → d
    "\u0142": "l",  # ł → l
    "\u00f8": "o",  # ø → o
    "\u00e6": "ae",  # æ → ae
    "\u00df": "ss",  # ß → ss
    "\u00e0": "a",  # à → a
    "\u00e1": "a",  # á → a
    "\u00e2": "a",  # â → a
    "\u00e3": "a",  # ã → a
    "\u00e4": "a",  # ä → a
    "\u00e8": "e",  # è → e
    "\u00e9": "e",  # é → e
    "\u00ea": "e",  # ê → e
    "\u00eb": "e",  # ë → e
    "\u00ec": "i",  # ì → i
    "\u00ed": "i",  # í → i
    "\u00ee": "i",  # î → i
    "\u00ef": "i",  # ï → i
    "\u00f2": "o",  # ò → o
    "\u00f3": "o",  # ó → o
    "\u00f4": "o",  # ô → o
    "\u00f5": "o",  # õ → o
    "\u00f6": "o",  # ö → o
    "\u00f9": "u",  # ù → u
    "\u00fa": "u",  # ú → u
    "\u00fb": "u",  # û → u
    "\u00fc": "u",  # ü → u
    "\u00fd": "y",  # ý → y
    "\u00ff": "y",  # ÿ → y
    "\u00f1": "n",  # ñ → n
    "\u00e7": "c",  # ç → c
    # Numbers / symbols commonly used in squatting
    "\u2070": "0",  # ⁰ → 0 (superscript)
    "\u00b9": "1",  # ¹ → 1
    "\u00b2": "2",  # ² → 2
    "\u00b3": "3",  # ³ → 3
    # Fullwidth Latin
    "\uff41": "a",  # ａ → a
    "\uff42": "b",  # ｂ → b
    "\uff43": "c",  # ｃ → c
    "\uff44": "d",  # ｄ → d
    "\uff45": "e",  # ｅ → e
    "\uff46": "f",  # ｆ → f
    "\uff47": "g",  # ｇ → g
    "\uff48": "h",  # ｈ → h
    "\uff49": "i",  # ｉ → i
    "\uff4a": "j",  # ｊ → j
    "\uff4b": "k",  # ｋ → k
    "\uff4c": "l",  # ｌ → l
    "\uff4d": "m",  # ｍ → m
    "\uff4e": "n",  # ｎ → n
    "\uff4f": "o",  # ｏ → o
    "\uff50": "p",  # ｐ → p
    "\uff51": "q",  # ｑ → q
    "\uff52": "r",  # ｒ → r
    "\uff53": "s",  # ｓ → s
    "\uff54": "t",  # ｔ → t
    "\uff55": "u",  # ｕ → u
    "\uff56": "v",  # ｖ → v
    "\uff57": "w",  # ｗ → w
    "\uff58": "x",  # ｘ → x
    "\uff59": "y",  # ｙ → y
    "\uff5a": "z",  # ｚ → z
}


# Leet speak (1337) substitutions: digit/symbol → letter(s).
# Some digits map to multiple possible letters (e.g., 1 → i or l).
# We store the primary mapping and alternates separately.
LEET_PRIMARY: dict[str, str] = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "9": "g",
    "@": "a",
    "$": "s",
    "!": "i",
    "|": "l",
    "+": "t",
}

LEET_ALTERNATES: dict[str, list[str]] = {
    "1": ["l"],
    "0": ["q"],
    "5": ["z"],
}


def normalize_leet(text: str) -> str:
    """Normalize leet speak substitutions to their letter equivalents.

    Applies primary mapping: g00gl3 → google, 1nd1t3x → inditex
    """
    return "".join(LEET_PRIMARY.get(c, c) for c in text.lower())


def normalize_leet_variants(text: str) -> list[str]:
    """Generate normalized variants considering alternate leet mappings.

    Returns a list of possible normalizations (primary + alternates).
    The first element is always the primary normalization.
    """
    primary = normalize_leet(text)
    variants = [primary]

    # Generate variants for characters with alternate mappings
    text_lower = text.lower()
    for i, c in enumerate(text_lower):
        if c in LEET_ALTERNATES:
            for alt in LEET_ALTERNATES[c]:
                variant = list(normalize_leet(text_lower))
                variant[i] = alt
                v = "".join(variant)
                if v not in variants:
                    variants.append(v)

    return variants


def decode_punycode(domain: str) -> str:
    """Decode a punycode/IDN domain to its Unicode representation.

    Handles both full IDN domains (xn--...) and mixed domains where only
    some labels are punycode-encoded.
    """
    try:
        return domain.encode("ascii").decode("idna")
    except (UnicodeError, UnicodeDecodeError):
        # Try label-by-label decoding for mixed domains
        parts = domain.split(".")
        decoded = []
        for part in parts:
            try:
                decoded.append(part.encode("ascii").decode("idna"))
            except (UnicodeError, UnicodeDecodeError):
                decoded.append(part)
        return ".".join(decoded)


def normalize_homoglyphs(text: str) -> str:
    """Normalize a string by replacing confusable Unicode characters with
    their ASCII equivalents.

    Steps:
    1. NFKD Unicode normalization (decomposes characters)
    2. Replace known confusable characters
    3. Lowercase
    """
    # First pass: Unicode NFKD normalization
    text = unicodedata.normalize("NFKD", text)

    # Second pass: replace known confusables
    result = []
    for char in text:
        replacement = CONFUSABLES.get(char)
        if replacement:
            result.append(replacement)
        elif char.isascii():
            result.append(char)
        else:
            # Try to find the base character by stripping combining marks
            if not unicodedata.combining(char):
                result.append(char)

    return "".join(result).lower()
