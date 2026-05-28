# NERDO

**NEwly Registered DOmains** — detect suspicious domain registrations for brand protection and typosquatting analysis.

NERDO downloads newly registered domains (last 24h) and compares them against your keywords using multiple detection techniques to identify potential brand abuse, phishing infrastructure, and domain squatting.

## What it detects

| Technique | Confidence | Example |
|-----------|-----------|---------|
| **Damerau-Levenshtein distance** | High | `googel.com`, `paypla.com` |
| **Homoglyph/IDN attacks** | High | `gооgle.com` (Cyrillic 'о') |
| **Punycode abuse** | High | `xn--ggle-55da.com` |
| **Typosquatting patterns** | Medium | `wwwgoogle.com`, `paypal-login.com` |
| **Hyphen manipulation** | Medium | `pay-pal.com` |
| **Character repetition** | Medium | `gooogle.com` |
| **Substring presence** | Low | `googlemasti.xyz` |

### Confidence levels

- **High**: The domain is very likely an impersonation attempt (small edit distance or homoglyph substitution).
- **Medium**: Known squatting patterns detected (suspicious prefixes/suffixes, hyphen tricks, character repetition).
- **Low**: The keyword appears as a substring in the domain name — could be legitimate or suspicious.

## Installation

From PyPI:

```bash
pip install nerdo
```

From source:

```bash
git clone https://github.com/hacklego/nerdo.git
cd nerdo
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

```
usage: nerdo [-h] [-v] [-f {text,json,csv}] [--high-only] [keywords ...]
```

### Examples

```bash
# Single keyword
nerdo google

# Multiple keywords
nerdo google paypal microsoft

# From a file (one keyword per line, # for comments)
nerdo keywords.txt

# From stdin
echo "google" | nerdo

# JSON output for SIEM integration
nerdo -f json google paypal

# CSV output
nerdo -f csv google > results.csv

# Only high confidence matches
nerdo --high-only google

# Verbose mode
nerdo -vv google
```

### Sample output

```
high    googel.com      (damerau-levenshtein, keyword=google)
high    gοοgle.xyz      (homoglyph+damerau-levenshtein, keyword=google)
medium  google-login.net (suffix-login, keyword=google)
medium  wwwgoogle.org   (prefix-www, keyword=google)
low     googlesecurity-check.com    (substring, keyword=google)
```

### JSON output

```json
[
  {
    "domain": "googel.com",
    "keyword": "google",
    "confidence": "high",
    "technique": "damerau-levenshtein",
    "distance": 1
  }
]
```

## How it works

1. Downloads newly registered domains (last 24h) from public sources (whoisdownload.com, secrank.cn as fallback).
2. For each domain, extracts the registrable name (without TLD).
3. Compares against each keyword using:
   - **Damerau-Levenshtein distance** with dynamic thresholds based on keyword length.
   - **Homoglyph normalization** — maps Cyrillic, Greek, and other confusable Unicode characters to ASCII before comparing.
   - **Punycode decoding** — converts IDN domains (`xn--...`) to Unicode for comparison.
   - **Pattern matching** — detects common squatting prefixes (`www`, `my`, `get`...), suffixes (`login`, `secure`, `verify`...), hyphen tricks, and character repetition.
   - **Substring matching** — catches domains that embed the keyword.

### Dynamic thresholds

The edit distance threshold scales with keyword length to reduce false positives on short words and false negatives on long ones:

| Keyword length | Threshold | Example |
|---------------|-----------|---------|
| 1-3 chars | 0 (exact only) | `go` |
| 4-7 chars | 1 | `google` |
| 8-12 chars | 2 | `microsoft` |
| 13+ chars | 3 | `stackoverflow` |

## Known limitations

- **Domain source availability**: Relies on free public sources that may rate-limit or go down. Two sources are configured with automatic fallback.
- **TLD detection**: Uses a simple split-on-dot approach. Multi-part TLDs (`.co.uk`) are not fully parsed — only the leftmost label is analyzed.
- **Homoglyph coverage**: Covers the most common Cyrillic, Greek, and Latin Extended confusables. Not exhaustive — consider extending `homoglyphs.py` for your specific threat model.
- **No persistence**: Results are not stored between runs. Pipe output to a file or integrate with your SIEM.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check nerdo/ tests/
```

## License

GPLv3 — see [LICENSE](LICENSE).
