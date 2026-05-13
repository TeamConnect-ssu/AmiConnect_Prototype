"""End-to-end MVP pipeline (Mac terminal):
mic -> VAD -> Moonshine STT -> Router(Local rule TLM | Mindlogic Gateway) -> Executor -> TTS -> Rich console.
"""
from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs) -> bool:
        return False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    _RICH_TAG_RE = re.compile(r"\[/?[a-zA-Z][^\]]*\]")

    def _plain(value: object) -> str:
        return _RICH_TAG_RE.sub("", str(value))

    class Console:
        def print(self, value: object = "", *args, **kwargs) -> None:
            print(_plain(value))

    class Panel:
        def __init__(self, renderable: object, title: str | None = None, **kwargs) -> None:
            self.renderable = renderable
            self.title = title

        @classmethod
        def fit(cls, renderable: object, **kwargs) -> "Panel":
            return cls(renderable, **kwargs)

        def __str__(self) -> str:
            return f"{self.title + ': ' if self.title else ''}{_plain(self.renderable)}"

    class Table:
        def __init__(self, *args, **kwargs) -> None:
            self.rows: list[tuple[object, ...]] = []

        def add_column(self, *args, **kwargs) -> None:
            pass

        def add_row(self, *values: object) -> None:
            self.rows.append(values)

        def __str__(self) -> str:
            return "\n".join("  ".join(_plain(value) for value in row) for row in self.rows)

from src.router.router import Router
from src.schema import PipelineResult
import src.executor as executor
from src.stt.moonshine import DEFAULT_MODEL as DEFAULT_STT_MODEL


def _result_table(result: PipelineResult, latency_ms: dict[str, float]) -> Table:
    tbl = Table(show_header=False, box=None, padding=(0, 1))
    tbl.add_column(style="cyan", no_wrap=True)
    tbl.add_column()
    tbl.add_row("STT 텍스트", f"[bold white]{result.transcript}[/bold white]")
    tbl.add_row(
        "Intent",
        f"[bold green]{result.intent}[/bold green]  route=[yellow]{result.route}[/yellow]  confidence=[cyan]{result.confidence:.2f}[/cyan]",
    )
    slot_str = ", ".join(f"{k}={v}" for k, v in result.slots.items()) or "[dim](none)[/dim]"
    tbl.add_row("Slots", slot_str)
    if result.command:
        tbl.add_row("Command", f"[dim]{result.command.get('action')} → {result.command.get('target')}[/dim]")
    if result.response_text:
        tbl.add_row("응답", f"[italic]{result.response_text}[/italic]")
    if result.error:
        tbl.add_row("Error", f"[red]{result.error}[/red]")
    lat = " | ".join(f"{k}: {v:.0f}ms" for k, v in latency_ms.items())
    tbl.add_row("Latency", f"[yellow]{lat}[/yellow]")
    return tbl


def _process(result: PipelineResult, tts_backend: str) -> None:
    if result.command:
        executor.execute(result.command)
    if result.response_text:
        backend = tts_backend.lower()
        if backend in {"melo", "auto"}:
            try:
                from src.tts.melo import MeloTTS

                MeloTTS().speak(result.response_text)
                return
            except Exception as exc:
                if backend == "melo":
                    print(f"[TTS skipped] {exc}")
                    return
                print(f"[TTS fallback] MeloTTS unavailable: {exc}")
        if backend in {"system", "auto"}:
            try:
                from src.tts.system import SystemTTS

                SystemTTS().speak(result.response_text)
            except Exception as exc:
                print(f"[TTS skipped] {exc}")


def run_mic(
    console: Console,
    router: Router,
    mic_index: int | None,
    stt_model: str,
    tts_backend: str,
) -> None:
    import sounddevice as sd

    from src.audio.microphone import MicVADStream
    from src.stt.moonshine import MoonshineSTT

    console.print(Panel.fit("[bold]AmiConnect MVP[/bold] — 마이크에 말씀하세요. Ctrl+C 종료.", style="cyan"))
    console.print("[dim]Loading Moonshine STT...[/dim]")
    stt = MoonshineSTT(model=stt_model)
    console.print("[dim]Initializing mic + VAD...[/dim]")
    if len(sd.query_devices()) == 0:
        raise RuntimeError(
            "PortAudio가 오디오 장치를 찾지 못했습니다. macOS 마이크 권한이나 실행 환경을 확인하세요."
        )
    mic = MicVADStream(device=mic_index)

    for utt in mic.utterances():
        t0 = time.time()
        text = stt.transcribe(utt)
        t1 = time.time()
        if not text:
            continue
        console.print(f"[cyan]STT:[/cyan] [bold white]{text}[/bold white]")
        result = router.route(text)
        t2 = time.time()
        _process(result, tts_backend)
        console.print(
            Panel(
                _result_table(result, {"audio": len(utt) / 16.0, "stt": (t1 - t0) * 1000, "nlu": (t2 - t1) * 1000}),
                title="Utterance",
                border_style="green",
            )
        )


def run_audio_file(
    console: Console,
    router: Router,
    audio_file: str,
    stt_model: str,
    tts_backend: str,
) -> None:
    from src.stt.moonshine import MoonshineSTT, load_wav_mono_16k

    t0 = time.time()
    audio = load_wav_mono_16k(audio_file)
    t1 = time.time()
    stt = MoonshineSTT(model=stt_model)
    text = stt.transcribe(audio)
    t2 = time.time()
    result = router.route(text)
    t3 = time.time()
    _process(result, tts_backend)
    console.print(
        Panel(
            _result_table(
                result,
                {
                    "audio_load": (t1 - t0) * 1000,
                    "audio": len(audio) / 16.0,
                    "stt": (t2 - t1) * 1000,
                    "nlu": (t3 - t2) * 1000,
                },
            ),
            title=f"Audio file: {audio_file}",
            border_style="green",
        )
    )


def run_text(console: Console, router: Router, text: str, tts_backend: str) -> None:
    t0 = time.time()
    result = router.route(text)
    t1 = time.time()
    _process(result, tts_backend)
    console.print(
        Panel(
            _result_table(result, {"nlu": (t1 - t0) * 1000}),
            title="Text input",
            border_style="green",
        )
    )


def run_chat(console: Console, router: Router, tts_backend: str) -> None:
    console.print(Panel.fit("[bold]AmiConnect Chat[/bold] — 명령을 입력하세요. 종료: /exit 또는 Ctrl+C", style="cyan"))
    while True:
        try:
            text = input("ami> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye.[/dim]")
            return
        if not text:
            continue
        if text in {"/exit", "/quit", "exit", "quit"}:
            console.print("[dim]bye.[/dim]")
            return
        run_text(console, router, text, tts_backend)


def main() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", help="음성 대신 텍스트로 단발 테스트")
    parser.add_argument("--chat", action="store_true", help="텍스트 채팅처럼 여러 명령을 연속 입력")
    parser.add_argument("--audio-file", help="녹음된 WAV 파일로 STT + 라우터 단발 테스트")
    parser.add_argument("--mic", action="store_true", help="마이크 입력 모드")
    parser.add_argument("--mic-index", type=int, default=None)
    parser.add_argument("--stt-model", default=DEFAULT_STT_MODEL)
    parser.add_argument(
        "--tts-backend",
        choices=["system", "melo", "auto", "none"],
        default=os.environ.get("AMICONNECT_TTS_BACKEND", "system").lower(),
        help="TTS backend: system=macOS say, melo=MeloTTS, auto=Melo then system, none=disable",
    )
    parser.add_argument("--privacy", action="store_true", help="cloud LLM 호출 차단")
    args = parser.parse_args()

    console = Console()
    router = Router(privacy_mode=True if args.privacy else None)

    if args.text:
        run_text(console, router, args.text, args.tts_backend)
    elif args.chat:
        run_chat(console, router, args.tts_backend)
    elif args.audio_file:
        run_audio_file(console, router, args.audio_file, args.stt_model, args.tts_backend)
    elif args.mic:
        try:
            run_mic(console, router, args.mic_index, args.stt_model, args.tts_backend)
        except KeyboardInterrupt:
            console.print("\n[dim]bye.[/dim]")
        except Exception as exc:
            console.print(f"[red]Mic mode failed:[/red] {exc}")
            raise SystemExit(1) from exc
    else:
        parser.error("--text, --chat, --audio-file, --mic 중 하나를 지정하세요.")


if __name__ == "__main__":
    main()
