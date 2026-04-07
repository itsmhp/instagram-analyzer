"""Lightweight launcher GUI — folder picker → analysis → HTML report."""
from __future__ import annotations

import logging
import os
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
    UI_ACCENT_RED,
)
from core.analyzer import run_analysis
from ui.html_report import generate_report

logger = logging.getLogger(__name__)

_WIN_WIDTH = 520
_WIN_HEIGHT = 400


class Dashboard(ctk.CTk):
    """Minimal launcher: pick export folder → generate HTML report → open."""

    def __init__(self) -> None:
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)
        super().__init__()

        self.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.geometry(f"{_WIN_WIDTH}x{_WIN_HEIGHT}")
        self.resizable(False, False)

        self._report_path: Optional[Path] = None
        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # Logo + title
        ctk.CTkLabel(self, text="📷", font=ctk.CTkFont(size=48)).grid(
            row=0, column=0, pady=(36, 0)
        )
        ctk.CTkLabel(
            self, text=APP_TITLE,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=1, column=0, pady=(4, 2))
        ctk.CTkLabel(
            self, text=f"v{APP_VERSION}  •  100% local & private",
            font=ctk.CTkFont(size=12), text_color="gray",
        ).grid(row=2, column=0, pady=(0, 24))

        # Import button
        self._import_btn = ctk.CTkButton(
            self, text="📁  Select Export Folder",
            width=300, height=48,
            fg_color=UI_ACCENT_BLUE, hover_color="#0a2a50",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_import,
        )
        self._import_btn.grid(row=3, column=0, pady=(0, 12))

        # Progress label
        self._status_var = ctk.StringVar(value="Select your Instagram data export folder to begin.")
        self._status_label = ctk.CTkLabel(
            self, textvariable=self._status_var,
            font=ctk.CTkFont(size=12), text_color="gray",
            wraplength=440,
        )
        self._status_label.grid(row=4, column=0, padx=20, pady=(0, 8))

        # Progress bar (hidden initially)
        self._progress = ctk.CTkProgressBar(self, width=300, mode="indeterminate")
        self._progress.grid(row=5, column=0, pady=(0, 16))
        self._progress.grid_remove()

        # Open report button (hidden initially)
        self._open_btn = ctk.CTkButton(
            self, text="🌐  Open Report in Browser",
            width=300, height=44,
            fg_color="#10a37f", hover_color="#0d8b6a",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_open_report,
        )
        self._open_btn.grid(row=6, column=0, pady=(0, 12))
        self._open_btn.grid_remove()

        # Show in folder button (hidden initially)
        self._folder_btn = ctk.CTkButton(
            self, text="📂  Show File in Folder",
            width=300, height=36,
            fg_color="transparent", hover_color=("#1e1e3e", "#2a2a4e"),
            border_width=1, border_color="#30363d",
            font=ctk.CTkFont(size=12),
            command=self._on_show_folder,
        )
        self._folder_btn.grid(row=7, column=0, pady=(0, 20))
        self._folder_btn.grid_remove()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_import(self) -> None:
        folder = filedialog.askdirectory(title="Select Instagram Export Folder Root")
        if not folder:
            return
        export_path = Path(folder)
        self._import_btn.configure(state="disabled")
        self._open_btn.grid_remove()
        self._folder_btn.grid_remove()
        self._progress.grid()
        self._progress.start()
        self._status_var.set(f"Analyzing {export_path.name} …")
        self.update_idletasks()
        threading.Thread(
            target=self._analysis_worker, args=(export_path,), daemon=True
        ).start()

    def _analysis_worker(self, export_path: Path) -> None:
        try:
            result = run_analysis(export_path)
            report_path = generate_report(result, export_path)
            self.after(0, self._on_success, result, report_path)
        except Exception as exc:
            logger.exception("Analysis failed for %s", export_path)
            self.after(0, self._on_error, str(exc))

    def _on_success(self, result: object, report_path: Path) -> None:
        from core.models import AnalysisResult
        assert isinstance(result, AnalysisResult)
        self._report_path = report_path
        self._import_btn.configure(state="normal")
        self._progress.stop()
        self._progress.grid_remove()

        skipped = f"  ({result.skipped_entries} skipped)" if result.skipped_entries else ""
        self._status_var.set(
            f"✅  Done — {result.follower_count:,} followers · "
            f"{result.following_count:,} following · "
            f"{len(result.not_following_back):,} not following back{skipped}\n"
            f"Report saved to: {report_path.name}"
        )
        self._open_btn.grid()
        self._folder_btn.grid()

    def _on_error(self, message: str) -> None:
        self._import_btn.configure(state="normal")
        self._progress.stop()
        self._progress.grid_remove()
        self._status_var.set(f"❌  {message[:200]}")
        messagebox.showerror("Analysis Failed", message)

    def _on_open_report(self) -> None:
        if self._report_path and self._report_path.exists():
            webbrowser.open(self._report_path.as_uri())

    def _on_show_folder(self) -> None:
        if self._report_path and self._report_path.exists():
            os.startfile(self._report_path.parent)  # type: ignore[attr-defined]
