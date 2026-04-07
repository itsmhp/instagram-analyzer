from __future__ import annotations

import logging
from pathlib import Path

from config import BLOCKED_FILE, CONNECTIONS_SUBPATH, FOLLOWING_FILE, UNFOLLOWED_FILE
from core import parser
from core.models import AnalysisResult, ProfileRecord

logger = logging.getLogger(__name__)


def run_analysis(export_root: Path) -> AnalysisResult:
    """Full analysis pipeline: parse the export and compute all diffs.

    Raises ValueError if the export folder structure is invalid.
    """
    _validate_export_root(export_root)

    result = AnalysisResult()
    total_skipped = 0

    followers, skipped = parser.parse_followers(export_root)
    result.followers = followers
    total_skipped += skipped

    following, skipped = parser.parse_single_file(export_root, FOLLOWING_FILE)
    result.following = following
    total_skipped += skipped

    blocked, skipped = parser.parse_single_file(export_root, BLOCKED_FILE)
    result.blocked = blocked
    total_skipped += skipped

    unfollowed, skipped = parser.parse_single_file(export_root, UNFOLLOWED_FILE)
    result.recently_unfollowed = unfollowed
    total_skipped += skipped

    result.skipped_entries = total_skipped

    # Set-difference computations (case-insensitive)
    followers_set = {r.username.lower() for r in followers}
    following_set = {r.username.lower() for r in following}

    result.not_following_back = [
        r for r in following if r.username.lower() not in followers_set
    ]
    result.fans = [
        r for r in followers if r.username.lower() not in following_set
    ]
    result.mutual = [
        r for r in followers if r.username.lower() in following_set
    ]

    logger.info(
        "Analysis complete — followers: %d, following: %d, "
        "not_following_back: %d, fans: %d, mutual: %d",
        len(followers), len(following),
        len(result.not_following_back), len(result.fans), len(result.mutual),
    )
    return result


def _validate_export_root(export_root: Path) -> None:
    """Raise ValueError if the folder does not look like an Instagram export."""
    connections_dir = export_root / CONNECTIONS_SUBPATH
    if not connections_dir.is_dir():
        raise ValueError(
            f"Expected directory not found:\n  {connections_dir}\n\n"
            "Did you select the correct export folder root?\n"
            "It should contain a 'connections/followers_and_following/' subfolder."
        )
