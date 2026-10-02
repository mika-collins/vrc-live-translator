# VRChat Live Translator

A free, lightweight desktop app that listens to the microphone, transcribes
speech, translates it, and sends the result straight into the VRChat
Chatbox.

## How it works

VRChat runs a small OSC (Open Sound Control) server in the background
whenever OSC is enabled in its settings, listening on `127.0.0.1:9000`. This
app is a completely separate program; it doesn't hook into VRChat directly.
It just sends UDP packets to that address. If VRChat is running with OSC
enabled, it picks them up and writes the text into the chatbox; if not, the
packets are silently dropped (UDP has no delivery confirmation).

That means:
- VRChat and this app are two independent programs. Launch order mostly
  doesn't matter, but VRChat needs to be running with OSC enabled *before*
  speaking, or the message won't go anywhere.
- Closing this app doesn't affect VRChat, and vice versa.

## Stack

- **Python 3.11+**: primary language.
- **Tkinter/ttk**: Python's built-in GUI toolkit; builds the app's window and controls.
- **SpeechRecognition + Google Web Speech API**: converts captured microphone audio into text.
- **MyMemory translation API**: translates the transcript between languages via MyMemory's free API, called directly with the Python standard library (anonymous tier capped around 5,000 words/day).
- **python-osc**: an OSC client and server; sends the translated text to VRChat's Chatbox and receives avatar parameter changes back from it (for the avatar toggle).
- **PyAudio**: gives SpeechRecognition access to the system microphone.
- **pynput**: a global keyboard hook that toggles listening via the desktop hotkey, even when VRChat has focus.

## Quick Setup

Open PowerShell in this project folder and run these commands once:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

After installation, start the desktop window with:

```powershell
python app.py
```

Choose a microphone, select the source and target language, then click
**Start listening**. Keep the PowerShell window open while the application
is running. Close the GUI window to exit.

The virtual environment needs to be activated again in each new PowerShell
window:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

It can also be launched without activation by using the environment's Python
directly:

```powershell
.\.venv\Scripts\python.exe app.py
```

## VRChat setup

1. Launch VRChat.
2. Open the Action Menu → **Options** → **OSC** → **Enabled**.
3. Leave VRChat running. It now listens for OSC messages on `127.0.0.1:9000`.

This app sends translated text to `/chatbox/input` with `True` as the second
argument, which submits the message immediately rather than just typing it
into the box.

## Hotkeys & VR control

Clicking **Start listening** works fine at a desk, but it isn't reachable
once VRChat has focus (and not while wearing a headset). Two ways
to start/stop listening remotely, each in its own guide:

- [Desktop hotkey setup](docs/desktop-hotkey.md) - a global keyboard
  shortcut (default F9). Best for desktop play or testing without a headset.
- [VRChat avatar toggle setup](docs/avatar-toggle-setup.md) - bind a toggle
  in the avatar's Expression Menu, controllable from a VR controller alone.
  Needed for headset/Quest play with no keyboard in reach; requires editing
  the avatar in Unity.

## Current limitations

- The free speech and translation web endpoints can rate-limit requests and
  may change behavior without notice. Network errors are logged and do not
  crash the GUI.
- One Chatbox message is sent per recognized phrase, so rapid speech can
  produce multiple back-to-back Chatbox submissions rather than one clean
  message.
- No delivery confirmation: if VRChat isn't listening, a send fails silently.
- VRChat's Chatbox has a character limit (~144); this app truncates before
  sending and logs when it does, so a truncated message won't be a silent
  surprise, but it will still cut off mid-sentence.

