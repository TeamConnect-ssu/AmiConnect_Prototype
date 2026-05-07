"""MeloTTS Korean wrapper for AmiConnect MVP.

Official references:
- https://github.com/myshell-ai/MeloTTS
- https://huggingface.co/myshell-ai/MeloTTS-Korean

MeloTTS writes speech to a WAV file, then this wrapper optionally plays it.
That makes the MVP easy to verify on Windows/macOS and keeps generated demo
audio under ``results/tts``.
"""
from __future__ import annotations

import argparse
import os
import platform
import re
import subprocess
import sys
import time
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


class MeloTTS:
    """Generate Korean speech with MeloTTS and optionally play the WAV."""

    def __init__(
        self,
        language: str | None = None,
        speaker: str | None = None,
        speed: float | None = None,
        device: str | None = None,
        output_dir: str | Path | None = None,
        auto_play: bool | None = None,
        cleanup: bool | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.language = language or os.environ.get("AMICONNECT_TTS_LANGUAGE", "KR")
        self.speaker = speaker or os.environ.get("AMICONNECT_TTS_SPEAKER", "KR")
        self.speed = speed if speed is not None else float(os.environ.get("AMICONNECT_TTS_SPEED", "1.0"))
        self.device = device or os.environ.get("AMICONNECT_TTS_DEVICE", "auto")
        self.output_dir = Path(
            output_dir or os.environ.get("AMICONNECT_TTS_OUTPUT_DIR") or repo_root / "results" / "tts"
        )
        self.auto_play = (
            os.environ.get("AMICONNECT_TTS_PLAY", "true").lower() != "false"
            if auto_play is None
            else auto_play
        )
        self.cleanup = (
            os.environ.get("AMICONNECT_TTS_CLEANUP", "true").lower() != "false"
            if cleanup is None
            else cleanup
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model = self._load_model()
        self.speaker_id = self._resolve_speaker_id()

    def _patch_korean_imports(self) -> None:
        if self.language.split("-")[0].upper() != "KR":
            return

        # MeloTTS imports every language cleaner at module import time. The
        # non-Korean cleaners eagerly load tokenizers, which is
        # unnecessary for Korean synthesis and can fail before KR is reached.
        def unsupported(*_: Any, **__: Any) -> None:
            raise RuntimeError("Non-Korean MeloTTS cleaners are disabled in AmiConnect KR mode")

        def distribute_phone(n_phone: int, n_word: int) -> list[int]:
            phones_per_word = [0] * n_word
            for _ in range(n_phone):
                min_tasks = min(phones_per_word)
                min_index = phones_per_word.index(min_tasks)
                phones_per_word[min_index] += 1
            return phones_per_word

        for module_name in (
            "melo.text.chinese",
            "melo.text.japanese",
            "melo.text.english",
            "melo.text.chinese_mix",
            "melo.text.french",
            "melo.text.spanish",
        ):
            stub = types.ModuleType(module_name)
            stub.text_normalize = unsupported
            stub.g2p = unsupported
            stub.get_bert_feature = unsupported
            stub.distribute_phone = distribute_phone
            sys.modules.setdefault(module_name, stub)

        # MeloTTS imports cached_path even when use_hf=True, but AmiConnect
        # does not need its optional S3/GCS clients for the Korean model path.
        cached_path_stub = types.ModuleType("cached_path")
        cached_path_stub.cached_path = unsupported
        sys.modules.setdefault("cached_path", cached_path_stub)

    def _load_model(self) -> Any:
        try:
            self._patch_korean_imports()
            from melo.api import TTS
        except Exception as exc:
            raise RuntimeError(
                "MeloTTS is not available in this environment. Because MeloTTS pins "
                "transformers==4.27.4, do not install it through amiconnect extras. "
                "Install the MeloTTS package with --no-deps, then add the Korean TTS "
                "runtime dependencies separately, or run TTS in a separate venv."
            ) from exc

        return TTS(language=self.language, device=self.device)

    def _resolve_speaker_id(self) -> int:
        speaker_ids = dict(self.model.hps.data.spk2id)
        if self.speaker in speaker_ids:
            return int(speaker_ids[self.speaker])
        if self.language in speaker_ids:
            return int(speaker_ids[self.language])
        if len(speaker_ids) == 1:
            return int(next(iter(speaker_ids.values())))

        available = ", ".join(sorted(speaker_ids))
        raise ValueError(f"Unknown MeloTTS speaker '{self.speaker}'. Available speakers: {available}")

    def speak(self, text: str) -> Path | None:
        """Synthesize text to a timestamped WAV file and play it when enabled."""
        if not text.strip():
            return None

        if self.auto_play and os.environ.get("AMICONNECT_TTS_CHUNKED", "true").lower() != "false":
            outputs = self.speak_chunked(text)
            return outputs[-1] if outputs else None

        stamp = time.strftime("%Y%m%d-%H%M%S")
        output_wav = self.output_dir / f"tts-{stamp}.wav"
        self.synthesize_to_file(text, output_wav)

        if self.auto_play:
            self.play(output_wav)
            if self.cleanup:
                self._delete_file(output_wav)

        print(f"[TTS] {output_wav}")
        return output_wav

    def speak_chunked(self, text: str) -> list[Path]:
        """Generate short WAV chunks and play each one as soon as it is ready.

        MeloTTS exposes a file-oriented API, not a streaming PCM API. Chunking
        gives lower perceived latency while preserving the generated audio files.
        """
        chunks = self._split_text(text)
        if not chunks:
            return []

        stamp = time.strftime("%Y%m%d-%H%M%S")
        outputs = [self.output_dir / f"tts-{stamp}-{idx:02d}.wav" for idx in range(1, len(chunks) + 1)]

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.synthesize_to_file, chunks[0], outputs[0])
            for idx, chunk in enumerate(chunks):
                output = future.result()
                next_idx = idx + 1
                if next_idx < len(chunks):
                    future = pool.submit(self.synthesize_to_file, chunks[next_idx], outputs[next_idx])
                self.play(output)
                if self.cleanup:
                    self._delete_file(output)
                print(f"[TTS] {output}")

        return outputs

    @staticmethod
    def _delete_file(path: str | Path) -> None:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError as exc:
            print(f"[TTS cleanup skipped] {exc}")

    @staticmethod
    def _split_text(text: str, max_chars: int = 45) -> list[str]:
        sentences = [
            part.strip()
            for part in re.findall(r"[^.!?\n。！？]+[.!?。！？]?", text)
            if part.strip()
        ]
        chunks: list[str] = []
        for sentence in sentences:
            if len(sentence) <= max_chars:
                chunks.append(sentence)
                continue
            parts = [part.strip() for part in re.split(r"([,，、])", sentence) if part.strip()]
            current = ""
            for part in parts:
                candidate = f"{current}{part}" if part in {",", "，", "、"} else f"{current} {part}".strip()
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    if current:
                        chunks.append(current)
                    current = part
            if current:
                chunks.append(current)
        return chunks

    def synthesize_to_file(self, text: str, output_wav: str | Path) -> Path:
        output_path = Path(output_wav)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.tts_to_file(text, self.speaker_id, str(output_path), speed=self.speed)
        return output_path

    def play(self, wav_path: str | Path) -> None:
        path = str(wav_path)
        system = platform.system()
        if system == "Windows":
            import winsound

            winsound.PlaySound(path, winsound.SND_FILENAME)
        elif system == "Darwin":
            subprocess.run(["afplay", path], check=False)
        else:
            subprocess.run(["aplay", path], check=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument("--output", help="Output WAV path")
    parser.add_argument("--no-play", action="store_true", help="Generate WAV without playback")
    parser.add_argument("--keep-file", action="store_true", help="Do not delete generated WAV after playback")
    parser.add_argument("--language", default=None, help="MeloTTS language code, default KR")
    parser.add_argument("--speaker", default=None, help="MeloTTS speaker key, default KR")
    parser.add_argument("--speed", type=float, default=None, help="Speech speed, default 1.0")
    parser.add_argument("--device", default=None, help="cpu, cuda:0, mps, or auto")
    args = parser.parse_args()

    tts = MeloTTS(
        language=args.language,
        speaker=args.speaker,
        speed=args.speed,
        device=args.device,
        auto_play=not args.no_play,
        cleanup=not args.keep_file,
    )
    if args.output:
        output = tts.synthesize_to_file(args.text, args.output)
        if not args.no_play:
            tts.play(output)
        print(f"[TTS] {output}")
    else:
        tts.speak(args.text)


if __name__ == "__main__":
    main()
