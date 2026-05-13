"""OBS-friendly AmiConnect MVP demo runner.

This keeps the real Router path, but formats each scenario for video capture:
life scene -> local MVP decision -> policy/action/result.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTHONWARNINGS", "ignore")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.router.router import Router
from src.schema import PipelineResult


@dataclass(frozen=True)
class DemoScene:
    scene_id: str
    title: str
    wake_word: str
    voice_line: str
    life_result: str
    caption: str
    status_policy: str


SCENES: tuple[DemoScene, ...] = (
    DemoScene(
        scene_id="01",
        title="거실 조명 안전 디밍",
        wake_word="동구야",
        voice_line="거실 불 꺼줘",
        life_result="거실 조명은 완전히 꺼지지 않고 20% 밝기로 유지됩니다.",
        caption='같은 "불 꺼줘"라도, 시니어케어에서는 다르게 동작합니다.',
        status_policy="senior_care.min_brightness",
    ),
    DemoScene(
        scene_id="02",
        title="복약 시간 확인",
        wake_word="동구야",
        voice_line="약 먹을 시간 됐나",
        life_result="복약 일정을 조회하고 다음 복용 시간을 안내합니다.",
        caption="복약 일정은 로컬 시스템에서 확인합니다.",
        status_policy="senior_care.medication_enabled",
    ),
    DemoScene(
        scene_id="03",
        title="추위 대응",
        wake_word="동구야",
        voice_line="추워",
        life_result="방 온도를 올리고 보온 보조 장치를 제안합니다.",
        caption="단순 제어를 넘어 돌봄 맥락의 다음 행동을 제안합니다.",
        status_policy="senior_care.suggest_warmth_aid",
    ),
    DemoScene(
        scene_id="04",
        title="긴급 도움 요청",
        wake_word="동구야",
        voice_line="도와줘",
        life_result="보호자에게 긴급 알림을 보내고 어르신에게 대기 안내를 합니다.",
        caption="긴급 요청은 보호자 알림으로 연결됩니다.",
        status_policy="senior_care.emergency",
    ),
    DemoScene(
        scene_id="05",
        title="아파트형 취침 장면 실행",
        wake_word="헤이 푸르지오",
        voice_line="자기 전 분위기로 해줘",
        life_result="조명 20%, 따뜻한 색온도, 야간 모드를 함께 적용합니다.",
        caption="호출어 이후의 명령을 이해하고, 주거 환경에 맞는 취침 장면을 실행합니다.",
        status_policy="senior_care.bedtime_scene",
    ),
)


def _command_summary(command: dict[str, Any]) -> str:
    if not command:
        return "(none)"
    action = command.get("action", "?")
    target = command.get("target", "?")
    params = command.get("params") or {}
    if isinstance(params, dict) and isinstance(params.get("steps"), list):
        steps = " -> ".join(str(step.get("action", "?")) for step in params["steps"])
        return f"{target} <- {action} ({len(params['steps'])} steps: {steps})"
    compact_params = ", ".join(f"{k}={v}" for k, v in params.items()) if isinstance(params, dict) else str(params)
    return f"{target} <- {action} ({compact_params or 'no params'})"


def _large_action_summary(command: dict[str, Any]) -> str:
    if not command:
        return "(none)"
    params = command.get("params") or {}
    if isinstance(params, dict) and isinstance(params.get("steps"), list):
        return "bedroom light 20% + warm 2200K + night mode"
    return _command_summary(command)


def _large_slot_summary(result: PipelineResult) -> str:
    if not result.slots:
        return "(none)"
    return " · ".join(f"{k}: {v}" for k, v in result.slots.items())


def _policy(command: dict[str, Any], fallback: str) -> str:
    if not command:
        return fallback
    return str(command.get("policy_applied") or fallback or "(none)")


def _decision_table(result: PipelineResult, scene: DemoScene, latency_ms: float, *, show_latency: bool = True) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("field", style="cyan", no_wrap=True, width=14)
    table.add_column("value", style="white")
    table.add_row("음성 인식", f"[bold]{result.transcript}[/bold]")
    table.add_row("Intent", f"[bold green]{result.intent or '(unknown)'}[/bold green]  confidence=[cyan]{result.confidence:.2f}[/cyan]")
    table.add_row("Route", f"[yellow]{result.route}[/yellow]")
    slot_str = ", ".join(f"{k}={v}" for k, v in result.slots.items()) or "[dim](none)[/dim]"
    table.add_row("Slots", slot_str)
    table.add_row("Policy", f"[bold yellow]{_policy(result.command, scene.status_policy)}[/bold yellow]")
    table.add_row("Command", f"[white]{_command_summary(result.command)}[/white]")
    table.add_row("응답", f"[italic]{result.response_text or result.error or '(none)'}[/italic]")
    if show_latency:
        table.add_row("Latency", f"[yellow]{latency_ms:.0f}ms[/yellow]")
    return table


def _status_panel(scene: DemoScene, result: PipelineResult) -> Panel:
    text = Text()
    text.append("AmiConnect MVP\n", style="bold white")
    text.append("\nMode: ", style="cyan")
    text.append("Senior Care", style="bold white")
    text.append("\nPrivacy: ", style="cyan")
    text.append("ON", style="bold green")
    text.append("\nCloud LLM: ", style="cyan")
    text.append("BLOCKED", style="bold red")
    text.append("\n\nCurrent Policy:\n", style="cyan")
    text.append(_policy(result.command, scene.status_policy), style="bold yellow")
    text.append("\n\nLife Result:\n", style="cyan")
    text.append(scene.life_result, style="white")
    return Panel(text, title="Status", border_style="cyan")


def _scene_panel(scene: DemoScene) -> Panel:
    text = Text()
    text.append(f"Scene {scene.scene_id}. {scene.title}\n", style="bold white")
    text.append("\n할머니: ", style="cyan")
    text.append(f'"{scene.wake_word}"', style="bold white")
    text.append("\nAmiConnect: ", style="cyan")
    text.append('"네, 말씀하세요."', style="bold green")
    text.append("\n할머니: ", style="cyan")
    text.append(f'"{scene.voice_line}"', style="bold white")
    text.append("\n\nCaption: ", style="cyan")
    text.append(scene.caption, style="white")
    return Panel(Align.left(text), title="Life Scene", border_style="magenta")


def _render_scene(console: Console, router: Router, scene: DemoScene) -> None:
    console.rule(f"[bold cyan]AmiConnect 실제 MVP 처리 화면 · Scene {scene.scene_id}")
    console.print(_scene_panel(scene))

    t0 = time.time()
    # Hide model-loading/debug stdout so the recorded frame stays clean.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = router.route(scene.voice_line, request_id=f"video_{scene.scene_id}")
    latency_ms = (time.time() - t0) * 1000

    grid = Table.grid(expand=True)
    grid.add_column(ratio=3)
    grid.add_column(ratio=2)
    grid.add_row(
        Panel(_decision_table(result, scene, latency_ms), title="MVP Decision", border_style="green"),
        _status_panel(scene, result),
    )
    console.print(grid)
    console.print(Panel(scene.life_result, title="Back to Life Scene", border_style="yellow"))
    console.print()


def _conversation_table(scene: DemoScene) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("speaker", style="cyan", no_wrap=True, width=12)
    table.add_column("line", style="white")
    table.add_row("할머니", f"[bold]\"{scene.wake_word}\"[/bold]")
    table.add_row("AmiConnect", "[bold green]\"네, 말씀하세요.\"[/bold green]")
    table.add_row("할머니", f"[bold]\"{scene.voice_line}\"[/bold]")
    return table


def _compact_decision_table(result: PipelineResult, scene: DemoScene) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("field", style="cyan", no_wrap=True, width=12)
    table.add_column("value", style="white")
    table.add_row("음성 인식", f"[bold]{result.transcript}[/bold]")
    table.add_row("의도", f"[bold green]{result.intent or '(unknown)'}[/bold green]  confidence=[cyan]{result.confidence:.2f}[/cyan]")
    table.add_row("Route", f"[yellow]{result.route}[/yellow]")
    table.add_row("정책", f"[bold yellow]{_policy(result.command, scene.status_policy)}[/bold yellow]")
    table.add_row("실행", _command_summary(result.command))
    return table


def _chat_line(speaker: str, line: str, *, style: str = "white") -> Panel:
    text = Text()
    text.append(f"{speaker}\n", style="bold cyan")
    text.append(line, style=style)
    if speaker == "할머니":
        border = "cyan"
    elif speaker == "AmiConnect":
        border = "green"
    else:
        border = "yellow"
    return Panel(text, border_style=border)


def _render_chat_card(console: Console, router: Router, scene: DemoScene) -> None:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = router.route(scene.voice_line, request_id=f"chat_{scene.scene_id}")

    console.rule(f"[bold cyan]AmiConnect 대화형 캡처 · {scene.title}")
    title = Text()
    title.append("AmiConnect MVP\n", style="bold white")
    title.append(scene.caption, style="white")
    console.print(Panel(title, title=f"Scene {scene.scene_id}", border_style="cyan"))

    console.print(_chat_line("할머니", f'"{scene.wake_word}"', style="bold white"))
    console.print(_chat_line("System", "호출어 감지됨. 음성 입력 대기 상태로 전환합니다.", style="yellow"))
    console.print(_chat_line("AmiConnect", '"네, 말씀하세요."', style="bold green"))
    console.print(_chat_line("할머니", f'"{scene.voice_line}"', style="bold white"))
    console.print(_chat_line("System", "STT 호출: 음성 입력을 텍스트로 변환합니다.", style="yellow"))
    console.print(_chat_line("System", f'인식 결과 불러옴: "{result.transcript}"', style="yellow"))
    console.print(Panel(_compact_decision_table(result, scene), title="실제 MVP 판단", border_style="yellow"))
    console.print(_chat_line("AmiConnect", f'"{result.response_text or result.error or scene.life_result}"', style="bold green"))
    console.print(Panel(scene.life_result, title="적용 결과", border_style="magenta"))


def _render_live_log(console: Console, router: Router, scene: DemoScene) -> None:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = router.route(scene.voice_line, request_id=f"live_{scene.scene_id}")

    command = _command_summary(result.command)
    policy = _policy(result.command, scene.status_policy)
    console.print(f"[bold cyan]AmiConnect MVP live[/bold cyan]  [dim]scene={scene.scene_id} mode=senior_care privacy=on[/dim]")
    console.print()
    console.print(f"[white]user[/white]    [bold]\"{scene.wake_word}\"[/bold]")
    console.print("[dim]system[/dim]  wake word detected")
    console.print("[green]ami[/green]     \"네, 말씀하세요.\"")
    console.print(f"[white]user[/white]    [bold]\"{scene.voice_line}\"[/bold]")
    console.print("[dim]system[/dim]  STT request started")
    console.print(f"[dim]system[/dim]  transcript loaded: [bold white]\"{result.transcript}\"[/bold white]")
    console.print(f"[dim]router[/dim]  intent=[bold green]{result.intent or '(unknown)'}[/bold green] confidence=[cyan]{result.confidence:.2f}[/cyan]")
    console.print(f"[dim]router[/dim]  route=[yellow]{result.route}[/yellow]")
    if result.slots:
        slot_str = ", ".join(f"{k}={v}" for k, v in result.slots.items())
        console.print(f"[dim]router[/dim]  slots={slot_str}")
    console.print(f"[dim]policy[/dim]  [bold yellow]{policy}[/bold yellow]")
    console.print(f"[dim]exec[/dim]    {command}")
    console.print(f"[green]ami[/green]     \"{result.response_text or result.error or scene.life_result}\"")
    console.print(f"[magenta]result[/magenta]  {scene.life_result}")


def _render_large_log(console: Console, router: Router, scene: DemoScene) -> None:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = router.route(scene.voice_line, request_id=f"large_{scene.scene_id}")

    policy = _policy(result.command, scene.status_policy)
    command = _large_action_summary(result.command)
    console.print("[bold cyan]AmiConnect MVP[/bold cyan]  [dim]senior_care · privacy on · local first[/dim]")
    console.print()
    console.print(f"[bold white]user[/bold white]    \"{scene.wake_word}\"")
    console.print("          [cyan]wake word detected[/cyan]  [dim]listening...[/dim]")
    console.print()
    console.print("[bold green]ami[/bold green]     \"네, 말씀하세요.\"")
    console.print()
    console.print(f"[bold white]user[/bold white]    \"{scene.voice_line}\"")
    console.print("          [cyan]STT[/cyan] → [cyan]NLU router[/cyan]")
    console.print()
    console.print("[bold yellow]nlu[/bold yellow]     parsed command")
    console.print(f"          intent  [bold green]{result.intent or '(unknown)'}[/bold green]  [dim]confidence={result.confidence:.2f}[/dim]")
    console.print(f"          route   [yellow]{result.route}[/yellow]")
    console.print(f"          slots   {_large_slot_summary(result)}")
    console.print(f"          policy  [bold yellow]{policy}[/bold yellow]")
    console.print()
    console.print(f"[bold yellow]action[/bold yellow]  {command}")
    console.print()
    console.print(f"[bold green]ami[/bold green]     \"{result.response_text or result.error or scene.life_result}\"")
    console.print()
    console.print(f"[bold magenta]result[/bold magenta]  {scene.life_result}")


def _analysis_panel(result: PipelineResult, scene: DemoScene) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("field", style="cyan", no_wrap=True, width=10)
    table.add_column("value", style="white")
    table.add_row("STT", f"[bold]{result.transcript}[/bold]")
    table.add_row("Intent", f"[bold green]{result.intent or '(unknown)'}[/bold green]")
    table.add_row("Route", f"[yellow]{result.route}[/yellow]")
    table.add_row("Conf.", f"[cyan]{result.confidence:.2f}[/cyan]")
    table.add_row("Slots", _large_slot_summary(result))
    table.add_row("Policy", f"[bold yellow]{_policy(result.command, scene.status_policy)}[/bold yellow]")
    table.add_row("Action", _large_action_summary(result.command))
    return table


def _dialog_panel(result: PipelineResult, scene: DemoScene) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("speaker", style="cyan", no_wrap=True, width=8)
    table.add_column("line", style="white")
    table.add_row("user", f'[bold]"{scene.wake_word}"[/bold]')
    table.add_row("system", "[dim]wake word detected · listening...[/dim]")
    table.add_row("ami", '[bold green]"네, 말씀하세요."[/bold green]')
    table.add_row("user", f'[bold]"{scene.voice_line}"[/bold]')
    table.add_row("system", "[dim]STT → NLU router[/dim]")
    response = result.response_text or result.error or scene.life_result
    if len(response) > 34:
        response = response[:31].rstrip() + "..."
    table.add_row("ami", f'[bold green]"{response}"[/bold green]')
    return table


def _render_split_card(console: Console, router: Router, scene: DemoScene) -> None:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = router.route(scene.voice_line, request_id=f"split_{scene.scene_id}")

    console.rule(f"[bold cyan]AmiConnect MVP · {scene.title}")
    console.print(f"[bold white]{scene.caption}[/bold white]")
    console.print("[dim]senior_care · privacy on · local first[/dim]")
    console.print()

    grid = Table.grid(expand=True)
    grid.add_column(ratio=5)
    grid.add_column(ratio=6)
    grid.add_row(
        Panel(_dialog_panel(result, scene), title="대화", border_style="cyan"),
        Panel(_analysis_panel(result, scene), title="NLU 분석 / 정책 적용", border_style="yellow"),
    )
    console.print(grid)
    console.print(Panel(scene.life_result, title="적용 결과", border_style="magenta"))


def _vertical_analysis_table(result: PipelineResult, scene: DemoScene) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("label", style="cyan", no_wrap=True, width=10)
    table.add_column("value", style="white")
    table.add_row("STT", f"[bold]{result.transcript}[/bold]")
    table.add_row("Intent", f"[bold green]{result.intent or '(unknown)'}[/bold green]")
    table.add_row("Route", f"[yellow]{result.route}[/yellow]")
    table.add_row("Conf.", f"[cyan]{result.confidence:.2f}[/cyan]")
    table.add_row("Slots", _large_slot_summary(result))
    table.add_row("Policy", f"[bold yellow]{_policy(result.command, scene.status_policy)}[/bold yellow]")
    table.add_row("Action", _large_action_summary(result.command))
    return table


def _render_vertical_card(console: Console, router: Router, scene: DemoScene, *, header: bool = True) -> None:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = router.route(scene.voice_line, request_id=f"vertical_{scene.scene_id}")

    if header:
        console.rule(f"[bold cyan]AmiConnect MVP · {scene.title}")
        console.print(f"[bold white]{scene.caption}[/bold white]")
        console.print("[dim]senior_care · privacy on · local first[/dim]")
        console.print()
    else:
        console.print("[dim]listening for wake word...[/dim]")
        console.print()

    console.print(f"[bold white]user[/bold white]    \"{scene.wake_word}\"")
    console.print("          [cyan]wake word detected[/cyan]")
    console.print("[bold green]ami[/bold green]     \"네, 말씀하세요.\"")
    console.print(f"[bold white]user[/bold white]    \"{scene.voice_line}\"")
    console.print("          [cyan]STT → NLU router[/cyan]")
    console.print()
    console.print(Panel(_vertical_analysis_table(result, scene), title="system analysis", border_style="yellow"))
    console.print()
    console.print(f"[bold green]ami[/bold green]     \"{result.response_text or result.error or scene.life_result}\"")
    console.print(f"[bold magenta]result[/bold magenta]  {scene.life_result}")


def _render_image_card(console: Console, router: Router, scene: DemoScene) -> None:
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = router.route(scene.voice_line, request_id=f"image_{scene.scene_id}")
    latency_ms = (time.time() - t0) * 1000

    console.rule(f"[bold cyan]AmiConnect 캡처 카드 · {scene.title}")
    header = Text()
    header.append("AmiConnect MVP\n", style="bold white")
    header.append(scene.caption, style="white")
    console.print(Panel(header, title=f"Scene {scene.scene_id}", border_style="cyan"))

    grid = Table.grid(expand=True)
    grid.add_column(ratio=5)
    grid.add_column(ratio=7)
    grid.add_row(
        Panel(_conversation_table(scene), title="호출어 → 음성 명령", border_style="magenta"),
        Panel(_decision_table(result, scene, latency_ms, show_latency=False), title="실제 MVP 판단", border_style="green"),
    )
    console.print(grid)
    console.print(_status_panel(scene, result))
    console.print(Panel(scene.life_result, title="적용 결과", border_style="yellow"))


def _privacy_intro(console: Console) -> None:
    text = Text()
    text.append("Privacy Mode ON\n", style="bold green")
    text.append("\n민감한 생활 공간의 음성은 외부 LLM으로 전송하지 않습니다.\n", style="white")
    text.append("Local TLM only · Cloud fallback blocked", style="bold red")
    console.print(Panel(Align.center(text), title="Privacy", border_style="green"))


def main() -> None:
    parser = argparse.ArgumentParser(description="OBS-friendly AmiConnect MVP demo runner")
    parser.add_argument("--scene", choices=[s.scene_id for s in SCENES], help="Run only one scene")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between scenes in seconds")
    parser.add_argument("--width", type=int, default=120, help="Console width for OBS capture")
    parser.add_argument("--privacy-intro", action="store_true", help="Show privacy intro before scenes")
    parser.add_argument("--image-card", action="store_true", help="Render still-image-friendly card layout")
    parser.add_argument("--chat-card", action="store_true", help="Render vertical conversation-style screenshot card")
    parser.add_argument("--live-log", action="store_true", help="Render borderless live terminal log for screenshots")
    parser.add_argument("--large-log", action="store_true", help="Render spacious large-font-style screenshot log")
    parser.add_argument("--split-card", action="store_true", help="Render screenshot with dialogue left and analysis right")
    parser.add_argument("--vertical-card", action="store_true", help="Render dialogue first, then analysis below")
    args = parser.parse_args()

    console = Console(width=args.width)
    router = Router(privacy_mode=True)
    default_scene = "01"
    scenes = [s for s in SCENES if args.scene == s.scene_id or (not args.scene and s.scene_id == default_scene)]

    if args.privacy_intro:
        _privacy_intro(console)
        if args.delay:
            time.sleep(args.delay)

    for index, scene in enumerate(scenes):
        if args.vertical_card:
            _render_vertical_card(console, router, scene)
        elif not any((args.image_card, args.chat_card, args.live_log, args.large_log, args.split_card)):
            _render_vertical_card(console, router, scene, header=False)
        elif args.split_card:
            _render_split_card(console, router, scene)
        elif args.large_log:
            _render_large_log(console, router, scene)
        elif args.live_log:
            _render_live_log(console, router, scene)
        elif args.chat_card:
            _render_chat_card(console, router, scene)
        elif args.image_card:
            _render_image_card(console, router, scene)
        else:
            _render_scene(console, router, scene)
        if args.delay and index < len(scenes) - 1:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
