"""VRChat live speech translator - entry point."""

from __future__ import annotations

import customtkinter as ctk

from gui import LiveTranslatorApp


def main() -> None:
    """Launch the desktop application."""
    root = ctk.CTk()
    LiveTranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
