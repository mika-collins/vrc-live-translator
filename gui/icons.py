"""Load icon assets as CTkImage objects for use in CustomTkinter widgets."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
ICO_PATH = ICONS_DIR / "microphone.ico"


def load(file_name: str, size: tuple[int, int]) -> ctk.CTkImage:
    """Load PNG icon from assets/icons as a CTkImage sized for widget use."""
    image = Image.open(ICONS_DIR / file_name)
    return ctk.CTkImage(light_image=image, dark_image=image, size=size)
