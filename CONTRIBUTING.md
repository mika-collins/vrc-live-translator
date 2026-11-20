# Contributing

This guide covers how the app works, how to run it from source, and how
changes are checked, built and released.

## Reporting bugs and requesting features

Open an [issue](https://github.com/mika-collins/vrc-live-translator/issues/new/choose)
and pick the template that fits: **Bug report**, **Feature request** or
**Task / chore**. For bugs, include which release was downloaded (or the
commit, if running from source) and anything shown in the app's Activity
log.

## How it works

VRChat runs a small OSC (Open Sound Control) server whenever OSC is enabled
in its settings, listening on `127.0.0.1:9000`. This app is a separate
program; it doesn't modify or hook into VRChat. It sends UDP packets to that
address, and VRChat writes the text into the Chatbox. If VRChat isn't
running with OSC enabled, the packets are silently dropped (UDP has no
delivery confirmation).

That means:
- VRChat and this app are independent programs. Launch order mostly doesn't
  matter, but VRChat needs to be running with OSC enabled before speaking,
  or the message won't go anywhere.
- Closing this app doesn't affect VRChat, and vice versa.

The app also listens on `127.0.0.1:9001` for avatar parameter changes sent by
VRChat, which is how the avatar toggle starts and stops listening.

### Project layout

| Path | Purpose |
| --- | --- |
| [`app.py`](app.py) | Entry point |
| [`config.py`](config.py) | Shared constants: OSC ports and addresses, supported languages |
| [`gui/`](gui/) | CustomTkinter window, theme colours and icon loading |
| [`speech_worker.py`](speech_worker.py) | Background thread: capture speech, transcribe, translate, send |
| [`translator.py`](translator.py) | Translation through the MyMemory API |
| [`osc_bridge.py`](osc_bridge.py) | OSC: Chatbox messages out, avatar parameters in |
| [`hotkey.py`](hotkey.py) | Global desktop hotkey |
| [`assets/icons/`](assets/icons/) | App icon and UI images |
| [`VRCTranslator.spec`](VRCTranslator.spec) | PyInstaller build configuration |

### Built with

- **Python 3.11+**: primary language.
- **CustomTkinter**: a modern-looking layer over Tkinter, Python's built-in GUI toolkit.
- **SpeechRecognition + Google Web Speech API**: converts captured microphone audio into text.
- **MyMemory translation API**: translates the transcript, called directly with the Python standard library (anonymous tier capped around 5,000 words/day).
- **python-osc**: an OSC client and server; sends the translated text to VRChat's Chatbox and receives avatar parameter changes back from it (for the avatar toggle).
- **PyAudio**: gives SpeechRecognition access to the system microphone.
- **pynput**: a global keyboard hook that toggles listening via the desktop hotkey, even when VRChat has focus.
- **PyInstaller**: packages the app as a Windows executable for releases.

## Running from source

Install [Python 3.11](https://www.python.org/downloads/), then open
PowerShell in the project folder and run these commands once:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Then start the app with:

```powershell
python app.py
```

Keep the PowerShell window open while the app is running. Close the app
window to exit.

The virtual environment needs to be activated again in each new PowerShell
window. Activation can also be skipped by using the environment's Python
directly:

```powershell
.\.venv\Scripts\python.exe app.py
```

## Making changes

All changes reach `main` through a pull request:

1. Create a branch from `main`.
2. Make the changes and run the [checks](#checks) locally.
3. Open a pull request and fill in the template. PR titles follow
   [Conventional Commits](https://www.conventionalcommits.org/), for example
   `feat: add Japanese as a target language` or
   `fix(osc): truncate messages over the 144-char chatbox limit`.
4. Link the issue it addresses (`Closes #12`).

### Checks

Every pull request runs the checks in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml):

| Check | Tool | What it verifies |
| --- | --- | --- |
| Lint | [Ruff](https://docs.astral.sh/ruff/), [actionlint](https://github.com/rhysd/actionlint) | Code quality, formatting, and workflow file mistakes |
| Install & compile | pip, `compileall` | Dependencies install and the app imports on Windows with Python 3.11 |
| Type check | [Pyright](https://github.com/microsoft/pyright) | Type hints are consistent across the app and its libraries |
| Security audit | [pip-audit](https://github.com/pypa/pip-audit) | No dependency has a known vulnerability |
| Package | PyInstaller | The Windows executable builds and contains its required files (see [Building the Windows executable](#building-the-windows-executable)) |

Install the development tools into the virtual environment:

```powershell
pip install -r requirements-dev.txt
```

Run the same checks locally before pushing:

```powershell
ruff check .
ruff format --check .
pyright
pip-audit -r requirements.txt -r requirements-dev.txt -r requirements-build.txt
actionlint
```

`ruff check --fix .` and `ruff format .` fix most lint and formatting issues
automatically.

Dependencies are pinned to exact versions in the `requirements*.txt` files.
[Dependabot](.github/dependabot.yml) opens a pull request each week when
updates are available.

## Building the Windows executable

The app is packaged with [PyInstaller](https://pyinstaller.org/) as a
one-folder build, configured in [`VRCTranslator.spec`](VRCTranslator.spec):

```powershell
pip install -r requirements-build.txt
pyinstaller --noconfirm VRCTranslator.spec
```

The output is `dist/VRCTranslator/`. Run `VRCTranslator.exe` inside it to
test. The `_internal` folder must stay next to the `.exe`. The `build/` and
`dist/` folders are generated output and are ignored by git.

The build steps live in one place,
[`.github/workflows/build.yml`](.github/workflows/build.yml), which both CI
and the release workflow use. Every pull request builds the executable, and
the zip is attached to the CI run as the `windows-build` artifact (kept for
7 days) so reviewers can download and try it.

Most dependencies need no spec changes: PyInstaller and
[pyinstaller-hooks-contrib](https://github.com/pyinstaller/pyinstaller-hooks-contrib)
already know how to bundle common packages, including CustomTkinter,
SpeechRecognition and pynput. When adding a dependency or app file that the
build doesn't pick up on its own:

- **New files in `assets/`** are included automatically.
- **Other data files or modules loaded at runtime** that no hook covers go in
  `datas` or `hiddenimports` in the spec's `Analysis(...)`.
- **Files the app loads at runtime** should be added to the list in the
  **Check bundled files** step of `build.yml`, so a build that leaves them out
  fails.
- **Large bundled files the app doesn't use** can be dropped through
  `EXCLUDED_DATA` in the spec.

Changes that affect packaging should be tested by running the built exe, not
just `python app.py`.

## Releasing

Releases are built and published by
[`.github/workflows/release.yml`](.github/workflows/release.yml). To publish
a new version, tag a commit on `main` and push the tag:

```powershell
git checkout main
git pull
git tag v1.0.0
git push origin v1.0.0
```

The workflow first checks that the tagged commit is on `main` and stops if
it isn't. It then builds the executable on a fresh Windows machine, zips it as
`VRCTranslator-v1.0.0-windows.zip`, and creates a GitHub Release with the
zip, a SHA-256 checksum, and release notes generated from the merged pull
requests. It also adds a
[build attestation](https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations)
proving the zip was built by this workflow.

Use [semantic versioning](https://semver.org/) (`vMAJOR.MINOR.PATCH`). Tags
with a suffix, such as `v1.0.0-beta.1`, are published as pre-releases.

To test a build without publishing anything, open the **Actions** tab,
choose **Release**, and click **Run workflow**. The zip is attached to the
workflow run as a downloadable artifact.
