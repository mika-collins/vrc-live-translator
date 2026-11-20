# PyInstaller build spec for the Windows release.
# Build with: pyinstaller --noconfirm VRCTranslator.spec
# Output: dist/VRCTranslator/ (one-folder build; zip it for distribution)
#
# Data files and runtime-selected modules for customtkinter, speech_recognition and
# pynput are collected automatically by hooks in pyinstaller-hooks-contrib, which is
# installed with PyInstaller. Only list things here that no hook covers.

import re
import shutil
import sys
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

APP_NAME = "VRCTranslator"
ROOT = Path(SPECPATH)

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
    # pynput is LGPL-licensed. Keeping it as plain .py files in _internal/pynput,
    # instead of inside the exe, lets users replace it with a modified version.
    module_collection_mode={"pynput": "py"},
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
    name=APP_NAME,
    icon="assets/icons/live_translator.ico",
    console=False,
    # UPX-compressed binaries are more likely to be flagged by antivirus.
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name=APP_NAME,
    upx=False,
)


# --- License files -------------------------------------------------------------------
# Copies LICENSE, THIRD-PARTY-NOTICES.md and a licenses/ folder next to the exe. The
# licenses/ folder gets the license files of every package the app bundles (found from
# requirements.txt and their dependencies), Python's license, and the extra texts kept
# in this repo's licenses/<package>/ folders for things packages don't ship themselves.

LICENSE_FILE = re.compile(r"(licen[cs]e|copying|notice)", re.IGNORECASE)


def bundled_distributions():
    """Return {canonical name: Distribution} for requirements.txt and dependencies."""
    pending = [
        Requirement(line).name
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    found = {}
    while pending:
        dist = metadata.distribution(pending.pop())
        key = canonicalize_name(dist.metadata["Name"])
        if key in found:
            continue
        found[key] = dist
        for requirement in map(Requirement, dist.requires or []):
            if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
                pending.append(requirement.name)
    # PyInstaller's bootloader starts the exe, but its own dependencies are build-only.
    found["pyinstaller"] = metadata.distribution("pyinstaller")
    return found


def copy_licenses(out_dir):
    licenses_dir = out_dir / "licenses"
    shutil.rmtree(licenses_dir, ignore_errors=True)
    distributions = bundled_distributions()
    extra_dirs = {
        canonicalize_name(path.name): path
        for path in (ROOT / "licenses").iterdir()
        if path.is_dir()
    }

    unknown = sorted(set(extra_dirs) - set(distributions))
    if unknown:
        sys.exit(f"licenses/ has folders for packages that aren't bundled: {unknown}")

    missing = []
    for key, dist in sorted(distributions.items()):
        target = licenses_dir / dist.metadata["Name"]
        target.mkdir(parents=True, exist_ok=True)
        files = [
            file
            for file in dist.files or []
            if ".dist-info" in str(file) and LICENSE_FILE.search(file.name)
        ]
        for file in files:
            shutil.copy2(file.locate(), target / file.name)
        if key in extra_dirs:
            shutil.copytree(extra_dirs[key], target, dirs_exist_ok=True)
        elif not files:
            missing.append(dist.metadata["Name"])
    if missing:
        sys.exit(
            f"No license file found for bundled packages {missing}. Add the license "
            "text to licenses/<package>/ in the repo and list the package in "
            "THIRD-PARTY-NOTICES.md."
        )

    python_dir = licenses_dir / "Python"
    python_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", python_dir / "LICENSE.txt")

    shutil.copy2(ROOT / "LICENSE", out_dir / "LICENSE.txt")
    shutil.copy2(ROOT / "THIRD-PARTY-NOTICES.md", out_dir / "THIRD-PARTY-NOTICES.txt")


copy_licenses(Path(DISTPATH) / APP_NAME)
