"""Mindlogic API Gateway NLU fallback.

Uses the OpenAI-compatible Chat Completions endpoint:
https://factchat-cloud.mindlogic.ai/v1/gateway/chat/completions/
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


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

Return compact valid JSON only. No markdown.
"""


@dataclass
class GatewayOutput:
    intent: str
    slots: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    rationale: str = ""
    command: dict[str, Any] = field(default_factory=dict)
    response_text: str = ""
    raw: str = ""


class GatewayNLU:
    def __init__(self, model: str | None = None) -> None:
        api_key = os.environ.get("FACTCHAT_API_KEY") or os.environ.get("MINDLOGIC_API_KEY")
        if not api_key:
            raise RuntimeError("FACTCHAT_API_KEY is not set")
        self.api_key = api_key
        self.base_url = os.environ.get("FACTCHAT_BASE_URL", "https://factchat-cloud.mindlogic.ai/v1/gateway").rstrip("/")
        self.model = model or os.environ.get("FACTCHAT_MODEL", "gemini-3.1-flash-lite-preview")
        self.timeout = float(os.environ.get("FACTCHAT_TIMEOUT_SECONDS", "30"))

    def parse(self, text: str) -> GatewayOutput:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f'발화: "{text}"'},
            ],
            "temperature": 0.0,
            "max_tokens": 320,
            "response_format": {"type": "json_object"},
        }
        data = self._post_json("/chat/completions/", payload)
        raw = self._message_content(data)
        parsed = self._parse_json(raw)
        return GatewayOutput(
            intent=parsed.get("intent", "unknown"),
            slots=parsed.get("slots") or {},
            confidence=float(parsed.get("confidence") or 0.0),
            rationale=parsed.get("rationale", ""),
            command=parsed.get("command") or {},
            response_text=parsed.get("response_text", ""),
            raw=raw,
        )

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "AmiConnect-MVP/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gateway HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gateway request failed: {exc.reason}") from exc

    @staticmethod
    def _message_content(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            return "{}"
        message = choices[0].get("message") or {}
        content = message.get("content") or "{}"
        if isinstance(content, list):
            return "".join(str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in content)
        return str(content)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"intent": "unknown", "raw": raw}
