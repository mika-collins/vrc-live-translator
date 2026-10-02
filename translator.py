"""Text translation via the free MyMemory endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

MYMEMORY_MAX_QUERY_BYTES = 500
REQUEST_TIMEOUT_SECONDS = 5


class TranslationError(Exception):
    """Raised when a translation provider fails or returns an error response."""


def translate_text(text: str, source: str, target: str) -> str:
    """Translate text from source to target language."""
    if source == target:
        return text
    return _translate_mymemory(text, source, target)


def _translate_mymemory(text: str, source: str, target: str) -> str:
    """Translate text with MyMemory, raising TranslationError on any failure."""
    if len(text.encode("utf-8")) > MYMEMORY_MAX_QUERY_BYTES:
        raise TranslationError(
            f"Phrase is too long for MyMemory (limit is {MYMEMORY_MAX_QUERY_BYTES} bytes)."
        )

    query = urllib.parse.urlencode({"q": text, "langpair": f"{source}|{target}"})
    try:
        # Keep the https:// scheme written out here so Ruff's S310 rule can verify it.
        with urllib.request.urlopen(
            f"https://api.mymemory.translated.net/get?{query}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise TranslationError(f"MyMemory returned HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise TranslationError(f"Could not reach MyMemory: {error.reason}") from error
    except TimeoutError as error:
        raise TranslationError(
            f"MyMemory did not respond within {REQUEST_TIMEOUT_SECONDS} seconds."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TranslationError("MyMemory returned an unreadable response.") from error

    return _parse_mymemory_response(payload)


def _parse_mymemory_response(payload: object) -> str:
    """Extract the translation, treating any error or quota response as a failure."""
    if not isinstance(payload, dict):
        raise TranslationError("MyMemory returned an unexpected response.")

    details = payload.get("responseDetails") or "no details given"
    if payload.get("quotaFinished"):
        raise TranslationError(f"MyMemory daily quota exceeded: {details}")

    # responseStatus may be an int or a string depending on the error path.
    status = str(payload.get("responseStatus"))
    if status == "429":
        raise TranslationError(f"MyMemory daily quota exceeded: {details}")
    if status != "200":
        raise TranslationError(f"MyMemory error {status}: {details}")

    response_data = payload.get("responseData")
    translated = (
        response_data.get("translatedText") if isinstance(response_data, dict) else None
    )
    if not isinstance(translated, str) or not translated.strip():
        raise TranslationError("MyMemory returned an empty translation.")
    # Quota warnings have been seen inside translatedText with a 200 status.
    if translated.upper().startswith("MYMEMORY WARNING"):
        raise TranslationError(f"MyMemory daily quota exceeded: {translated}")
    return translated
