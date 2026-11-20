"""Shared constants for the Live Translator for VRChat app."""

from __future__ import annotations

APP_TITLE = "Live Translator for VRChat"
HEADER_TITLE = "Live Translator"

VRCHAT_OSC_HOST = "127.0.0.1"
VRCHAT_OSC_SEND_PORT = 9000
VRCHAT_OSC_LISTEN_PORT = 9001
CHATBOX_ADDRESS = "/chatbox/input"
CHATBOX_CHAR_LIMIT = 144
DEFAULT_AVATAR_PARAMETER = "LiveTranslatorListening"

# The following languages are supported by the MyMemory translation endpoint
LANGUAGES = (
    ("en-US", "English (United States)"),
    ("ja-JP", "Japanese (Japan)"),
    ("ko-KR", "Korean (South Korea)"),
    ("zh-CN", "Chinese (Simplified, China)"),
    ("fr-FR", "French (France)"),
    ("de-DE", "German (Germany)"),
    ("es-ES", "Spanish (Spain)"),
    ("it-IT", "Italian (Italy)"),
    ("pt-PT", "Portuguese (Portugal)"),
)
LANGUAGE_LABEL_BY_CODE = dict(LANGUAGES)
LANGUAGE_CODE_BY_LABEL = {label: code for code, label in LANGUAGES}
