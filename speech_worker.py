"""Background thread: capture speech, transcribe, translate, and send onward."""

from __future__ import annotations

import threading
from typing import Callable

import speech_recognition as sr

from translator import TranslationError, translate_text


class SpeechWorker:
    """Run the listen-transcribe-translate loop on a background thread."""

    def __init__(
        self,
        recognizer: sr.Recognizer,
        microphone_name: str,
        microphone_indices: dict[str, int],
        get_source_language: Callable[[], str],
        get_target_language: Callable[[], str],
        get_transcribe_only: Callable[[], bool],
        stop_event: threading.Event,
        on_log: Callable[[str], None],
        on_result: Callable[[str], None],
        on_stopped: Callable[[], None],
    ) -> None:
        self._recognizer = recognizer
        self._microphone_name = microphone_name
        self._microphone_indices = microphone_indices
        self._get_source_language = get_source_language
        self._get_target_language = get_target_language
        self._get_transcribe_only = get_transcribe_only
        self._stop_event = stop_event
        self._on_log = on_log
        self._on_result = on_result
        self._on_stopped = on_stopped

    def run(self) -> None:
        """Capture speech, translate it, and send it onward until stopped."""
        try:
            microphone_index = self._microphone_indices.get(self._microphone_name)
            if microphone_index is None:
                raise ValueError(f"Unknown microphone: {self._microphone_name}")
            with sr.Microphone(device_index=microphone_index) as source:
                self._on_log("Adjusting for ambient noise for one second...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
                self._on_log("Ready for speech.")

                while not self._stop_event.is_set():
                    try:
                        # A short timeout lets the loop notice Stop promptly.
                        audio = self._recognizer.listen(source, timeout=1, phrase_time_limit=12)
                        transcript = self._recognizer.recognize_google(
                            audio, language=self._get_source_language()
                        )
                        self._on_log(f"You: {transcript}")
                        translated = self._translate(transcript)
                        self._on_result(translated)
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        self._on_log("Speech was not clear enough to transcribe.")
                    except sr.RequestError as error:
                        self._on_log(f"Speech recognition network error: {error}")
                    except TranslationError as error:
                        self._on_log(f"Translation failed: {error}")
                    except (OSError, ConnectionError) as error:
                        self._on_log(f"Audio or network error: {error}")
                    except Exception as error:
                        # Catch-all for unexpected errors in the worker thread; prevent silent failure.
                        self._on_log(f"Could not process phrase ({type(error).__name__}): {error}")
        except (OSError, ValueError, IndexError) as error:
            self._on_log(f"Could not start microphone: {error}")
        finally:
            self._on_stopped()

    def _translate(self, transcript: str) -> str:
        """Translate transcript unless transcribe-only mode is active."""
        if self._get_transcribe_only():
            return transcript
        source = self._get_source_language()
        target = self._get_target_language()
        translated = translate_text(transcript, source, target)
        self._on_log(f"Translation: {translated}")
        return translated
