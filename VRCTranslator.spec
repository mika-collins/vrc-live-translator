# PyInstaller build spec for the Windows release.
# Build with: pyinstaller VRCTranslator.spec
# Output: dist/VRCTranslator/ (one-folder build; zip it for distribution)

from PyInstaller.utils.hooks import collect_data_files

datas = [("assets", "assets")]
# CustomTkinter themes and fonts are loaded from the package directory at runtime.
datas += collect_data_files("customtkinter")
# recognize_google shells out to the flac encoder bundled inside speech_recognition.
datas += collect_data_files("speech_recognition", include_py_files=False)

a = Analysis(
    ["app.py"],
    datas=datas,
    # pynput picks its platform backend at runtime, so PyInstaller can't see it.
    hiddenimports=["pynput.keyboard._win32", "pynput.mouse._win32"],
    excludes=[],
)
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
