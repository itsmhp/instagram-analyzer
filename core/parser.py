from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, Tag

from config import (
    CONNECTIONS_SUBPATH,
    CSS_ENTRY_CARD,
    CSS_TYPE_B_HEADING,
    FOLLOWERS_GLOB,
    INSTAGRAM_BASE,
    INSTAGRAM_REDIRECT_PREFIX,
    TIMESTAMP_FORMAT,
)
from core.models import ProfileRecord

logger = logging.getLogger(__name__)


def parse_export_file(html_path: Path) -> tuple[list[ProfileRecord], int]:
    """Parse a single Instagram export HTML file.

    Handles both Type A (followers) and Type B (following/blocked) formats.
    Returns (records, skipped_count).
    """
    records: list[ProfileRecord] = []
    skipped = 0

    try:
        raw_html = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.error("Cannot read %s: %s", html_path, exc)
        return records, skipped

    soup = BeautifulSoup(raw_html, "lxml")
    main = soup.find("main")
    if main is None:
        logger.warning("No <main> element in %s — skipping", html_path.name)
        return records, skipped

    containers = main.find_all("div", class_=lambda c: c and CSS_ENTRY_CARD in c)
    for container in containers:
        record = _parse_container(container, source_file=html_path.name)
        if record is None:
            skipped += 1
        else:
            records.append(record)

    logger.debug("Parsed %d records (%d skipped) from %s", len(records), skipped, html_path.name)
    return records, skipped


def parse_followers(export_root: Path) -> tuple[list[ProfileRecord], int]:
    """Glob and merge all followers_*.html files from the export root."""
    folder = export_root / CONNECTIONS_SUBPATH
    files = sorted(folder.glob(FOLLOWERS_GLOB))

    if not files:
        logger.warning("No follower files matching '%s' found in %s", FOLLOWERS_GLOB, folder)

    all_records: list[ProfileRecord] = []
    total_skipped = 0
    for f in files:
        records, skipped = parse_export_file(f)
        all_records.extend(records)
        total_skipped += skipped

    return all_records, total_skipped


def parse_single_file(export_root: Path, filename: str) -> tuple[list[ProfileRecord], int]:
    """Parse a single named file within the export's connections folder."""
    path = export_root / CONNECTIONS_SUBPATH / filename
    if not path.exists():
        logger.warning("File not found (optional): %s", path)
        return [], 0
    return parse_export_file(path)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_container(container: Tag, source_file: str) -> Optional[ProfileRecord]:
    """Extract a ProfileRecord from a single entry container div."""
    try:
        # Detect Type B by presence of <h2> with the heading CSS class
        heading = container.find("h2", class_=lambda c: c and CSS_TYPE_B_HEADING in c)
        if heading:
            username = heading.get_text(strip=True)
        else:
            # Type A: username is the anchor text
            link = container.find("a", href=True)
            if not link:
                return None
            username = link.get_text(strip=True)
            if username.startswith("http"):
                username = _username_from_url(username)

        if not username:
            return None

        link = container.find("a", href=True)
        raw_url = link.get("href", "") if link else ""
        profile_url = _normalize_url(raw_url, username)
        timestamp = _extract_timestamp(container)

        return ProfileRecord(
            username=username,
            profile_url=profile_url,
            timestamp=timestamp,
            source_file=source_file,
        )
    except Exception as exc:
        logger.warning("Skipping malformed entry in %s: %s", source_file, exc)
        return None


def _normalize_url(raw_url: str, username: str) -> str:
    """Normalize an Instagram profile URL to canonical form (no _u/ prefix)."""
    if raw_url.startswith(INSTAGRAM_REDIRECT_PREFIX):
        return INSTAGRAM_BASE + username
    if raw_url.startswith(INSTAGRAM_BASE):
        return raw_url.rstrip("/")
    return INSTAGRAM_BASE + username


def _username_from_url(url: str) -> str:
    """Extract bare username from an Instagram URL."""
    path = url.replace(INSTAGRAM_REDIRECT_PREFIX, "").replace(INSTAGRAM_BASE, "")
    return path.strip("/").split("?")[0]


def _extract_timestamp(container: Tag) -> Optional[datetime]:
    """Find and parse the timestamp from an entry container.

    Timestamps are stored in leaf <div> elements (no child tags).
    """
    for div in container.find_all("div"):
        if div.find() is not None:
            continue  # skip non-leaf divs
        text = div.get_text(strip=True)
        if _looks_like_timestamp(text):
            ts = _parse_timestamp(text)
            if ts is not None:
                return ts
    return None


def _looks_like_timestamp(text: str) -> bool:
    """Heuristic: does this text look like an Instagram export timestamp?"""
    if not (16 <= len(text) <= 30):
        return False
    months = {"jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"}
    lower = text.lower()
    return text[:3].lower() in months and ("am" in lower or "pm" in lower)


def _parse_timestamp(text: str) -> Optional[datetime]:
    """Parse a timestamp string, normalizing am/pm to uppercase for strptime."""
    normalized = re.sub(r"\b(am|pm)\b", lambda m: m.group().upper(), text.strip(), flags=re.IGNORECASE)
    try:
        return datetime.strptime(normalized, TIMESTAMP_FORMAT)
    except ValueError:
        return None
