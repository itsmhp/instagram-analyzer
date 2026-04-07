from __future__ import annotations

import logging
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from config import (
    APP_TITLE,
    APP_VERSION,
    APPEARANCE_MODE,
    COLOR_THEME,
    UI_ACCENT_BLUE,
    UI_ACCENT_GREEN,
    UI_ACCENT_ORANGE,
    UI_ACCENT_PURPLE,
    UI_ACCENT_RED,
    UI_SIDEBAR_WIDTH,
    WINDOW_GEOMETRY,
)
from core.analyzer import run_analysis
from core.models import AnalysisResult, ProfileRecord
from ui.widgets import ProfileListFrame, StatCard

logger = logging.getLogger(__name__)

_NAV_SECTIONS: list[tuple[str, str]] = [
    ("Not Following Back", UI_ACCENT_RED),
    ("Fans", UI_ACCENT_BLUE),
    ("Mutual", UI_ACCENT_PURPLE),
    ("Blocked", "#888888"),
    ("Recently Unfollowed", "#666666"),
]


class Dashboard(ctk.CTk):
    """Main application window for Instagram Analyzer."""

    def __init__(self) -> None:
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)
        super().__init__()

        self.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.geometry(WINDOW_GEOMETRY)
        self.minsize(900, 580)

        self._result: Optional[AnalysisResult] = None
        self._active_section = "Not Following Back"

        self._build_layout()
        self._show_section(self._active_section)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self._build_sidebar()
        self._build_content()
        self._build_statusbar()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=UI_SIDEBAR_WIDTH, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="📷", font=ctk.CTkFont(size=36)).pack(pady=(28, 0))
        ctk.CTkLabel(
            sidebar, text=APP_TITLE, font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(4, 24))

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for section, _ in _NAV_SECTIONS:
            btn = ctk.CTkButton(
                sidebar, text=section,
                width=UI_SIDEBAR_WIDTH - 20, height=36, anchor="w",
                fg_color="transparent", hover_color=("#1e1e3e", "#2a2a4e"),
                font=ctk.CTkFont(size=12),
                command=lambda s=section: self._show_section(s),  # type: ignore[misc]
            )
            btn.pack(padx=10, pady=2)
            self._nav_buttons[section] = btn

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(expand=True, fill="y")

        self._import_btn = ctk.CTkButton(
            sidebar, text="📁  Import Export",
            width=UI_SIDEBAR_WIDTH - 20, height=40,
            fg_color=UI_ACCENT_BLUE, hover_color="#0a2a50",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_import,
        )
        self._import_btn.pack(padx=10, pady=(0, 20))

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=16, pady=(16, 4))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        # ── Stats row ──────────────────────────────────────────────────────
        stats = ctk.CTkFrame(content, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for i in range(5):
            stats.grid_columnconfigure(i, weight=1)

        self._stat_followers = StatCard(stats, "Followers", "—", UI_ACCENT_BLUE)
        self._stat_followers.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._stat_following = StatCard(stats, "Following", "—", UI_ACCENT_PURPLE)
        self._stat_following.grid(row=0, column=1, padx=4, sticky="ew")

        self._stat_not_back = StatCard(stats, "Not Following Back", "—", UI_ACCENT_RED)
        self._stat_not_back.grid(row=0, column=2, padx=4, sticky="ew")

        self._stat_fans = StatCard(stats, "Fans", "—", UI_ACCENT_GREEN)
        self._stat_fans.grid(row=0, column=3, padx=4, sticky="ew")

        self._stat_ratio = StatCard(stats, "Follow Ratio", "—", UI_ACCENT_ORANGE)
        self._stat_ratio.grid(row=0, column=4, padx=(4, 0), sticky="ew")

        # ── Section header + search ────────────────────────────────────────
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        header.grid_columnconfigure(0, weight=1)

        self._section_label = ctk.CTkLabel(
            header, text="Not Following Back",
            font=ctk.CTkFont(size=18, weight="bold"), anchor="w",
        )
        self._section_label.grid(row=0, column=0, sticky="w")

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(
            header, placeholder_text="🔍  Search username...",
            width=230, textvariable=self._search_var,
        ).grid(row=0, column=1, sticky="e")

        # ── Profile list ───────────────────────────────────────────────────
        self._profile_list = ProfileListFrame(
            content, on_open=webbrowser.open, fg_color="transparent",
        )
        self._profile_list.grid(row=2, column=0, sticky="nsew")

    def _build_statusbar(self) -> None:
        self._status_var = ctk.StringVar(
            value="Ready — select 📁 Import Export to load your Instagram data."
        )
        ctk.CTkLabel(
            self, textvariable=self._status_var, height=26, anchor="w",
            font=ctk.CTkFont(size=11), text_color="gray",
        ).grid(row=1, column=1, sticky="ew", padx=16, pady=(0, 6))

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_import(self) -> None:
        folder = filedialog.askdirectory(title="Select Instagram Export Folder Root")
        if not folder:
            return
        export_path = Path(folder)
        self._import_btn.configure(state="disabled")
        self._status_var.set(f"Analyzing  {export_path.name} …")
        self.update_idletasks()
        threading.Thread(
            target=self._analysis_worker, args=(export_path,), daemon=True
        ).start()

    def _analysis_worker(self, export_path: Path) -> None:
        try:
            result = run_analysis(export_path)
            self.after(0, self._on_success, result)
        except Exception as exc:
            logger.exception("Analysis failed for %s", export_path)
            self.after(0, self._on_error, str(exc))

    def _on_success(self, result: AnalysisResult) -> None:
        self._result = result
        self._import_btn.configure(state="normal")
        self._refresh_stats()
        self._show_section(self._active_section)
        skipped = f"  ({result.skipped_entries} skipped)" if result.skipped_entries else ""
        self._status_var.set(
            f"Loaded — {result.follower_count:,} followers · "
            f"{result.following_count:,} following · "
            f"{len(result.not_following_back):,} not following back{skipped}"
        )

    def _on_error(self, message: str) -> None:
        self._import_btn.configure(state="normal")
        self._status_var.set(f"Error: {message[:120]}")
        messagebox.showerror("Analysis Failed", message)

    def _show_section(self, section: str) -> None:
        self._active_section = section
        self._section_label.configure(text=section)
        for name, btn in self._nav_buttons.items():
            btn.configure(fg_color="#1e2a4a" if name == section else "transparent")
        query = self._search_var.get() if hasattr(self, "_search_var") else ""
        self._profile_list.populate(self._get_records(section), query=query)

    def _get_records(self, section: str) -> list[ProfileRecord]:
        if self._result is None:
            return []
        return {
            "Not Following Back": self._result.not_following_back,
            "Fans": self._result.fans,
            "Mutual": self._result.mutual,
            "Blocked": self._result.blocked,
            "Recently Unfollowed": self._result.recently_unfollowed,
        }.get(section, [])

    def _refresh_stats(self) -> None:
        if self._result is None:
            return
        self._stat_followers.update_value(f"{self._result.follower_count:,}")
        self._stat_following.update_value(f"{self._result.following_count:,}")
        self._stat_not_back.update_value(f"{len(self._result.not_following_back):,}")
        self._stat_fans.update_value(f"{len(self._result.fans):,}")
        self._stat_ratio.update_value(str(self._result.ratio))

    def _on_search(self, *_: object) -> None:
        self._show_section(self._active_section)
