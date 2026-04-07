"""Analyzer unit tests — uses synthetic (fictitious) usernames only. §4.5."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.analyzer import run_analysis, _validate_export_root
from core.models import ProfileRecord


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rec(username: str) -> ProfileRecord:
    return ProfileRecord(
        username=username,
        profile_url=f"https://www.instagram.com/{username}",
        timestamp=datetime(2026, 1, 1),
        source_file="test",
    )


def _mock_parser(followers, following, blocked=None, unfollowed=None):
    """Patch core.analyzer.parser with predetermined return values."""
    mock = MagicMock()
    mock.parse_followers.return_value = (followers, 0)
    mock.parse_single_file.side_effect = [
        (following, 0),
        (blocked or [], 0),
        (unfollowed or [], 0),
    ]
    return mock


# ── Diff algorithm ────────────────────────────────────────────────────────────

def test_not_following_back_identified(tmp_path):
    followers = [_rec("synth_alpha"), _rec("synth_beta")]
    following = [_rec("synth_alpha"), _rec("synth_gamma")]

    with patch("core.analyzer.parser", _mock_parser(followers, following)):
        _make_connections_dir(tmp_path)
        result = run_analysis(tmp_path)

    assert len(result.not_following_back) == 1
    assert result.not_following_back[0].username == "synth_gamma"


def test_fans_identified(tmp_path):
    followers = [_rec("synth_alpha"), _rec("synth_beta")]
    following = [_rec("synth_alpha")]

    with patch("core.analyzer.parser", _mock_parser(followers, following)):
        _make_connections_dir(tmp_path)
        result = run_analysis(tmp_path)

    assert len(result.fans) == 1
    assert result.fans[0].username == "synth_beta"


def test_mutual_identified(tmp_path):
    shared = [_rec("synth_alpha"), _rec("synth_beta")]

    with patch("core.analyzer.parser", _mock_parser(shared, shared)):
        _make_connections_dir(tmp_path)
        result = run_analysis(tmp_path)

    assert len(result.mutual) == 2
    assert len(result.not_following_back) == 0
    assert len(result.fans) == 0


def test_case_insensitive_matching(tmp_path):
    """Username comparisons must be case-insensitive (§2.3)."""
    followers = [_rec("Synth_Alpha")]
    following = [_rec("synth_alpha")]

    with patch("core.analyzer.parser", _mock_parser(followers, following)):
        _make_connections_dir(tmp_path)
        result = run_analysis(tmp_path)

    assert len(result.mutual) == 1
    assert len(result.not_following_back) == 0


def test_empty_inputs_produce_empty_results(tmp_path):
    with patch("core.analyzer.parser", _mock_parser([], [])):
        _make_connections_dir(tmp_path)
        result = run_analysis(tmp_path)

    assert result.follower_count == 0
    assert result.following_count == 0
    assert result.not_following_back == []
    assert result.fans == []
    assert result.mutual == []


# ── Stats ─────────────────────────────────────────────────────────────────────

def test_ratio_calculation(tmp_path):
    followers = [_rec(f"f_{i}") for i in range(3)]
    following = [_rec(f"g_{i}") for i in range(6)]

    with patch("core.analyzer.parser", _mock_parser(followers, following)):
        _make_connections_dir(tmp_path)
        result = run_analysis(tmp_path)

    assert result.ratio == 0.5


def test_ratio_zero_following(tmp_path):
    with patch("core.analyzer.parser", _mock_parser([_rec("synth_x")], [])):
        _make_connections_dir(tmp_path)
        result = run_analysis(tmp_path)

    assert result.ratio == 0.0


# ── Validation ────────────────────────────────────────────────────────────────

def test_invalid_export_root_raises(tmp_path):
    """run_analysis must raise ValueError for folders missing the expected structure."""
    with pytest.raises(ValueError, match="connections"):
        run_analysis(tmp_path)


# ── Utilities ─────────────────────────────────────────────────────────────────

def _make_connections_dir(base: Path) -> Path:
    """Create the expected connections/followers_and_following/ dir structure."""
    from config import CONNECTIONS_SUBPATH
    d = base / CONNECTIONS_SUBPATH
    d.mkdir(parents=True, exist_ok=True)
    return d
