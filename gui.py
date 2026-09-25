"""Tk/ttk desktop window: wires the UI to the OSC, speech, and hotkey modules."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import speech_recognition as sr

from config import (
    APP_TITLE,
    CHATBOX_CHAR_LIMIT,
    DEFAULT_AVATAR_PARAMETER,
    LANGUAGE_CODE_BY_LABEL,
    LANGUAGE_LABEL_BY_CODE,
    LANGUAGES,
    VRCHAT_OSC_LISTEN_PORT,
)
from hotkey import AVAILABLE as HOTKEY_AVAILABLE
from hotkey import HotkeyManager, format_key
from osc_bridge import OscBridge
from speech_worker import SpeechWorker


class LiveTranslatorApp:
    """Own the controls, worker thread, and message flow for the application."""

    def __init__(self, root: tk.Tk) -> None:
        """Create the window and populate controls from local microphone data."""
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("760x620")
        self.root.minsize(620, 500)

        self.recognizer = sr.Recognizer()
        self.message_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None

        self.hotkey_manager = HotkeyManager(
            on_toggle=lambda: self.message_queue.put(("hotkey_press", None)),
            on_captured=lambda key: self.message_queue.put(("hotkey_captured", key)),
        )
        self.osc_bridge = OscBridge(
            on_avatar_param=lambda address, value: self.message_queue.put(
                ("avatar_param", (address, value))
            )
        )

        self.microphones = self._get_microphones()
        self.microphone_var = tk.StringVar(value=self.microphones[0])
        self.source_language_var = tk.StringVar(value="en-US")
        self.target_language_var = tk.StringVar(value="es-ES")
        self.source_language_display_var = tk.StringVar(value=LANGUAGE_LABEL_BY_CODE["en-US"])
        self.target_language_display_var = tk.StringVar(value=LANGUAGE_LABEL_BY_CODE["es-ES"])
        self.transcribe_only_var = tk.BooleanVar(value=False)
        self.hotkey_display_var = tk.StringVar(value=format_key(self.hotkey_manager.hotkey))
        self.avatar_parameter_var = tk.StringVar(value=DEFAULT_AVATAR_PARAMETER)
        self.status_var = tk.StringVar(value="Stopped")

        self._build_widgets()
        self._drain_messages()
        self._start_hotkey_listener()
        self._start_osc_server()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _get_microphones(self) -> list[str]:
        """Return input device names as reported by the default PyAudio host API."""
        self.microphone_indices: dict[str, int] = {}
        try:
            names = sr.Microphone.list_microphone_names()
        except OSError as error:
            self._queue_log(f"Could not list microphones: {error}")
            return ["No microphone found"]

        for index, name in enumerate(names):
            self.microphone_indices[name] = index

        return names or ["No microphone found"]

    def _build_widgets(self) -> None:
        """Build the form and the read-only activity log."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        settings = ttk.LabelFrame(self.root, text="Translation settings", padding=12)
        settings.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(3, weight=1)

        ttk.Label(settings, text="Microphone").grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")
        self.microphone_combo = ttk.Combobox(
            settings,
            textvariable=self.microphone_var,
            values=self.microphones,
            state="readonly",
        )
        self.microphone_combo.grid(row=0, column=1, columnspan=3, pady=5, sticky="ew")

        language_labels = tuple(label for _, label in LANGUAGES)

        ttk.Label(settings, text="Source language").grid(row=1, column=0, padx=(0, 8), pady=5, sticky="w")
        self.source_combo = ttk.Combobox(
            settings,
            textvariable=self.source_language_display_var,
            values=language_labels,
            state="readonly",
            width=26,
        )
        self.source_combo.grid(row=1, column=1, pady=5, sticky="ew")
        self.source_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.source_language_var.set(
                LANGUAGE_CODE_BY_LABEL[self.source_language_display_var.get()]
            ),
        )

        ttk.Label(settings, text="Target language").grid(row=1, column=2, padx=(20, 8), pady=5, sticky="w")
        self.target_combo = ttk.Combobox(
            settings,
            textvariable=self.target_language_display_var,
            values=language_labels,
            state="readonly",
            width=26,
        )
        self.target_combo.grid(row=1, column=3, pady=5, sticky="ew")
        self.target_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.target_language_var.set(
                LANGUAGE_CODE_BY_LABEL[self.target_language_display_var.get()]
            ),
        )

        ttk.Checkbutton(
            settings,
            text="Mute assist (transcribe only)",
            variable=self.transcribe_only_var,
            command=self._on_transcribe_only_toggle,
        ).grid(row=2, column=0, columnspan=4, pady=(8, 0), sticky="w")

        hotkeys = ttk.LabelFrame(self.root, text="Hotkeys & VR control", padding=12)
        hotkeys.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        hotkeys.columnconfigure(1, weight=1)

        ttk.Label(hotkeys, text="Desktop hotkey (toggle)").grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")
        ttk.Label(hotkeys, textvariable=self.hotkey_display_var, width=14).grid(row=0, column=1, pady=5, sticky="w")
        self.change_hotkey_button = ttk.Button(hotkeys, text="Change...", command=self._start_hotkey_capture)
        self.change_hotkey_button.grid(row=0, column=2, pady=5, sticky="e")
        if not HOTKEY_AVAILABLE:
            self.change_hotkey_button.state(["disabled"])

        ttk.Label(hotkeys, text="VRChat avatar parameter").grid(row=1, column=0, padx=(0, 8), pady=5, sticky="w")
        ttk.Entry(hotkeys, textvariable=self.avatar_parameter_var).grid(
            row=1, column=1, columnspan=2, pady=5, sticky="ew"
        )

        controls = ttk.Frame(self.root, padding=(16, 8))
        controls.grid(row=2, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        self.toggle_button = ttk.Button(controls, text="Start listening", command=self._toggle_listening)
        self.toggle_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.test_button = ttk.Button(controls, text="Send test message", command=self._send_test_message)
        self.test_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Label(controls, textvariable=self.status_var).grid(row=1, column=0, columnspan=2, pady=(6, 0))

        log_frame = ttk.LabelFrame(self.root, text="Activity log", padding=8)
        log_frame.grid(row=3, column=0, padx=16, pady=(8, 16), sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.activity_log = ScrolledText(log_frame, state="disabled", wrap=tk.WORD, height=16)
        self.activity_log.grid(row=0, column=0, sticky="nsew")

        self._queue_log("Ready. Choose a microphone and press Start listening.")

    def _on_transcribe_only_toggle(self) -> None:
        """Grey out the target language selector while transcribe only mode is active."""
        self.target_combo.configure(state="disabled" if self.transcribe_only_var.get() else "readonly")

    def _send_test_message(self) -> None:
        """Send a fixed string straight to VRChat, bypassing mic and translation."""
        self._queue_log("Sending OSC test message...")
        self._send_to_vrchat("VRC Live Translator test message")

    def _start_hotkey_listener(self) -> None:
        """Start the global keyboard hook that works even when VRChat has focus."""
        if not HOTKEY_AVAILABLE:
            self._queue_log(
                "pynput is not installed; the desktop hotkey is disabled. Run: pip install -r requirements.txt"
            )
            return
        try:
            self.hotkey_manager.start()
            self._queue_log(f"Desktop push-to-talk hotkey armed: {self.hotkey_display_var.get()}")
        except Exception as error:
            self._queue_log(f"Could not start the desktop hotkey listener ({type(error).__name__}): {error}")

    def _start_hotkey_capture(self) -> None:
        """Arm capture mode so the next key press becomes the new hotkey."""
        self.hotkey_manager.begin_capture()
        self.change_hotkey_button.state(["disabled"])
        self.hotkey_display_var.set("press a key...")
        self._queue_log("Press any key to set the new desktop hotkey...")

    def _finish_hotkey_capture(self, key) -> None:
        """Apply the captured key as the new hotkey (runs on the Tk main thread)."""
        self.hotkey_manager.set_hotkey(key)
        self.hotkey_display_var.set(format_key(key))
        self.change_hotkey_button.state(["!disabled"])
        self._queue_log(f"Desktop hotkey set to: {self.hotkey_display_var.get()}")

    def _start_osc_server(self) -> None:
        """Listen for VRChat avatar parameter changes, ex. an Expression Menu toggle."""
        try:
            self.osc_bridge.start_server()
            self._queue_log(f"Listening for avatar OSC parameters on port {VRCHAT_OSC_LISTEN_PORT}.")
        except OSError as error:
            self._queue_log(f"Could not start the avatar OSC listener on port {VRCHAT_OSC_LISTEN_PORT}: {error}")

    def _toggle_listening(self) -> None:
        """Start or stop the single background listening worker."""
        if self.worker and self.worker.is_alive():
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self) -> None:
        """Validate the microphone and start listening without blocking Tk."""
        microphone_name = self.microphone_var.get()
        if microphone_name == "No microphone found":
            messagebox.showerror(APP_TITLE, "No microphone is available.")
            return

        self.stop_event.clear()
        speech_worker = SpeechWorker(
            recognizer=self.recognizer,
            microphone_name=microphone_name,
            microphone_indices=self.microphone_indices,
            get_source_language=self.source_language_var.get,
            get_target_language=self.target_language_var.get,
            get_transcribe_only=self.transcribe_only_var.get,
            stop_event=self.stop_event,
            on_log=self._queue_log,
            on_result=self._send_to_vrchat,
            on_stopped=lambda: self.message_queue.put(("stopped", "")),
        )
        self.worker = threading.Thread(target=speech_worker.run, name="speech-listener", daemon=True)
        self.worker.start()
        self.toggle_button.configure(text="Stop listening")
        self.status_var.set("Listening")
        self._queue_log(f"Listening with: {microphone_name}")

    def _stop_listening(self) -> None:
        """Ask the worker to finish its current listen cycle and stop."""
        self.stop_event.set()
        self.toggle_button.configure(text="Stopping...")
        self.toggle_button.state(["disabled"])
        self._queue_log("Stopping listener...")

    def _send_to_vrchat(self, text: str) -> None:
        """Send translated text to VRChat's local OSC Chatbox endpoint."""
        _, truncated = self.osc_bridge.send_chatbox(text)
        if truncated:
            self._queue_log(f"Message truncated to {CHATBOX_CHAR_LIMIT} characters.")
        self._queue_log("Sent to VRChat Chatbox.")

    def _queue_log(self, message: str) -> None:
        """Queue a log message so only the Tk main thread touches widgets."""
        self.message_queue.put(("log", message))

    def _drain_messages(self) -> None:
        """Apply worker messages to widgets, then check again shortly."""
        try:
            while True:
                message_type, message = self.message_queue.get_nowait()
                if message_type == "log":
                    self.activity_log.configure(state="normal")
                    self.activity_log.insert(tk.END, f"{message}\n")
                    self.activity_log.see(tk.END)
                    self.activity_log.configure(state="disabled")
                elif message_type == "stopped":
                    self.toggle_button.state(["!disabled"])
                    self.toggle_button.configure(text="Start listening")
                    self.status_var.set("Stopped")
                    self._queue_log("Listener stopped.")
                elif message_type == "hotkey_press":
                    self._toggle_listening()
                elif message_type == "hotkey_captured":
                    self._finish_hotkey_capture(message)
                elif message_type == "avatar_param":
                    address, value = message
                    expected_address = f"/avatar/parameters/{self.avatar_parameter_var.get()}"
                    if address != expected_address:
                        continue
                    is_listening = bool(self.worker and self.worker.is_alive())
                    if value and not is_listening:
                        self._queue_log("Avatar toggle: starting listening.")
                        self._start_listening()
                    elif not value and is_listening:
                        self._queue_log("Avatar toggle: stopping listening.")
                        self._stop_listening()
        except queue.Empty:
            pass
        self.root.after(100, self._drain_messages)

    def _close(self) -> None:
        """Request shutdown and close the window without waiting on the worker."""
        self.stop_event.set()
        self.hotkey_manager.stop()
        self.osc_bridge.shutdown()
        self.root.destroy()
