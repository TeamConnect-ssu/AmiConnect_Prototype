"""Mic capture + Silero VAD utterance segmentation for macOS."""
from __future__ import annotations

import queue
from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
FRAME_MS = 32
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000  # 512


@dataclass
class VADConfig:
    threshold: float = 0.5
    min_speech_ms: int = 250
    silence_tail_ms: int = 700
    max_utterance_ms: int = 12_000


class MicVADStream:
    def __init__(self, device: int | None = None, vad_cfg: VADConfig | None = None) -> None:
        self.device = device
        self.cfg = vad_cfg or VADConfig()
        self._q: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._vad = self._load_vad()

    @staticmethod
    def _load_vad():
        from silero_vad import load_silero_vad

        return load_silero_vad(onnx=True)

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            pass  # underflow/overflow — ignore for MVP
        # Mono float32 16kHz expected
        self._q.put(indata[:, 0].copy())

    def utterances(self) -> Iterator[np.ndarray]:
        """Yield numpy float32 mono utterances at 16kHz, segmented by VAD."""
        import torch

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=FRAME_SAMPLES,
            device=self.device,
            callback=self._callback,
        )
        speech_frames: list[np.ndarray] = []
        in_speech = False
        silence_ms = 0
        speech_ms = 0

        with self._stream:
            while True:
                frame = self._q.get()
                tensor = torch.from_numpy(frame)
                prob = float(self._vad(tensor, SAMPLE_RATE).item())
                is_speech = prob >= self.cfg.threshold

                if is_speech:
                    speech_frames.append(frame)
                    speech_ms += FRAME_MS
                    silence_ms = 0
                    in_speech = True
                elif in_speech:
                    speech_frames.append(frame)
                    silence_ms += FRAME_MS
                    if silence_ms >= self.cfg.silence_tail_ms:
                        if speech_ms >= self.cfg.min_speech_ms:
                            yield np.concatenate(speech_frames)
                        speech_frames = []
                        in_speech = False
                        silence_ms = 0
                        speech_ms = 0
                if speech_ms >= self.cfg.max_utterance_ms:
                    yield np.concatenate(speech_frames)
                    speech_frames = []
                    in_speech = False
                    silence_ms = 0
                    speech_ms = 0
