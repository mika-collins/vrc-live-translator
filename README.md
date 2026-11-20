# VRChat Live Translator

A free, lightweight Windows app that listens to a microphone, turns speech
into text, translates it, and sends the result straight into the VRChat
Chatbox, so other players can read it in their own language. It runs
alongside VRChat and talks to it through VRChat's built-in OSC feature; it
doesn't modify the game.

> VRChat Live Translator is not affiliated with or endorsed by VRChat Inc.

## Download

**[Download the latest release](https://github.com/mika-collins/vrc-live-translator/releases/latest)**

Requirements:
- Windows 10 or 11 (64-bit)
- An internet connection (speech recognition and translation run online)
- VRChat, with OSC enabled (see [Getting started](#getting-started))

No Python or other software needs to be installed. Everything the app needs
is included in the download.

### Install

1. On the release page, under **Assets**, download
   `VRCTranslator-<version>-windows.zip`.
2. Right-click the zip and choose **Extract All...**, then pick a place to
   keep it.
3. Open the extracted `VRCTranslator` folder and double-click
   **`VRCTranslator.exe`**.

Keep the `_internal` folder next to `VRCTranslator.exe`. The app needs the
files inside it. Running the exe from inside the zip without extracting it
first won't work.

To uninstall, delete the `VRCTranslator` folder.

### "Windows protected your PC"

The first time the app is opened, Windows SmartScreen may show a blue
**"Windows protected your PC"** warning. It appears because the app isn't
code-signed, which is common for free, open-source tools, and doesn't mean
anything was found wrong with it. Click **More info**, then **Run anyway**.
Windows remembers the choice.

Only download the app from this repository's
[Releases page](https://github.com/mika-collins/vrc-live-translator/releases).
Each release also includes a `.sha256` checksum file, which confirms the
download wasn't changed. To check it, download both files into the same
folder, open PowerShell in that folder, and run the command below with
`<version>` replaced. It prints `True` when the zip matches:

```powershell
(Get-FileHash .\VRCTranslator-<version>-windows.zip).Hash -eq (Get-Content .\VRCTranslator-<version>-windows.zip.sha256).Split()[0]
```

## Getting started

1. **Enable OSC in VRChat.** Open the Action Menu, then
   **Options → OSC → Enabled**. This only needs to be done once.
2. **Open VRChat Live Translator.**
3. **Choose a microphone**, the spoken language (**Source language**) and
   the language to translate to (**Target language**).
4. Click **Send test message**. "VRC Live Translator test message" should
   appear in the Chatbox above the avatar in VRChat. If it doesn't, see
   [Troubleshooting](#troubleshooting).
5. Click **Start listening** and speak. Each phrase is translated and posted
   to the Chatbox after a pause in speech.

**Mute assist (transcribe only)** skips translation and sends speech as-is,
which is useful for playing muted with speech typed out in the Chatbox.

### Desktop and VR setup

Clicking **Start listening** works at a desk, but the button can't be
reached while VRChat has focus or while wearing a headset. There are two
ways to start and stop listening from inside the game:

- **Desktop**: a keyboard shortcut (F9 by default) that works even while
  VRChat is the active window. Best for desktop mode.
- **VR**: a toggle in the avatar's Expression Menu, which controls the app
  from a VR controller. Needed for headset play without a keyboard in reach.
  This requires adding a parameter to the avatar in Unity.

Step-by-step desktop and VR guides are coming soon.

## Privacy

To work, the app sends data to two free online services:

- **Recorded speech** is sent to Google's speech recognition service to be
  turned into text.
- **The recognized text** is sent to [MyMemory](https://mymemory.translated.net/)
  to be translated.

Both connections are encrypted (HTTPS). The app only records while it is
listening, and it doesn't save audio or text. Each service handles what it
receives under its own terms, so avoid saying anything sensitive while the
app is listening.

## Troubleshooting

**Nothing shows up in the VRChat Chatbox**
- Check that OSC is enabled in VRChat (**Options → OSC → Enabled**).
- Use **Send test message**. If the test message doesn't arrive, the problem
  is the connection to VRChat, not the microphone.
- Another OSC app may already be using the same ports (9000/9001). Close
  other OSC tools and try again.

**No microphones are listed, or nothing is heard**
- Open Windows **Settings → Privacy & security → Microphone** and turn on
  **Let desktop apps access your microphone**.
- Check that the right microphone is selected and isn't muted in Windows.

**Translation stops working partway through the day**
- The free MyMemory service allows about 5,000 words per day. The Activity
  log shows a "quota exceeded" message when the limit is reached. It resets
  daily.

**Antivirus software flagged the app**
- The desktop hotkey uses a keyboard hook so that it works while VRChat has
  focus. Some antivirus tools treat any keyboard hook in an unsigned app as
  suspicious. The app only checks whether a pressed key is the chosen
  hotkey; it doesn't record or send keystrokes.

## Contributing

Any feedback is welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md) for how the app works, how to run it from
source, and how releases are built.
