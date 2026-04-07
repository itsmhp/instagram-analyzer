from __future__ import annotations

from pathlib import Path

# ── Application ───────────────────────────────────────────────────────────────
APP_TITLE = "Instagram Analyzer"
APP_VERSION = "0.2.0"
WINDOW_GEOMETRY = "1200x720"
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"

# ── Export Folder Layout ──────────────────────────────────────────────────────
CONNECTIONS_SUBPATH: Path = Path("connections") / "followers_and_following"
FOLLOWERS_GLOB = "followers_*.html"
FOLLOWING_FILE = "following.html"
BLOCKED_FILE = "blocked_profiles.html"
UNFOLLOWED_FILE = "recently_unfollowed_profiles.html"
PENDING_FILE = "pending_follow_requests.html"

# ── HTML Selectors (per §2.3 — never hardcode inline) ─────────────────────────
CSS_ENTRY_CARD = "_a6-g"        # Key class shared by all entry containers
CSS_TYPE_B_HEADING = "_a6-h"    # Type-B: <h2> class that contains the username
CSS_CONTENT_WRAPPER = "_a6-p"   # Inner content wrapper div

# ── URL Constants ─────────────────────────────────────────────────────────────
INSTAGRAM_BASE = "https://www.instagram.com/"
INSTAGRAM_REDIRECT_PREFIX = "https://www.instagram.com/_u/"

# ── Timestamp ─────────────────────────────────────────────────────────────────
# Format: "Apr 05, 2026 8:16 PM"  (normalized to uppercase AM/PM before parse)
TIMESTAMP_FORMAT = "%b %d, %Y %I:%M %p"

# ── UI Palette ────────────────────────────────────────────────────────────────
UI_ACCENT_RED = "#e94560"
UI_ACCENT_BLUE = "#0f3460"
UI_ACCENT_PURPLE = "#533483"
UI_ACCENT_GREEN = "#10a37f"
UI_ACCENT_ORANGE = "#f5a623"
UI_BG_DARK = "#1a1a2e"
UI_BG_CARD = "#16213e"
UI_SIDEBAR_WIDTH = 210
MAX_DISPLAY_ROWS = 2000
