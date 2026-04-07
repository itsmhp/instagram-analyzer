"""Parser unit tests — uses synthetic (fictitious) usernames only. §4.5."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from core.models import ProfileRecord
from core.parser import _parse_container, _looks_like_timestamp, _parse_timestamp, parse_export_file

# ── Fixtures ──────────────────────────────────────────────────────────────────

TYPE_A_HTML = """
<div class="pam _3-95 _2ph- _a6-g uiBoxWhite noborder">
  <div class="_a6-p">
    <div>
      <div><a target="_blank" href="https://www.instagram.com/synth_user_a">synth_user_a</a></div>
      <div>Apr 06, 2026 9:18 pm</div>
    </div>
  </div>
</div>
"""

TYPE_B_HTML = """
<div class="pam _3-95 _2ph- _a6-g uiBoxWhite noborder">
  <h2 class="_3-95 _2pim _a6-h _a6-i">synth_user_b</h2>
  <div class="_a6-p">
    <div>
      <div><a target="_blank" href="https://www.instagram.com/_u/synth_user_b">https://www.instagram.com/_u/synth_user_b</a></div>
      <div>Apr 05, 2026 8:16 pm</div>
    </div>
  </div>
</div>
"""

EMPTY_CARD_HTML = '<div class="pam _3-95 _2ph- _a6-g uiBoxWhite noborder"></div>'


def _container(html: str):
    soup = BeautifulSoup(html, "lxml")
    return soup.find("div", class_=lambda c: c and "_a6-g" in c)


# ── Type A tests ──────────────────────────────────────────────────────────────

def test_type_a_username():
    record = _parse_container(_container(TYPE_A_HTML), source_file="followers_1.html")
    assert record is not None
    assert record.username == "synth_user_a"


def test_type_a_url_canonical():
    record = _parse_container(_container(TYPE_A_HTML), source_file="followers_1.html")
    assert record.profile_url == "https://www.instagram.com/synth_user_a"


def test_type_a_timestamp():
    record = _parse_container(_container(TYPE_A_HTML), source_file="followers_1.html")
    # 9:18 PM = 21:18 in 24-hour time
    assert record.timestamp == datetime(2026, 4, 6, 21, 18)


def test_type_a_source_file():
    record = _parse_container(_container(TYPE_A_HTML), source_file="followers_1.html")
    assert record.source_file == "followers_1.html"


# ── Type B tests ──────────────────────────────────────────────────────────────

def test_type_b_username_from_heading():
    record = _parse_container(_container(TYPE_B_HTML), source_file="following.html")
    assert record is not None
    assert record.username == "synth_user_b"


def test_type_b_url_normalized():
    """_u/ redirect prefix must be stripped from profile URL."""
    record = _parse_container(_container(TYPE_B_HTML), source_file="following.html")
    assert record.profile_url == "https://www.instagram.com/synth_user_b"


def test_type_b_timestamp():
    record = _parse_container(_container(TYPE_B_HTML), source_file="following.html")
    # 8:16 PM = 20:16
    assert record.timestamp == datetime(2026, 4, 5, 20, 16)


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_container_returns_none():
    record = _parse_container(_container(EMPTY_CARD_HTML), source_file="test.html")
    assert record is None


def test_looks_like_timestamp_valid():
    assert _looks_like_timestamp("Apr 06, 2026 9:18 pm") is True
    assert _looks_like_timestamp("Jan 01, 2025 12:00 am") is True


def test_looks_like_timestamp_rejects_username():
    assert _looks_like_timestamp("synth_user_a") is False
    assert _looks_like_timestamp("") is False


def test_parse_timestamp_lowercase_pm():
    """Lowercase 'pm' must be handled correctly (§2.3)."""
    ts = _parse_timestamp("Apr 05, 2026 8:16 pm")
    assert ts == datetime(2026, 4, 5, 20, 16)


def test_parse_timestamp_lowercase_am():
    ts = _parse_timestamp("Jan 01, 2025 12:00 am")
    assert ts == datetime(2025, 1, 1, 0, 0)


def test_parse_timestamp_invalid_returns_none():
    assert _parse_timestamp("not a timestamp") is None


# ── Integration: parse_export_file ────────────────────────────────────────────

def test_parse_export_file_type_a(tmp_path: Path):
    content = f"<html><body><main>{TYPE_A_HTML}</main></body></html>"
    f = tmp_path / "followers_1.html"
    f.write_text(content, encoding="utf-8")
    records, skipped = parse_export_file(f)
    assert len(records) == 1
    assert skipped == 0
    assert records[0].username == "synth_user_a"


def test_parse_export_file_type_b(tmp_path: Path):
    content = f"<html><body><main>{TYPE_B_HTML}</main></body></html>"
    f = tmp_path / "following.html"
    f.write_text(content, encoding="utf-8")
    records, skipped = parse_export_file(f)
    assert len(records) == 1
    assert records[0].username == "synth_user_b"


def test_parse_export_file_no_main(tmp_path: Path):
    """File without <main> returns empty list (no crash)."""
    f = tmp_path / "broken.html"
    f.write_text("<html><body></body></html>", encoding="utf-8")
    records, skipped = parse_export_file(f)
    assert records == []
    assert skipped == 0


def test_parse_export_file_missing_file(tmp_path: Path):
    """Non-existent file returns empty list (no crash)."""
    records, skipped = parse_export_file(tmp_path / "ghost.html")
    assert records == []
