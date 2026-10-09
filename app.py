"""VRChat live speech translator - entry point."""

from __future__ import annotations

import ctypes

import customtkinter as ctk

from gui import LiveTranslatorApp

APP_USER_MODEL_ID = "VRCTranslator"


def main() -> None:
    """Launch the desktop application."""
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    root = ctk.CTk()
    LiveTranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
