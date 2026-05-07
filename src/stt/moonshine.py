"""Moonshine-tiny-ko ONNX STT wrapper and file-based test CLI."""
from __future__ import annotations

import argparse
import json
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

SAMPLE_RATE = 16_000
DEFAULT_MODEL = "UsefulSensors/moonshine-tiny-ko"


@dataclass
class STTResult:
    request_id: str | None
    input_audio: str | None
    transcript: str
    stt_confidence: float | None
    model: str
    sample_rate: int = SAMPLE_RATE

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _pcm_bytes_to_float32(raw: bytes, sample_width: int) -> np.ndarray:
    if sample_width == 1:
        audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        return (audio - 128.0) / 128.0
    if sample_width == 2:
        audio = np.frombuffer(raw, dtype="<i2").astype(np.float32)
        return audio / 32768.0
    if sample_width == 3:
        bytes_ = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        sign = (bytes_[:, 2] & 0x80) != 0
        padded = np.zeros((bytes_.shape[0], 4), dtype=np.uint8)
        padded[:, :3] = bytes_
        padded[sign, 3] = 0xFF
        audio = padded.view("<i4").reshape(-1).astype(np.float32)
        return audio / 8388608.0
    if sample_width == 4:
        audio = np.frombuffer(raw, dtype="<i4").astype(np.float32)
        return audio / 2147483648.0
    raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")


def _resample_linear(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate or audio.size == 0:
        return audio.astype(np.float32, copy=False)

    duration = audio.size / source_rate
    target_size = max(1, int(round(duration * target_rate)))
    source_x = np.linspace(0.0, duration, num=audio.size, endpoint=False)
    target_x = np.linspace(0.0, duration, num=target_size, endpoint=False)
    return np.interp(target_x, source_x, audio).astype(np.float32)


def load_wav_mono_16k(path: str | Path) -> np.ndarray:
    """Load a PCM WAV file as float32 mono 16 kHz audio."""
    audio_path = Path(path)
    try:
        with wave.open(str(audio_path), "rb") as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            raw = wav.readframes(wav.getnframes())

        audio = _pcm_bytes_to_float32(raw, sample_width)
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)
    except wave.Error:
        import soundfile as sf

        audio, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
    audio = _resample_linear(audio, sample_rate, SAMPLE_RATE)
    return np.clip(audio, -1.0, 1.0).astype(np.float32, copy=False)


class MoonshineSTT:
    """Thin wrapper around moonshine_onnx."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model_name = model
        self._impl = self._load(model)

    @staticmethod
    def _load(model: str) -> dict[str, Any]:
        model_path = Path(model)
        if model.startswith("UsefulSensors/") or (
            model_path.exists() and (model_path / "model.safetensors").exists()
        ):
            return MoonshineSTT._load_transformers(model)

        return MoonshineSTT._load_onnx(model)

    @staticmethod
    def _load_onnx(model: str) -> dict[str, Any]:
        try:
            from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
        except ImportError as e:
            raise RuntimeError(
                "moonshine_onnx not installed. `pip install useful-moonshine-onnx`"
            ) from e

        return {
            "backend": "onnx",
            "model": MoonshineOnnxModel(model_name=model),
            "tokenizer": load_tokenizer(),
        }

    @staticmethod
    def _load_transformers(model: str) -> dict[str, Any]:
        try:
            import torch
            from transformers import AutoProcessor, MoonshineForConditionalGeneration
        except ImportError as e:
            raise RuntimeError(
                "Transformers Moonshine backend not installed. `pip install transformers torch`"
            ) from e

        device = "cpu"
        try:
            processor = AutoProcessor.from_pretrained(model, local_files_only=True)
            hf_model = MoonshineForConditionalGeneration.from_pretrained(
                model,
                local_files_only=True,
            )
        except Exception:
            processor = AutoProcessor.from_pretrained(model)
            hf_model = MoonshineForConditionalGeneration.from_pretrained(model)
        hf_model = hf_model.to(device)
        hf_model.eval()
        return {
            "backend": "transformers",
            "model": hf_model,
            "processor": processor,
            "torch": torch,
            "device": device,
        }

    def transcribe(self, audio: np.ndarray) -> str:
        """audio: float32 mono 16kHz numpy array."""
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if self._impl["backend"] == "transformers":
            return self._transcribe_transformers(audio)
        # moonshine_onnx expects shape (1, N)
        wav = audio[np.newaxis, :]
        tokens = self._impl["model"].generate(wav)
        text = self._impl["tokenizer"].decode_batch(tokens)[0]
        return text.strip()

    def _transcribe_transformers(self, audio: np.ndarray) -> str:
        torch = self._impl["torch"]
        processor = self._impl["processor"]
        sample_rate = processor.feature_extractor.sampling_rate
        inputs = processor(audio, return_tensors="pt", sampling_rate=sample_rate)
        inputs = {key: value.to(self._impl["device"]) for key, value in inputs.items()}
        with torch.no_grad():
            generated_ids = self._impl["model"].generate(**inputs)
        return processor.decode(generated_ids[0], skip_special_tokens=True).strip()

    def transcribe_result(
        self,
        audio: np.ndarray,
        *,
        request_id: str | None = None,
        input_audio: str | None = None,
    ) -> STTResult:
        return STTResult(
            request_id=request_id,
            input_audio=input_audio,
            transcript=self.transcribe(audio),
            stt_confidence=None,
            model=self.model_name,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe one WAV file with Moonshine.")
    parser.add_argument("audio", help="Path to a WAV file")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--request-id", default=None)
    args = parser.parse_args()

    audio_path = Path(args.audio)
    stt = MoonshineSTT(model=args.model)
    result = stt.transcribe_result(
        load_wav_mono_16k(audio_path),
        request_id=args.request_id,
        input_audio=str(audio_path),
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
