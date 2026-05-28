"""NERDO: NEwly Registered DOmains — detect suspicious domain registrations."""

import argparse
import csv
import io
import json
import logging
import sys
import tempfile
from collections.abc import Iterator
from typing import Any

from .analyzer import AnalysisResult, analyze_domains
from .sources import download_domains

logger = logging.getLogger(__name__)


def init_log(verbosity: int = 0, log_file: str | None = None):
    if verbosity == 1:
        level = logging.INFO
    elif verbosity > 1:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        filename=log_file,
        format="%(levelname)s:%(name)s:%(message)s",
    )


def format_text(result: AnalysisResult) -> str:
    """Format results as human-readable text."""
    lines = []
    for match in result.high:
        lines.append(f"high\t{match.domain}\t({match.technique}, keyword={match.keyword})")
    for match in result.medium:
        lines.append(f"medium\t{match.domain}\t({match.technique}, keyword={match.keyword})")
    for match in result.low:
        lines.append(f"low\t{match.domain}\t({match.technique}, keyword={match.keyword})")
    return "\n".join(lines)


def format_json(result: AnalysisResult) -> str:
    """Format results as JSON."""
    data = []
    for match in result.all_matches:
        entry = {
            "domain": match.domain,
            "keyword": match.keyword,
            "confidence": match.confidence,
            "technique": match.technique,
        }
        if match.distance is not None:
            entry["distance"] = match.distance
        data.append(entry)
    return json.dumps(data, indent=2)


def format_csv(result: AnalysisResult) -> str:
    """Format results as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["confidence", "domain", "keyword", "technique", "distance"])
    for match in result.all_matches:
        writer.writerow([
            match.confidence,
            match.domain,
            match.keyword,
            match.technique,
            match.distance if match.distance is not None else "",
        ])
    return output.getvalue()


FORMATTERS = {
    "text": format_text,
    "json": format_json,
    "csv": format_csv,
}


def main():
    parser = argparse.ArgumentParser(
        description="NERDO: NEwly Registered DOmains — detect suspicious domain registrations "
        "for brand protection and typosquatting analysis.",
    )
    parser.add_argument(
        "keywords",
        nargs="*",
        help="Keywords to search for (strings or paths to files with keywords). "
        "Reads from stdin if none provided.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for info, -vv for debug).",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--high-only",
        action="store_true",
        help="Only show high confidence matches.",
    )

    args = parser.parse_args()

    init_log(args.verbose)
    keywords = list(read_text_targets(args.keywords))

    if not keywords:
        parser.error("No keywords provided. Pass keywords as arguments, a file, or via stdin.")

    logger.info("Analyzing domains for keywords: %s", keywords)

    with tempfile.TemporaryDirectory() as tmpdir:
        domain_file = download_domains(tmpdir)
        result = analyze_domains(domain_file, keywords)

    if args.high_only:
        result.medium.clear()
        result.low.clear()

    formatter = FORMATTERS[args.format]
    output = formatter(result)
    if output:
        print(output)

    if not result.all_matches:
        logger.info("No suspicious domains found.")


def read_text_targets(targets: Any) -> Iterator[str]:
    yield from read_text_lines(read_targets(targets))


def read_targets(targets: Any | None) -> Iterator[str]:
    """Read keywords from arguments, files, or stdin."""
    if not targets:
        yield from sys.stdin
        return

    for target in targets:
        try:
            with open(target) as fi:
                yield from fi
        except FileNotFoundError:
            yield target


def read_text_lines(fd: Iterator[str]) -> Iterator[str]:
    """Yield non-empty, non-comment lines."""
    for line in fd:
        line = line.strip()
        if line and not line.startswith("#"):
            yield line


if __name__ == "__main__":
    main()
