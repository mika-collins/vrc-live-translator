# PyInstaller build spec for the Windows release.
# Build with: pyinstaller --noconfirm VRCTranslator.spec
# Output: dist/VRCTranslator/ (one-folder build; zip it for distribution)
#
# Data files and runtime-selected modules for customtkinter, speech_recognition and
# pynput are collected automatically by hooks in pyinstaller-hooks-contrib, which is
# installed with PyInstaller. Only list things here that no hook covers.

# Bundled data files that the app never uses, matched by their path inside _internal.
EXCLUDED_DATA = (
    # Offline Sphinx speech model (~38 MB); the app only uses Google recognition.
    "speech_recognition/pocketsphinx-data/",
    # FLAC encoders for other platforms; Windows uses flac-win32.exe.
    "speech_recognition/flac-linux-",
    "speech_recognition/flac-mac",
)

a = Analysis(
    ["app.py"],
    datas=[("assets", "assets")],
)
a.datas = [
    entry
    for entry in a.datas
    if not entry[0].replace("\\", "/").startswith(EXCLUDED_DATA)
]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VRCTranslator",
    icon="assets/icons/live_translator.ico",
    console=False,
    # UPX-compressed binaries are more likely to be flagged by antivirus.
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="VRCTranslator",
    upx=False,
)
