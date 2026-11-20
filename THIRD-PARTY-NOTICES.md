# Third-party notices

Live Translator for VRChat is licensed under the MIT License (see
`LICENSE`). The Windows download also includes the open-source software
listed below. Each component belongs to its authors and is used under its
own license.

The download contains the full license texts in the `licenses` folder, next
to `VRCTranslator.exe`, with one subfolder per component. That folder is
generated each time the app is built, so it always covers every bundled
Python package, including small dependencies not listed by name here.

## Bundled software

- **Python** (Python Software Foundation License)
  Copyright (c) 2001 Python Software Foundation. https://www.python.org
  Python's Windows build also includes OpenSSL, libffi, bzip2, XZ (liblzma),
  Expat, Tcl/Tk and the Microsoft Visual C++ runtime, whose notices are part
  of Python's license file.
  License text: `licenses/Python/LICENSE.txt`

- **CustomTkinter** (MIT License)
  Copyright (c) 2023 Tom Schimansky.
  https://github.com/TomSchimansky/CustomTkinter
  License text: `licenses/customtkinter/`
  - Includes the **Roboto** font, Copyright 2011 Google Inc., under the
    Apache License 2.0. License text: `licenses/customtkinter/Apache-2.0.txt`

- **darkdetect** (BSD 3-Clause License), used by CustomTkinter
  Copyright (c) 2019, Alberto Sottile. https://github.com/albertosottile/darkdetect

- **packaging** (Apache License 2.0 or BSD 2-Clause License), used by
  CustomTkinter. https://github.com/pypa/packaging

- **Pillow** (MIT-CMU License)
  Copyright (c) 1997-2011 by Secret Labs AB, Copyright (c) 1995-2011 by
  Fredrik Lundh and contributors, Copyright (c) 2010 by Jeffrey 'Alex' Clark
  and contributors. https://python-pillow.github.io
  Pillow's Windows build includes image and font libraries (such as
  FreeType, HarfBuzz, libjpeg-turbo and zlib), whose notices are part of
  Pillow's license file. License text: `licenses/pillow/`

- **PyAudio** (MIT License)
  Copyright (c) 2006 Hubert Pham. https://people.csail.mit.edu/hubert/pyaudio/
  - Includes **PortAudio**, Copyright (c) 1999-2006 Ross Bencina and Phil
    Burk, under the PortAudio (MIT-style) license. https://www.portaudio.com
    License text: `licenses/PyAudio/PortAudio.txt`

- **pynput** (GNU Lesser General Public License v3), see below
  Copyright (C) 2015-2024 Moses Palmér. https://github.com/moses-palmer/pynput

- **python-osc** (The Unlicense, public domain)
  https://github.com/attwad/python-osc

- **six** (MIT License), used by pynput
  Copyright (c) 2010-2024 Benjamin Peterson. https://github.com/benjaminp/six

- **SpeechRecognition** (BSD 3-Clause License)
  Copyright (c) 2014-, Anthony Zhang.
  https://github.com/Uberi/speech_recognition
  - Includes the **FLAC** audio encoder, see below.

- **typing_extensions** (Python Software Foundation License)
  https://github.com/python/typing_extensions

- **PyInstaller bootloader** (GNU General Public License v2 or later, with
  the PyInstaller Bootloader Exception), which starts the app. The exception
  allows programs built with PyInstaller to be distributed under their own
  license. https://pyinstaller.org
  License text: `licenses/pyinstaller/COPYING.txt`

## pynput (LGPL v3)

pynput is included unmodified, as plain Python source files in the
`_internal/pynput` folder of the download, so it can be replaced with a
modified version. Its source code is available at
https://github.com/moses-palmer/pynput. The source code and build
configuration for this app are in this repository, so the app can also be
rebuilt with a different version of pynput.

License texts: `licenses/pynput/COPYING.LGPL` (LGPL v3) and
`licenses/pynput/GPL-3.0.txt` (GPL v3, which the LGPL v3 builds on).

## FLAC (GPL v2)

SpeechRecognition ships the FLAC command-line encoder as
`_internal/speech_recognition/flac-win32.exe`. It is an unmodified copy of
FLAC 1.3.2, Copyright (C) 2000-2009 Josh Coalson and (C) 2011-2016 Xiph.Org
Foundation, licensed under the GNU General Public License v2. It is a
separate program that the app runs to compress audio before sending it for
speech recognition; the GPL applies to the FLAC encoder only.

The complete source code for FLAC 1.3.2 is attached to every release of
this app as `flac-1.3.2.tar.xz`, on the same page as the download:
https://github.com/mika-collins/vrc-live-translator/releases. It is also
available from the FLAC project at
https://github.com/xiph/flac/releases/tag/1.3.2.

License text: `licenses/SpeechRecognition/LICENSE-FLAC.txt`

## Online services

The app sends recorded speech to Google's speech recognition service and
recognized text to the MyMemory translation service
(https://mymemory.translated.net). These services are not part of the
download and are provided by their owners under their own terms. See the
Privacy section of the README for what is sent.

## Trademarks

VRChat is a trademark of VRChat Inc. Google is a trademark of Google LLC.
Other product and company names are trademarks of their respective owners.
They are used here only to describe what the app works with, and their use
doesn't imply any affiliation with or endorsement by their owners.
