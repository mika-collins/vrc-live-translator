"""Text translation via the free MyMemory endpoint."""
import os # Unused import to test Ruff
from __future__ import annotations

from deep_translator import MyMemoryTranslator


def translate_text(text: str, source: str, target: str) -> str:
    """Translate text from source to target language using the MyMemory backend."""
    if source == target:
        return text
    return MyMemoryTranslator(source=source, target=target).translate(text)
