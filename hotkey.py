"""Global desktop hotkey: listen for a toggle key and support re-binding it."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

try:
    from pynput import keyboard as pynput_keyboard
except ImportError:
    pynput_keyboard = None

if TYPE_CHECKING:
    from pynput.keyboard import Listener

AVAILABLE = pynput_keyboard is not None
DEFAULT_HOTKEY = pynput_keyboard.Key.f9 if pynput_keyboard else None


def format_key(key) -> str:
    """Render a pynput key object as a short human-readable label."""
    if key is None:
        return "(none)"
    if pynput_keyboard is not None and isinstance(key, pynput_keyboard.KeyCode):
        return (key.char or str(key.vk)).upper()
    return str(key).replace("Key.", "").upper()


class HotkeyManager:
    """Own the pynput listener, the current hotkey, and rebind mode.

    Press/release detection runs on the pynput listener thread; callbacks are
    used to hand events off rather than mutating shared state from that thread.
    """

    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_captured: Callable[[object], None],
    ) -> None:
        self.hotkey = DEFAULT_HOTKEY
        self._on_toggle = on_toggle
        self._on_captured = on_captured
        self._listener: Listener | None = None
        self._held = False
        self._capturing = False

    def start(self) -> None:
        """Start the global keyboard hook that works even when VRChat has focus."""
        if pynput_keyboard is None:
            return
        self._listener = pynput_keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.start()

    def begin_capture(self) -> None:
        """Arm capture mode so the next key press becomes the new hotkey."""
        self._capturing = True

    def set_hotkey(self, key) -> None:
        """Apply a newly captured key as the active hotkey. Call from the Tk thread."""
        self.hotkey = key

    def _on_press(self, key) -> None:
        if self._capturing:
            self._capturing = False
            self._on_captured(key)
            return
        if key != self.hotkey or self._held:
            return
        self._held = True
        self._on_toggle()

    def _on_release(self, key) -> None:
        if key == self.hotkey:
            self._held = False

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
