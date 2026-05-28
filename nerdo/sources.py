"""Domain list download sources with retry and fallback support."""

import logging
import os
import time
import zipfile
from base64 import b64encode
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, multiplied by attempt number


class DownloadError(Exception):
    pass


def _download_with_retry(url: str, headers: dict, max_retries: int = MAX_RETRIES) -> bytes:
    """Download a URL with exponential backoff retry."""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Download attempt %d: %s", attempt, url)
            r = requests.get(url, headers=headers, timeout=60)
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:
            last_error = e
            if attempt < max_retries:
                wait = RETRY_BACKOFF * attempt
                logger.warning("Attempt %d failed: %s. Retrying in %ds...", attempt, e, wait)
                time.sleep(wait)
            else:
                logger.error("All %d attempts failed: %s", max_retries, e)

    raise DownloadError(f"Failed to download {url} after {max_retries} attempts: {last_error}")


def download_from_whoisdownload(directory: str, date: datetime | None = None) -> str:
    """Download newly registered domains from whoisdownload.com.

    Returns the path to the extracted domain-names.txt file.
    """
    base_url = "https://www.whoisdownload.com/download-panel/free-download-file/"
    target_date = date or (datetime.now() - timedelta(days=1))
    filename = target_date.strftime("%Y-%m-%d") + ".zip"
    b64_filename = b64encode(filename.encode("ascii")).decode()
    resource = b64_filename + "/nrd/home"

    headers = {"User-Agent": USER_AGENT}

    content = _download_with_retry(base_url + resource, headers)

    zip_path = os.path.join(directory, filename)
    with open(zip_path, "wb") as f:
        f.write(content)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(directory)

    domain_file = os.path.join(directory, "domain-names.txt")
    if not os.path.exists(domain_file):
        # Some zips use different naming — try to find any .txt file
        for name in os.listdir(directory):
            if name.endswith(".txt"):
                domain_file = os.path.join(directory, name)
                break
        else:
            raise DownloadError(f"No domain list file found in {filename}")

    return domain_file


def download_from_secrank(directory: str, date: datetime | None = None) -> str:
    """Download newly registered domains from secrank.cn (fallback source).

    Returns the path to the extracted domain list file.
    """
    target_date = date or (datetime.now() - timedelta(days=1))
    date_str = target_date.strftime("%Y-%m-%d")
    url = f"https://www.secrank.cn/static/data/nrd/{date_str}.zip"

    headers = {"User-Agent": USER_AGENT}

    content = _download_with_retry(url, headers)

    zip_path = os.path.join(directory, f"secrank-{date_str}.zip")
    with open(zip_path, "wb") as f:
        f.write(content)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(directory)

    # Find the extracted text file
    for name in os.listdir(directory):
        if name.endswith(".txt") and "domain" in name.lower():
            return os.path.join(directory, name)

    # Fallback: return first .txt file
    for name in os.listdir(directory):
        if name.endswith(".txt"):
            return os.path.join(directory, name)

    raise DownloadError("No domain list file found in secrank download")


# Ordered list of sources to try
SOURCES = [
    ("whoisdownload", download_from_whoisdownload),
    ("secrank", download_from_secrank),
]


def download_domains(directory: str, date: datetime | None = None) -> str:
    """Try each domain source in order until one succeeds.

    Returns the path to the domain list file.
    """
    errors = []
    for name, downloader in SOURCES:
        try:
            logger.info("Trying source: %s", name)
            path = downloader(directory, date)
            logger.info("Successfully downloaded from %s", name)
            return path
        except (DownloadError, Exception) as e:
            logger.warning("Source %s failed: %s", name, e)
            errors.append((name, e))

    error_summary = "; ".join(f"{name}: {err}" for name, err in errors)
    raise DownloadError(f"All domain sources failed. {error_summary}")
