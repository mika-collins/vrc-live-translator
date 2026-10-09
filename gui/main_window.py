"""CustomTkinter desktop window: wires the UI to the OSC, speech, and hotkey modules."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox
from typing import cast

import customtkinter as ctk
import pyaudio
import speech_recognition as sr

from config import (
    APP_TITLE,
    CHATBOX_CHAR_LIMIT,
    DEFAULT_AVATAR_PARAMETER,
    HEADER_TITLE,
    LANGUAGE_CODE_BY_LABEL,
    LANGUAGE_LABEL_BY_CODE,
    LANGUAGES,
    VRCHAT_OSC_LISTEN_PORT,
)
from gui import icons, theme
from hotkey import AVAILABLE as HOTKEY_AVAILABLE
from hotkey import HotkeyManager, format_key
from osc_bridge import OscBridge
from speech_worker import SpeechWorker


class LiveTranslatorApp:
    """Own the controls, worker thread, and message flow for the application."""

    def __init__(self, root: ctk.CTk) -> None:
        """Create the window and populate controls from local microphone data."""
        theme.apply()

        self.root = root
        self.root.title(APP_TITLE)
        # Set before CustomTkinter applies its default icon; default= also covers dialogs.
        self.root.iconbitmap(default=str(icons.APP_ICON))
        self.root.geometry("780x840")
        self.root.minsize(640, 600)
        self.root.configure(fg_color=theme.BG_PRIMARY)

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
        self.source_language_display_var = tk.StringVar(
            value=LANGUAGE_LABEL_BY_CODE["en-US"]
        )
        self.target_language_display_var = tk.StringVar(
            value=LANGUAGE_LABEL_BY_CODE["es-ES"]
        )
        self.transcribe_only_var = tk.BooleanVar(value=False)
        self.hotkey_display_var = tk.StringVar(
            value=format_key(self.hotkey_manager.hotkey)
        )
        self.avatar_parameter_var = tk.StringVar(value=DEFAULT_AVATAR_PARAMETER)
        self.status_var = tk.StringVar(value="Stopped")

        self._build_widgets()
        self._drain_messages()
        self._start_hotkey_listener()
        self._start_osc_server()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _get_microphones(self) -> list[str]:
        self.microphone_indices: dict[str, int] = {}
        try:
            audio = pyaudio.PyAudio()
        except OSError as error:
            self._queue_log(f"Could not list microphones: {error}")
            return ["No microphone found"]

        try:
            wdm_ks_host_apis = {
                index
                for index in range(audio.get_host_api_count())
                if str(audio.get_host_api_info_by_index(index)["name"]).startswith(
                    "Windows WDM-KS"
                )
            }

            names: list[str] = []
            for device_index in range(audio.get_device_count()):
                info = audio.get_device_info_by_index(device_index)
                if int(info.get("maxInputChannels", 0)) <= 0:
                    continue
                if info.get("hostApi") in wdm_ks_host_apis:
                    continue
                name = str(info.get("name", ""))
                if not name:
                    continue

                matched_existing = next(
                    (
                        existing
                        for existing in names
                        if existing == name
                        or existing.startswith(name)
                        or name.startswith(existing)
                    ),
                    None,
                )
                if matched_existing is None:
                    names.append(name)
                    self.microphone_indices[name] = device_index
                    continue

                if len(name) > len(matched_existing):
                    first_index = self.microphone_indices.pop(matched_existing)
                    names[names.index(matched_existing)] = name
                    self.microphone_indices[name] = first_index
        finally:
            audio.terminate()

        return names or ["No microphone found"]

    def _section(self, parent: tk.Misc, title: str) -> ctk.CTkFrame:
        """Build a titled panel matching the app's dark card style."""
        outer = ctk.CTkFrame(
            parent,
            fg_color=theme.BG_PANEL,
            corner_radius=theme.RADIUS_PANEL,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.CONTROL_BORDER,
        )
        ctk.CTkLabel(
            outer, text=title, font=theme.section_font(), text_color=theme.TEXT_PRIMARY
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=(14, 4), sticky="w")
        return outer

    def _build_widgets(self) -> None:
        """Build the header, form, controls, and read-only activity log."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        header = ctk.CTkFrame(
            self.root, fg_color=theme.BG_PRIMARY, corner_radius=0, height=84
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header, text="", image=icons.load("vrchat_white_96.png", (60, 60))
        ).grid(row=0, column=0, padx=(16, 10), pady=10)
        ctk.CTkLabel(
            header,
            text=HEADER_TITLE,
            font=theme.title_font(),
            text_color=theme.TEXT_PRIMARY,
        ).grid(row=0, column=1, sticky="w", pady=10)

        settings = self._section(self.root, "Translation settings")
        settings.grid(row=1, column=0, padx=16, pady=(16, 8), sticky="ew")
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(3, weight=1)

        ctk.CTkLabel(settings, text="Microphone", font=theme.body_font()).grid(
            row=1, column=0, padx=(16, 8), pady=8, sticky="w"
        )
        self.microphone_menu = ctk.CTkOptionMenu(
            settings,
            variable=self.microphone_var,
            values=self.microphones,
            fg_color=theme.CONTROL_BG,
            button_color=theme.CONTROL_BG,
            button_hover_color=theme.CONTROL_BG_HOVER,
            text_color=theme.ACCENT,
            dropdown_fg_color=theme.CONTROL_BG,
            dropdown_hover_color=theme.CONTROL_BG_HOVER,
            dropdown_text_color=theme.ACCENT,
            corner_radius=theme.RADIUS_CONTROL,
            height=36,
            font=theme.control_font(),
        )
        self.microphone_menu.grid(
            row=1, column=1, columnspan=3, padx=(0, 16), pady=8, sticky="ew"
        )

        language_labels = [label for _, label in LANGUAGES]

        ctk.CTkLabel(settings, text="Source language", font=theme.body_font()).grid(
            row=2, column=0, padx=(16, 8), pady=8, sticky="w"
        )
        self.source_menu = ctk.CTkOptionMenu(
            settings,
            variable=self.source_language_display_var,
            values=language_labels,
            command=self._on_source_language_change,
            fg_color=theme.CONTROL_BG,
            button_color=theme.CONTROL_BG,
            button_hover_color=theme.CONTROL_BG_HOVER,
            text_color=theme.ACCENT,
            dropdown_fg_color=theme.CONTROL_BG,
            dropdown_hover_color=theme.CONTROL_BG_HOVER,
            dropdown_text_color=theme.ACCENT,
            corner_radius=theme.RADIUS_CONTROL,
            height=36,
            font=theme.control_font(),
        )
        self.source_menu.grid(row=2, column=1, padx=(0, 8), pady=8, sticky="ew")

        ctk.CTkLabel(settings, text="Target language", font=theme.body_font()).grid(
            row=2, column=2, padx=(8, 8), pady=8, sticky="w"
        )
        self.target_menu = ctk.CTkOptionMenu(
            settings,
            variable=self.target_language_display_var,
            values=language_labels,
            command=self._on_target_language_change,
            fg_color=theme.CONTROL_BG,
            button_color=theme.CONTROL_BG,
            button_hover_color=theme.CONTROL_BG_HOVER,
            text_color=theme.ACCENT,
            dropdown_fg_color=theme.CONTROL_BG,
            dropdown_hover_color=theme.CONTROL_BG_HOVER,
            dropdown_text_color=theme.ACCENT,
            corner_radius=theme.RADIUS_CONTROL,
            height=36,
            font=theme.control_font(),
        )
        self.target_menu.grid(row=2, column=3, padx=(0, 16), pady=8, sticky="ew")

        ctk.CTkCheckBox(
            settings,
            text="Mute assist (transcribe only)",
            variable=self.transcribe_only_var,
            command=self._on_transcribe_only_toggle,
            font=theme.body_font(),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.CONTROL_BORDER,
            text_color=theme.TEXT_PRIMARY,
        ).grid(row=3, column=0, columnspan=4, padx=16, pady=(4, 14), sticky="w")

        hotkeys = self._section(self.root, "Hotkeys & VR control")
        hotkeys.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        hotkeys.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hotkeys, text="Desktop hotkey (toggle)", font=theme.body_font()
        ).grid(row=1, column=0, padx=(16, 8), pady=8, sticky="w")
        ctk.CTkLabel(
            hotkeys,
            textvariable=self.hotkey_display_var,
            font=theme.mono_font(),
            text_color=theme.ACCENT,
            width=90,
        ).grid(row=1, column=1, pady=8, sticky="w")
        self.change_hotkey_button = ctk.CTkButton(
            hotkeys,
            text="Change...",
            command=self._start_hotkey_capture,
            fg_color=theme.CONTROL_BG,
            hover_color=theme.CONTROL_BG_HOVER,
            text_color=theme.ACCENT,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.CONTROL_BORDER,
            corner_radius=theme.RADIUS_CONTROL,
            font=theme.control_font(),
            width=100,
        )
        self.change_hotkey_button.grid(
            row=1, column=2, padx=(8, 16), pady=8, sticky="e"
        )
        if not HOTKEY_AVAILABLE:
            self.change_hotkey_button.configure(state="disabled")

        ctk.CTkLabel(
            hotkeys, text="VRChat avatar parameter", font=theme.body_font()
        ).grid(row=2, column=0, padx=(16, 8), pady=(0, 14), sticky="w")
        ctk.CTkEntry(
            hotkeys,
            textvariable=self.avatar_parameter_var,
            fg_color=theme.CONTROL_BG,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.CONTROL_BORDER,
            text_color=theme.TEXT_PRIMARY,
            corner_radius=theme.RADIUS_CONTROL,
        ).grid(row=2, column=1, columnspan=2, padx=(0, 16), pady=(0, 14), sticky="ew")

        controls = ctk.CTkFrame(self.root, fg_color="transparent")
        controls.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        self.toggle_button = ctk.CTkButton(
            controls,
            text="Start listening",
            command=self._toggle_listening,
            fg_color=theme.PRIMARY_ACTION_BG,
            hover_color=theme.PRIMARY_ACTION_HOVER,
            text_color=theme.PRIMARY_ACTION_TEXT,
            corner_radius=theme.RADIUS_CONTROL,
            font=theme.control_font(),
            height=44,
        )
        self.toggle_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.test_button = ctk.CTkButton(
            controls,
            text="Send test message",
            command=self._send_test_message,
            fg_color=theme.CONTROL_BG,
            hover_color=theme.CONTROL_BG_HOVER,
            text_color=theme.ACCENT,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.CONTROL_BORDER,
            corner_radius=theme.RADIUS_CONTROL,
            font=theme.control_font(),
            height=44,
        )
        self.test_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(
            controls,
            textvariable=self.status_var,
            font=theme.body_font(),
            text_color=theme.TEXT_MUTED,
        ).grid(row=1, column=0, columnspan=2, pady=(8, 0))

        log_frame = self._section(self.root, "Activity log")
        log_frame.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="nsew")
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.activity_log = ctk.CTkTextbox(
            log_frame,
            state="disabled",
            wrap="word",
            font=theme.mono_font(),
            fg_color=theme.BG_PRIMARY,
            text_color=theme.TEXT_PRIMARY,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.CONTROL_BORDER,
            corner_radius=theme.RADIUS_PANEL,
        )
        self.activity_log.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        self._queue_log("Ready. Choose a microphone and press Start listening.")

    def _on_source_language_change(self, _selected_label: str) -> None:
        self.source_language_var.set(
            LANGUAGE_CODE_BY_LABEL[self.source_language_display_var.get()]
        )

    def _on_target_language_change(self, _selected_label: str) -> None:
        self.target_language_var.set(
            LANGUAGE_CODE_BY_LABEL[self.target_language_display_var.get()]
        )

    def _on_transcribe_only_toggle(self) -> None:
        """Grey out the target language selector while transcribe only mode is active."""
        self.target_menu.configure(
            state="disabled" if self.transcribe_only_var.get() else "normal"
        )

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
            self._queue_log(
                f"Desktop push-to-talk hotkey armed: {self.hotkey_display_var.get()}"
            )
        except Exception as error:
            self._queue_log(
                f"Could not start the desktop hotkey listener ({type(error).__name__}): {error}"
            )

    def _start_hotkey_capture(self) -> None:
        """Arm capture mode so the next key press becomes the new hotkey."""
        self.hotkey_manager.begin_capture()
        self.change_hotkey_button.configure(state="disabled")
        self.hotkey_display_var.set("press a key...")
        self._queue_log("Press any key to set the new desktop hotkey...")

    def _finish_hotkey_capture(self, key) -> None:
        """Apply the captured key as the new hotkey (runs on the Tk main thread)."""
        self.hotkey_manager.set_hotkey(key)
        self.hotkey_display_var.set(format_key(key))
        self.change_hotkey_button.configure(state="normal")
        self._queue_log(f"Desktop hotkey set to: {self.hotkey_display_var.get()}")

    def _start_osc_server(self) -> None:
        """Listen for VRChat avatar parameter changes, ex. an Expression Menu toggle."""
        try:
            self.osc_bridge.start_server()
            self._queue_log(
                f"Listening for avatar OSC parameters on port {VRCHAT_OSC_LISTEN_PORT}."
            )
        except OSError as error:
            self._queue_log(
                f"Could not start the avatar OSC listener on port {VRCHAT_OSC_LISTEN_PORT}: {error}"
            )

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
        self.worker = threading.Thread(
            target=speech_worker.run, name="speech-listener", daemon=True
        )
        self.worker.start()
        self.toggle_button.configure(
            text="Stop listening",
            fg_color=theme.STOP_ACTION_BG,
            hover_color=theme.STOP_ACTION_HOVER,
            text_color=theme.STOP_ACTION_TEXT,
        )
        self.status_var.set("Listening")
        self._queue_log(f"Listening with: {microphone_name}")

    def _stop_listening(self) -> None:
        """Ask the worker to finish its current listen cycle and stop."""
        self.stop_event.set()
        self.toggle_button.configure(text="Stopping...", state="disabled")
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
                    self.activity_log.insert("end", f"{message}\n")
                    self.activity_log.see("end")
                    self.activity_log.configure(state="disabled")
                elif message_type == "stopped":
                    self.toggle_button.configure(
                        state="normal",
                        text="Start listening",
                        fg_color=theme.PRIMARY_ACTION_BG,
                        hover_color=theme.PRIMARY_ACTION_HOVER,
                        text_color=theme.PRIMARY_ACTION_TEXT,
                    )
                    self.status_var.set("Stopped")
                    self._queue_log("Listener stopped.")
                elif message_type == "hotkey_press":
                    self._toggle_listening()
                elif message_type == "hotkey_captured":
                    self._finish_hotkey_capture(message)
                elif message_type == "avatar_param":
                    address, value = cast(tuple[str, bool], message)
                    expected_address = (
                        f"/avatar/parameters/{self.avatar_parameter_var.get()}"
                    )
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
