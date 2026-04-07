"""HTML report generator tests — synthetic data only (§4.5)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from core.models import AnalysisResult, ProfileRecord
from ui.html_report import generate_report


def _rec(username: str) -> ProfileRecord:
    return ProfileRecord(
        username=username,
        profile_url=f"https://www.instagram.com/{username}",
        timestamp=datetime(2026, 1, 1),
        source_file="test",
    )


def _sample_result() -> AnalysisResult:
    r = AnalysisResult()
    r.followers = [_rec("synth_alpha"), _rec("synth_beta"), _rec("synth_gamma")]
    r.following = [_rec("synth_alpha"), _rec("synth_delta")]
    r.not_following_back = [_rec("synth_delta")]
    r.fans = [_rec("synth_beta"), _rec("synth_gamma")]
    r.mutual = [_rec("synth_alpha")]
    r.blocked = [_rec("synth_blocked")]
    r.recently_unfollowed = []
    r.skipped_entries = 2
    return r


def test_generate_report_creates_file(tmp_path: Path):
    result = _sample_result()
    report = generate_report(result, tmp_path)
    assert report.exists()
    assert report.name == "instagram_report.html"


def test_report_contains_stats(tmp_path: Path):
    result = _sample_result()
    report = generate_report(result, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert "3" in content  # follower count
    assert "2" in content  # following count
    assert "Instagram Analyzer" in content


def test_report_contains_usernames(tmp_path: Path):
    result = _sample_result()
    report = generate_report(result, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert "synth_delta" in content
    assert "synth_alpha" in content


def test_report_contains_tab_sections(tmp_path: Path):
    result = _sample_result()
    report = generate_report(result, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert "Not Following Back" in content
    assert "Fans" in content
    assert "Mutual" in content
    assert "Blocked" in content
    assert "Recently Unfollowed" in content


def test_report_contains_skipped_warning(tmp_path: Path):
    result = _sample_result()
    report = generate_report(result, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert "2 malformed entries were skipped" in content


def test_report_no_skipped_warning_when_zero(tmp_path: Path):
    result = _sample_result()
    result.skipped_entries = 0
    report = generate_report(result, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert "malformed entries" not in content


def test_report_valid_html(tmp_path: Path):
    result = _sample_result()
    report = generate_report(result, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert content.startswith("<!DOCTYPE html>")
    assert "</html>" in content


def test_report_empty_result(tmp_path: Path):
    result = AnalysisResult()
    report = generate_report(result, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert report.exists()
    assert "No entries in this category" in content


def test_report_escapes_html_in_username(tmp_path: Path):
    """XSS prevention: usernames with special chars must be escaped."""
    r = AnalysisResult()
    malicious = _rec('<script>alert("xss")</script>')
    r.followers = [malicious]
    r.following = []
    r.fans = [malicious]
    report = generate_report(r, tmp_path)
    content = report.read_text(encoding="utf-8")
    assert '<script>alert("xss")</script>' not in content
    assert "&lt;script&gt;" in content
