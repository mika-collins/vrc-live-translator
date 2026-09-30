"""Color palette and appearance settings for the CustomTkinter UI."""

from __future__ import annotations

import customtkinter as ctk

BG_PRIMARY = "#121212"
BG_PANEL = "#1c1c1e"
BG_CONTROL = "#232326"
TEXT_PRIMARY = "#f5f5f7"
TEXT_MUTED = "#9a9a9e"
ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
BORDER = "#2a2a2d"

FONT_FAMILY = "Segoe UI"
FONT_SIZE_TITLE = 16
FONT_SIZE_SECTION = 13
FONT_SIZE_BODY = 12


def apply() -> None:
    """Configure CustomTkinter's global appearance before any widgets are built."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def title_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_TITLE, weight="bold")


def section_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SECTION, weight="bold")


def body_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY)


def mono_font() -> ctk.CTkFont:
    return ctk.CTkFont(family="Consolas", size=FONT_SIZE_BODY)
