"""VRChat live speech translator - entry point."""

from __future__ import annotations

import tkinter as tk

from gui import LiveTranslatorApp


def main() -> None:
    """Launch the desktop application."""
    root = tk.Tk()
    LiveTranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
