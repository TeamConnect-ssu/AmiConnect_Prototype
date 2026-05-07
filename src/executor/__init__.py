"""Mock executor — prints command to console; real IFTTT/Hue plugs in here."""
from __future__ import annotations

from typing import Any

from rich.console import Console

_console = Console()


def execute(command: dict[str, Any], *, dry_run: bool = False) -> bool:
    action = command.get("action", "?")
    target = command.get("target", "?")
    params = command.get("params", {})
    policy = command.get("policy_applied")

    label = f"[EXEC] {target} ← {action} {params}"
    if policy:
        label += f"  (policy: {policy})"

    if dry_run:
        _console.print(f"[dim]{label}[/dim]")
    else:
        _console.print(f"[bold yellow]{label}[/bold yellow]")

    return True
