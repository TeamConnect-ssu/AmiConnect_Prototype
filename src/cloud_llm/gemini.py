"""Gemini Flash-Lite NLU — extracts intent + slots + command + response_text."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types


SYSTEM_PROMPT = """You are a smart-home voice command understanding specialist.
Rephrase the Korean command internally, then return JSON only.

Task: map senior-care smart-home utterances to intent, slots, command, response_text.
Valid intent: ambient_mode or unknown.
Output fields: intent, slots, confidence, rationale, command, response_text.

Policy:
- For bedtime/sleep/night mood, never turn lights off. Keep bedroom light at 20%, warm color 2200K, and set night mode.
- For stuffy/ventilation requests, run a 10-minute air refresh scene.
- Do not control devices the user did not mention except system night mode for bedtime.

Examples:
Command: "잠자리 모드로 해줘"
JSON: {"intent":"ambient_mode","slots":{"mode":"자기 전"},"confidence":0.95,"rationale":"취침 분위기 요청","command":{"action":"execute_scene","target":"scene.composite","params":{"steps":[{"action":"set_brightness","target":"light.bedroom","params":{"brightness_pct":20}},{"action":"set_color_temperature","target":"light.bedroom","params":{"kelvin":2200}},{"action":"set_mode","target":"system","params":{"mode":"night"}}]},"policy_applied":"senior_care.bedtime_scene"},"response_text":"주무실 준비를 해드렸어요. 불은 살짝만 남기고 따뜻한 색으로 바꿨어요."}

Command: "환기 좀 해줘"
JSON: {"intent":"ambient_mode","slots":{"mode":"환기"},"confidence":0.95,"rationale":"환기 장면 요청","command":{"action":"execute_scene","target":"scene.ventilation","params":{"mode":"air_refresh","duration_min":10},"policy_applied":"senior_care.ventilation_scene"},"response_text":"네, 10분 동안 환기 모드로 바꿔드릴게요."}

Command: "{INPUT}"
Read the command again: "{INPUT}"
Return compact valid JSON only. No markdown.
"""


@dataclass
class GeminiOutput:
    intent: str
    slots: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    rationale: str = ""
    command: dict[str, Any] = field(default_factory=dict)
    response_text: str = ""
    raw: str = ""


class GeminiNLU:
    def __init__(self, model: str | None = None) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=api_key)
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

    def parse(self, text: str) -> GeminiOutput:
        resp = self.client.models.generate_content(
            model=self.model,
            contents=[f"발화: {text}"],
            config=types.GenerateContentConfig(
                systemInstruction=SYSTEM_PROMPT,
                responseMimeType="application/json",
                temperature=0.0,
                maxOutputTokens=320,
                thinkingConfig=types.ThinkingConfig(thinkingBudget=0),
            ),
        )
        raw = resp.text or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return GeminiOutput(intent="unknown", raw=raw)
        return GeminiOutput(
            intent=data.get("intent", "unknown"),
            slots=data.get("slots") or {},
            confidence=float(data.get("confidence") or 0.0),
            rationale=data.get("rationale", ""),
            command=data.get("command") or {},
            response_text=data.get("response_text", ""),
            raw=raw,
        )
