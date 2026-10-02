"""VRChat OSC send/receive: Chatbox messages out, avatar parameters in."""

from __future__ import annotations

import threading
from collections.abc import Callable

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from config import (
    CHATBOX_ADDRESS,
    CHATBOX_CHAR_LIMIT,
    VRCHAT_OSC_HOST,
    VRCHAT_OSC_LISTEN_PORT,
    VRCHAT_OSC_SEND_PORT,
)


class OscBridge:
    """Own the OSC client (send to VRChat) and server (receive avatar params)."""

    def __init__(self, on_avatar_param: Callable[[str, bool], None]) -> None:
        self._client = SimpleUDPClient(VRCHAT_OSC_HOST, VRCHAT_OSC_SEND_PORT)
        self._on_avatar_param = on_avatar_param
        self.server: ThreadingOSCUDPServer | None = None

    def send_chatbox(self, text: str) -> tuple[str, bool]:
        """Send text to VRChat's Chatbox, truncating to the character limit.

        Returns the (possibly truncated) text and whether truncation happened.
        """
        truncated = len(text) > CHATBOX_CHAR_LIMIT
        if truncated:
            text = text[:CHATBOX_CHAR_LIMIT]
        # The second value tells VRChat to immediately submit the Chatbox text.
        self._client.send_message(CHATBOX_ADDRESS, [text, True])
        return text, truncated

    def start_server(self) -> None:
        """Listen for VRChat avatar parameter changes, ex. an Expression Menu toggle."""
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._handle_message)
        self.server = ThreadingOSCUDPServer((VRCHAT_OSC_HOST, VRCHAT_OSC_LISTEN_PORT), dispatcher)
        threading.Thread(target=self.server.serve_forever, name="osc-server", daemon=True).start()

    def _handle_message(self, address: str, *args) -> None:
        if not args:
            return
        self._on_avatar_param(address, bool(args[0]))

    def shutdown(self) -> None:
        if self.server is not None:
            self.server.shutdown()
