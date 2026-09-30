"""Color palette and appearance settings for the CustomTkinter UI."""

from __future__ import annotations

import customtkinter as ctk

BG_PRIMARY = "#040d10"
BG_PANEL = "#06171b"

CONTROL_BG = "#07242b"
CONTROL_BG_HOVER = "#0c3641"
CONTROL_BORDER = "#053c48"

TEXT_PRIMARY = "#eaf7fb"
TEXT_MUTED = "#4d7d8a"

ACCENT = "#6ae3f9"
ACCENT_HOVER = "#9aeefc"

PRIMARY_ACTION_BG = "#3b82f6"
PRIMARY_ACTION_HOVER = "#2563eb"
PRIMARY_ACTION_TEXT = "#ffffff"

STOP_ACTION_BG = "#dc2626"
STOP_ACTION_HOVER = "#ef4444"
STOP_ACTION_TEXT = "#ffffff"

RADIUS_CONTROL = 8
RADIUS_PANEL = 10

BORDER_WIDTH = 2

FONT_FAMILY = "Segoe UI"
FONT_SIZE_TITLE = 22
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


def control_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SECTION, weight="bold")


def body_font() -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY)


def mono_font() -> ctk.CTkFont:
    return ctk.CTkFont(family="Consolas", size=FONT_SIZE_BODY)
