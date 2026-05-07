"""System TTS fallback.

On macOS this uses ``say`` so speech starts immediately without writing a WAV
file first. It is intended as the MVP runtime fallback when MeloTTS is not
installed in the current Python environment.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess


class SystemTTS:
    def __init__(self, voice: str | None = None, rate: int | None = None) -> None:
        self.system = platform.system()
        self.voice = voice or os.environ.get("AMICONNECT_SYSTEM_TTS_VOICE", "Yuna")
        self.rate = rate or int(os.environ.get("AMICONNECT_SYSTEM_TTS_RATE", "185"))

    def speak(self, text: str) -> None:
        if not text.strip():
            return

        if self.system == "Darwin":
            if not shutil.which("say"):
                raise RuntimeError("macOS say command is not available")
            subprocess.run(
                ["say", "-v", self.voice, "-r", str(self.rate), text],
                check=False,
            )
            return

        raise RuntimeError(f"SystemTTS is not implemented for {self.system}")
