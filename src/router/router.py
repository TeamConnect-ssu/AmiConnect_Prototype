"""Route between local KoMiniLM/RuleTLM and Mindlogic Gateway cloud NLU."""
from __future__ import annotations

import os

from pathlib import Path

from src.schema import PipelineResult
from src.tlm.infer import KoMiniLMTLM, RuleTLM

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FINETUNED_MODEL = _REPO_ROOT / "models/tlm/kominilm-finetuned/model.pt"


class Router:
    def __init__(self, privacy_mode: bool | None = None) -> None:
        self.local = None
        env_privacy = os.environ.get("AMICONNECT_PRIVACY_MODE", "false").lower() == "true"
        self.privacy_mode = privacy_mode if privacy_mode is not None else env_privacy
        self.local_confidence_threshold = float(
            os.environ.get("AMICONNECT_LOCAL_CONFIDENCE_THRESHOLD", "0.65")
        )
        self._cloud = None

    def _ensure_local(self):
        if self.local is None:
            if _FINETUNED_MODEL.exists():
                self.local = KoMiniLMTLM()
                print("[Router] KoMiniLMTLM 로드")
            else:
                self.local = RuleTLM()
                print("[Router] RuleTLM 사용 (학습 모델 없음)")
        return self.local

    @property
    def cloud(self):
        if self._cloud is None:
            from src.cloud_llm.gateway import GatewayNLU
            self._cloud = GatewayNLU()
        return self._cloud

    def route(self, text: str, request_id: str = "") -> PipelineResult:
        result = PipelineResult(request_id=request_id, transcript=text)

        # Privacy mode: never call cloud
        if self.privacy_mode:
            local = self._ensure_local().predict(text)
            if local.intent == "unknown" or local.confidence < self.local_confidence_threshold:
                result.error = "복합 명령은 지금 처리할 수 없습니다 (privacy mode)"
                result.route = "privacy_fallback"
                result.confidence = local.confidence
                result.model = local.source
                return result
            return self._from_tlm(result, local)

        # Try local model first; use Gateway only when local confidence is low.
        local = self._ensure_local().predict(text)
        if local.intent != "unknown" and local.confidence >= self.local_confidence_threshold:
            return self._from_tlm(result, local)

        # Fallback to Gateway for general unknown input
        return self._call_cloud(result)

    def _from_tlm(self, result: PipelineResult, tlm) -> PipelineResult:
        result.intent = tlm.intent
        result.slots = tlm.slots
        result.route = "KoMiniLM" if tlm.source == "kominilm" else "RuleTLM"
        result.confidence = tlm.confidence
        result.model = tlm.source
        result.command = tlm.command
        result.response_text = tlm.response_text
        return result

    def _call_cloud(self, result: PipelineResult) -> PipelineResult:
        try:
            cloud = self.cloud.parse(result.transcript)
        except Exception as exc:
            result.route = "Gateway"
            result.error = f"LLM 호출 실패: {exc}"
            result.response_text = "LLM 호출 설정을 확인해 주세요."
            return result
        result.intent = cloud.intent
        result.slots = cloud.slots
        result.route = "Gateway"
        result.confidence = cloud.confidence
        result.model = "gemini-3.1-flash-lite-preview"
        result.command = cloud.command
        result.response_text = cloud.response_text
        result.error = "" if cloud.intent != "unknown" else "LLM could not parse intent"
        return result
