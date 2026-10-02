"""Text translation via the free MyMemory endpoint."""

from __future__ import annotations

from typing import cast

from deep_translator import MyMemoryTranslator


def translate_text(text: str, source: str, target: str) -> str:
    """Translate text from source to target language using the MyMemory backend."""
    if source == target:
        return text
    # translate() only returns a list when return_all=True, which isn't used here.
    return cast(str, MyMemoryTranslator(source=source, target=target).translate(text))
