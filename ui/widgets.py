from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

import customtkinter as ctk

from config import (
    MAX_DISPLAY_ROWS,
    UI_ACCENT_BLUE,
    UI_ACCENT_GREEN,
    UI_ACCENT_ORANGE,
    UI_ACCENT_PURPLE,
    UI_ACCENT_RED,
    UI_BG_CARD,
)
from core.models import ProfileRecord


class StatCard(ctk.CTkFrame):
    """Card widget displaying a single labelled metric."""

    def __init__(
        self,
        master: Any,
        label: str,
        value: str,
        accent_color: str = UI_ACCENT_BLUE,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, corner_radius=10, fg_color=UI_BG_CARD, **kwargs)
        ctk.CTkLabel(
            self, text=label, font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(pady=(12, 0), padx=12)
        self._value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=accent_color,
        )
        self._value_label.pack(pady=(2, 12), padx=12)

    def update_value(self, value: str) -> None:
        self._value_label.configure(text=value)


class ProfileListFrame(ctk.CTkScrollableFrame):
    """Scrollable, filterable list of ProfileRecord entries."""

    def __init__(
        self,
        master: Any,
        on_open: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_open = on_open
        self._rows: list[Any] = []

    def populate(self, records: list[ProfileRecord], *, query: str = "") -> None:
        for widget in self._rows:
            widget.destroy()
        self._rows.clear()

        filtered = [r for r in records if not query or query.lower() in r.username.lower()]

        if not filtered:
            lbl = ctk.CTkLabel(
                self,
                text="No results match your search." if query else "No data loaded.",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            )
            lbl.pack(pady=40)
            self._rows.append(lbl)
            return

        truncated = len(filtered) > MAX_DISPLAY_ROWS
        display = filtered[:MAX_DISPLAY_ROWS]

        for i, record in enumerate(display):
            row = self._build_row(i, record)
            self._rows.append(row)

        if truncated:
            note = ctk.CTkLabel(
                self,
                text=f"Showing first {MAX_DISPLAY_ROWS:,} of {len(filtered):,} results — use search to filter.",
                text_color="gray",
                font=ctk.CTkFont(size=11),
            )
            note.pack(pady=(4, 8))
            self._rows.append(note)

    def _build_row(self, index: int, record: ProfileRecord) -> ctk.CTkFrame:
        row_color = "#1e1e2e" if index % 2 == 0 else "#16213e"
        row = ctk.CTkFrame(self, fg_color=row_color, corner_radius=4)
        row.pack(fill="x", padx=4, pady=1)
        row.grid_columnconfigure(1, weight=1)

        # Index number
        ctk.CTkLabel(
            row, text=f"{index + 1}.", width=44,
            font=ctk.CTkFont(size=11), text_color="gray", anchor="e",
        ).grid(row=0, column=0, padx=(8, 0), pady=8)

        # Username
        ctk.CTkLabel(
            row, text=record.username,
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        # Timestamp
        if record.timestamp:
            ctk.CTkLabel(
                row, text=record.timestamp.strftime("%d %b %Y"),
                font=ctk.CTkFont(size=11), text_color="gray", width=90,
            ).grid(row=0, column=2, padx=4)

        # Open profile button (user-initiated network action)
        if self._on_open:
            ctk.CTkButton(
                row, text="Open", width=60, height=26,
                font=ctk.CTkFont(size=11),
                command=lambda url=record.profile_url: self._on_open(url),  # type: ignore[misc]
            ).grid(row=0, column=3, padx=(4, 8))

        return row

    def clear(self) -> None:
        self.populate([])
