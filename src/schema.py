"""Common pipeline output schema (MVP_TEAM_GUIDE §2)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineResult:
    request_id: str = ""
    transcript: str = ""
    intent: str = ""
    slots: dict[str, str] = field(default_factory=dict)
    route: str = ""          # rule | llm | privacy_fallback
    command: dict[str, Any] = field(default_factory=dict)
    response_text: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "transcript": self.transcript,
            "intent": self.intent,
            "slots": self.slots,
            "route": self.route,
            "command": self.command,
            "response_text": self.response_text,
            "error": self.error,
        }
