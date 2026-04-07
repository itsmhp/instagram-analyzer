"""Generate a self-contained HTML dashboard from analysis results."""
from __future__ import annotations

import html
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import APP_TITLE, APP_VERSION
from core.models import AnalysisResult, ProfileRecord

logger = logging.getLogger(__name__)

_OUTPUT_FILENAME = "instagram_report.html"


def generate_report(result: AnalysisResult, output_dir: Path) -> Path:
    """Render analysis results into a standalone HTML file.

    Returns the path to the generated file.
    """
    report_path = output_dir / _OUTPUT_FILENAME
    html_content = _render(result)
    report_path.write_text(html_content, encoding="utf-8")
    logger.info("Report written to %s", report_path)
    return report_path


def _render(r: AnalysisResult) -> str:
    """Build the full HTML document string."""
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    sections = {
        "not_following_back": ("Not Following Back", r.not_following_back, "#e94560"),
        "fans": ("Fans", r.fans, "#0f3460"),
        "mutual": ("Mutual", r.mutual, "#533483"),
        "blocked": ("Blocked", r.blocked, "#6b7280"),
        "recently_unfollowed": ("Recently Unfollowed", r.recently_unfollowed, "#ef4444"),
    }

    tabs_html = ""
    panels_html = ""
    first = True
    for key, (label, records, color) in sections.items():
        count = len(records)
        active_cls = " active" if first else ""
        tabs_html += (
            f'<button class="tab-btn{active_cls}" data-tab="{key}" '
            f'style="--tab-accent:{color}">'
            f'{label} <span class="tab-count">{count:,}</span></button>\n'
        )
        rows = _render_rows(records)
        panels_html += (
            f'<div class="tab-panel{active_cls}" id="panel-{key}">\n'
            f'  <div class="table-wrap">\n'
            f'    <table>\n'
            f'      <thead><tr>'
            f'<th class="col-idx">#</th>'
            f'<th class="col-user">Username</th>'
            f'<th class="col-date">Date</th>'
            f'<th class="col-action">Profile</th>'
            f'</tr></thead>\n'
            f'      <tbody>{rows}</tbody>\n'
            f'    </table>\n'
            f'    {_empty_state(count)}'
            f'  </div>\n'
            f'</div>\n'
        )
        first = False

    ratio_display = f"{r.ratio:.2f}" if r.ratio else "0.00"
    ratio_pct = min(r.follower_count / max(r.following_count, 1) * 100, 100)

    skipped_note = ""
    if r.skipped_entries:
        skipped_note = (
            f'<div class="skipped-note">'
            f'⚠ {r.skipped_entries} malformed entries were skipped during parsing.'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{APP_TITLE} — Report</title>
<style>
{_CSS}
</style>
</head>
<body>

<header class="hero">
  <div class="hero-inner">
    <div class="hero-brand">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="2" width="20" height="20" rx="5"/>
          <circle cx="12" cy="12" r="5"/>
          <circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/>
        </svg>
      </div>
      <div>
        <h1>{APP_TITLE}</h1>
        <p class="hero-sub">v{APP_VERSION} &bull; Generated {now}</p>
      </div>
    </div>
    <div class="hero-search">
      <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input type="text" id="globalSearch" placeholder="Search username…" autocomplete="off" spellcheck="false">
    </div>
  </div>
</header>

<main class="container">

  <!-- Stats Grid -->
  <section class="stats-grid">
    <div class="stat-card" style="--accent:#0f3460">
      <div class="stat-value">{r.follower_count:,}</div>
      <div class="stat-label">Followers</div>
    </div>
    <div class="stat-card" style="--accent:#533483">
      <div class="stat-value">{r.following_count:,}</div>
      <div class="stat-label">Following</div>
    </div>
    <div class="stat-card" style="--accent:#e94560">
      <div class="stat-value">{len(r.not_following_back):,}</div>
      <div class="stat-label">Not Following Back</div>
    </div>
    <div class="stat-card" style="--accent:#10a37f">
      <div class="stat-value">{len(r.fans):,}</div>
      <div class="stat-label">Fans</div>
    </div>
    <div class="stat-card" style="--accent:#f5a623">
      <div class="stat-value">{ratio_display}</div>
      <div class="stat-label">Follow Ratio</div>
      <div class="ratio-bar"><div class="ratio-fill" style="width:{ratio_pct:.1f}%"></div></div>
    </div>
  </section>

  <!-- Visual Breakdown -->
  <section class="chart-section">
    <h2 class="section-title">Breakdown</h2>
    <div class="bar-chart">
      {_bar("Mutual", len(r.mutual), "#533483", max(r.follower_count, r.following_count, 1))}
      {_bar("Not Following Back", len(r.not_following_back), "#e94560", max(r.follower_count, r.following_count, 1))}
      {_bar("Fans", len(r.fans), "#10a37f", max(r.follower_count, r.following_count, 1))}
      {_bar("Blocked", len(r.blocked), "#6b7280", max(r.follower_count, r.following_count, 1))}
      {_bar("Recently Unfollowed", len(r.recently_unfollowed), "#ef4444", max(r.follower_count, r.following_count, 1))}
    </div>
  </section>

  {skipped_note}

  <!-- Tabs -->
  <section class="tabs-section">
    <div class="tabs-header" id="tabsHeader">
      {tabs_html}
    </div>
    <div class="tabs-body">
      {panels_html}
    </div>
  </section>

</main>

<footer class="footer">
  <p>{APP_TITLE} v{APP_VERSION} &mdash; 100% local, zero data leaves your machine.</p>
</footer>

<script>
{_JS}
</script>
</body>
</html>"""


def _render_rows(records: list[ProfileRecord]) -> str:
    if not records:
        return ""
    lines: list[str] = []
    for i, rec in enumerate(records, 1):
        username_esc = html.escape(rec.username)
        url_esc = html.escape(rec.profile_url)
        ts = rec.timestamp.strftime("%d %b %Y") if rec.timestamp else "—"
        lines.append(
            f'<tr data-user="{username_esc.lower()}">'
            f'<td class="col-idx">{i}</td>'
            f'<td class="col-user"><span class="username">@{username_esc}</span></td>'
            f'<td class="col-date">{ts}</td>'
            f'<td class="col-action">'
            f'<a href="{url_esc}" target="_blank" rel="noopener noreferrer" class="profile-link">Open ↗</a>'
            f'</td></tr>\n'
        )
    return "".join(lines)


def _empty_state(count: int) -> str:
    if count > 0:
        return ""
    return '<div class="empty-state">No entries in this category.</div>'


def _bar(label: str, value: int, color: str, max_val: int) -> str:
    pct = (value / max_val * 100) if max_val else 0
    return (
        f'<div class="bar-row">'
        f'<span class="bar-label">{label}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
        f'<span class="bar-value">{value:,}</span>'
        f'</div>'
    )


# ── Embedded CSS ──────────────────────────────────────────────────────────────

_CSS = """\
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #1c2333;
  --bg-card: #1a1f2e;
  --border: #30363d;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --text-muted: #484f58;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 2px 8px rgba(0,0,0,.3);
  --transition: .2s cubic-bezier(.4,0,.2,1);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  min-height: 100vh;
}

/* ── Hero Header ─────────────────────────────────────────────────── */
.hero {
  background: linear-gradient(135deg, #0d1117 0%, #161b22 40%, #1a1a2e 70%, #16213e 100%);
  border-bottom: 1px solid var(--border);
  padding: 2rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}
.hero-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}
.hero-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.logo-icon {
  color: #e94560;
  display: flex;
  align-items: center;
}
.hero h1 {
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -.02em;
  background: linear-gradient(135deg, #e94560, #533483);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-sub {
  font-size: .8rem;
  color: var(--text-secondary);
  margin-top: 2px;
}
.hero-search {
  position: relative;
}
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}
.hero-search input {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 10px 16px 10px 40px;
  color: var(--text-primary);
  font-size: .9rem;
  width: 280px;
  outline: none;
  transition: var(--transition);
}
.hero-search input:focus {
  border-color: #533483;
  box-shadow: 0 0 0 3px rgba(83,52,131,.2);
}
.hero-search input::placeholder { color: var(--text-muted); }

/* ── Container ───────────────────────────────────────────────────── */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem 3rem;
}

/* ── Stats Grid ──────────────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: var(--transition);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent);
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,.3);
  border-color: var(--accent);
}
.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: var(--accent);
  letter-spacing: -.02em;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  font-size: .8rem;
  color: var(--text-secondary);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: .05em;
}
.ratio-bar {
  margin-top: 10px;
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}
.ratio-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width .6s ease;
}

/* ── Chart Section ───────────────────────────────────────────────── */
.chart-section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  margin-bottom: 2rem;
}
.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-bottom: 1rem;
}
.bar-chart { display: flex; flex-direction: column; gap: .6rem; }
.bar-row { display: flex; align-items: center; gap: .75rem; }
.bar-label {
  width: 160px;
  font-size: .85rem;
  color: var(--text-secondary);
  text-align: right;
  flex-shrink: 0;
}
.bar-track {
  flex: 1;
  height: 22px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width .8s cubic-bezier(.4,0,.2,1);
  min-width: 2px;
}
.bar-value {
  width: 60px;
  font-size: .85rem;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
.tabs-section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.tabs-header {
  display: flex;
  overflow-x: auto;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
  padding: 0 .5rem;
  gap: 2px;
  scrollbar-width: thin;
}
.tab-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: .85rem 1.2rem;
  font-size: .85rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: .5rem;
  font-family: inherit;
}
.tab-btn:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,.03);
}
.tab-btn.active {
  color: var(--text-primary);
  border-bottom-color: var(--tab-accent);
}
.tab-count {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: .75rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-variant-numeric: tabular-nums;
}
.tab-btn.active .tab-count {
  background: var(--tab-accent);
  color: #fff;
}
.tabs-body { padding: 0; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* ── Table ───────────────────────────────────────────────────────── */
.table-wrap { overflow-x: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: .9rem;
}
thead {
  position: sticky;
  top: 0;
  z-index: 2;
}
th {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: .75rem;
  text-transform: uppercase;
  letter-spacing: .06em;
  padding: .75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
td {
  padding: .65rem 1rem;
  border-bottom: 1px solid rgba(48,54,61,.5);
  vertical-align: middle;
}
tr { transition: background var(--transition); }
tbody tr:hover { background: rgba(83,52,131,.08); }
.col-idx { width: 50px; color: var(--text-muted); text-align: right; }
.col-user { min-width: 180px; }
.col-date { width: 120px; color: var(--text-secondary); }
.col-action { width: 80px; text-align: center; }
.username {
  font-weight: 600;
  color: var(--text-primary);
}
.profile-link {
  color: #58a6ff;
  text-decoration: none;
  font-size: .82rem;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
  transition: var(--transition);
  border: 1px solid transparent;
}
.profile-link:hover {
  background: rgba(88,166,255,.1);
  border-color: rgba(88,166,255,.2);
}

/* ── Misc ────────────────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
  font-size: .95rem;
}
.skipped-note {
  background: rgba(245,166,35,.08);
  border: 1px solid rgba(245,166,35,.25);
  border-radius: var(--radius-sm);
  padding: .75rem 1rem;
  font-size: .85rem;
  color: #f5a623;
  margin-bottom: 1.5rem;
}
.no-results {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: .9rem;
  display: none;
}
.tab-panel .no-results-msg {
  display: none;
  text-align: center;
  padding: 2.5rem 1rem;
  color: var(--text-muted);
  font-size: .9rem;
}

/* ── Footer ──────────────────────────────────────────────────────── */
.footer {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: .8rem;
  border-top: 1px solid var(--border);
}

/* ── Responsive ──────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .bar-label { width: 100px; font-size: .78rem; }
  .hero-search input { width: 200px; }
  .hero-inner { flex-direction: column; align-items: stretch; }
  .hero-brand { justify-content: center; }
  .hero-search { width: 100%; }
  .hero-search input { width: 100%; }
}
@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .stat-value { font-size: 1.5rem; }
  .tab-btn { padding: .7rem .8rem; font-size: .8rem; }
}

/* ── Animations ──────────────────────────────────────────────────── */
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.stat-card { animation: fadeIn .4s ease both; }
.stat-card:nth-child(2) { animation-delay: .05s; }
.stat-card:nth-child(3) { animation-delay: .1s; }
.stat-card:nth-child(4) { animation-delay: .15s; }
.stat-card:nth-child(5) { animation-delay: .2s; }
.bar-row { animation: fadeIn .4s ease both; }
.bar-row:nth-child(2) { animation-delay: .05s; }
.bar-row:nth-child(3) { animation-delay: .1s; }
.bar-row:nth-child(4) { animation-delay: .15s; }
.bar-row:nth-child(5) { animation-delay: .2s; }
"""

# ── Embedded JavaScript ───────────────────────────────────────────────────────

_JS = """\
(function() {
  // Tab switching
  const btns = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-panel');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
      applySearch();
    });
  });

  // Global search
  const searchInput = document.getElementById('globalSearch');
  searchInput.addEventListener('input', applySearch);

  function applySearch() {
    const q = searchInput.value.trim().toLowerCase();
    const activePanel = document.querySelector('.tab-panel.active');
    if (!activePanel) return;
    const rows = activePanel.querySelectorAll('tbody tr');
    let visible = 0;
    rows.forEach((row, idx) => {
      const user = row.getAttribute('data-user') || '';
      const show = !q || user.includes(q);
      row.style.display = show ? '' : 'none';
      if (show) {
        visible++;
        // Re-number visible rows
        const idxCell = row.querySelector('.col-idx');
        if (idxCell) idxCell.textContent = visible;
      }
    });
    // Show/hide no-results message
    let msg = activePanel.querySelector('.no-results-msg');
    if (!msg) {
      msg = document.createElement('div');
      msg.className = 'no-results-msg';
      msg.textContent = 'No usernames match your search.';
      activePanel.querySelector('.table-wrap').appendChild(msg);
    }
    msg.style.display = (visible === 0 && q) ? 'block' : 'none';
  }

  // Keyboard shortcut: focus search on '/'
  document.addEventListener('keydown', e => {
    if (e.key === '/' && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === 'Escape') {
      searchInput.blur();
      searchInput.value = '';
      applySearch();
    }
  });
})();
"""
