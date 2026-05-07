"""TLM inference: RuleTLM (regex fallback) and KoMiniLMTLM (fine-tuned model).

KoMiniLMTLM — loads MultiTaskModelWithCRF from models/tlm/kominilm-finetuned.
               Intent + slots both come from the model (no regex for slots).
RuleTLM      — used only when fine-tuned model is unavailable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class TLMOutput:
    intent: str
    slots: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    source: str = "rule"     # rule | kominilm
    command: dict[str, Any] = field(default_factory=dict)
    response_text: str = ""


# ── RuleTLM (regex fallback) ──────────────────────────────────────────────────

_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("emergency_call",          re.compile(r"(도와줘|살려|응급|119)")),
    ("set_medication_schedule", re.compile(r"(할아버지|할머니|어르신|아버지|어머니).*(약|비타민|영양제).*(먹|드)")),
    ("medication_reminder",     re.compile(r"(약|혈압약|영양제|비타민|수면제|진통제|당뇨약).*(언제|시간|먹|드)")),
    ("set_brightness",          re.compile(r"(불|조명).*(약하|밝|세게|\d+\s*%|퍼센트)")),
    ("turn_off",                re.compile(r"(불|조명|에어컨|TV|티비|선풍기).*(꺼|꺼줘|꺼라|끄|멈춰)")),
    ("turn_on",                 re.compile(r"(불|조명|에어컨|TV|티비|선풍기).*(켜|켜줘|켜라|키주|키줘|틀어)")),
    ("set_temperature",         re.compile(r"(에어컨|난방|온도).*(\d+\s*도|올려|내려|높여|낮춰)|(추워|더워)")),
    ("weather_query",           re.compile(r"(날씨|오늘\s*추워|추워\?|내일\s*추워|비|눈|기온)")),
    ("time_query",              re.compile(r"(몇\s*시|지금\s*시간|오늘\s*날짜)")),
    ("ambient_mode",            re.compile(r"(자기\s*전|취침|수면|아침\s*모드|영화\s*모드|분위기|환기)")),
]

_PATIENT    = re.compile(r"(할아버지|할머니|어르신|아버지|어머니|아빠|엄마)")
_MEDICATION = re.compile(r"(혈압약|당뇨약|비타민[A-Dd]?|수면제|진통제|영양제|아스피린|[가-힣]+약)")
_MED_TIME   = re.compile(r"(오전\s*\d+시|오후\s*\d+시|아침|점심|저녁|식전|식후|자기\s*전|\d+시)")
_LOCATION   = re.compile(r"(거실|안방|방|침실|주방|화장실|현관)")
_LEVEL      = re.compile(r"(약하게|세게|밝게|어둡게|\d+\s*%|\d+\s*퍼센트)")
_STATE_ON   = re.compile(r"(켜|켜줘|켜라|키주|키줘)")
_TEMP       = re.compile(r"(\d+)\s*도")

_LOCATION_TARGET: dict[str, str] = {
    "거실": "light.living_room",
    "안방": "light.bedroom",
    "방":   "light.bedroom",
    "침실": "light.bedroom",
    "주방": "light.kitchen",
    "화장실": "light.bathroom",
    "현관": "light.entrance",
}


class RuleTLM:
    def predict(self, text: str) -> TLMOutput:
        text = text.strip()
        for intent, pat in _RULES:
            if pat.search(text):
                slots = self._extract_slots(intent, text)
                command, response_text = self._build_command(intent, slots, text)
                return TLMOutput(intent=intent, slots=slots, confidence=0.7,
                                 source="rule", command=command, response_text=response_text)
        return TLMOutput(intent="unknown", slots={}, confidence=0.0)

    def _extract_slots(self, intent: str, text: str) -> dict[str, str]:
        slots: dict[str, str] = {}
        if loc := _LOCATION.search(text):
            slots["location"] = loc.group(0)
        if intent == "set_brightness":
            if lvl := _LEVEL.search(text):
                slots["level"] = lvl.group(0)
        if intent == "set_temperature":
            if t := _TEMP.search(text):
                slots["value"] = t.group(1)
        if intent in ("set_medication_schedule", "medication_reminder"):
            if p := _PATIENT.search(text):
                slots["patient"] = p.group(0)
            if med := _MEDICATION.search(text):
                slots["medication"] = med.group(0)
            if t := _MED_TIME.search(text):
                slots["time"] = t.group(0).strip()
        return slots

    def _build_command(self, intent: str, slots: dict[str, str], text: str) -> tuple[dict[str, Any], str]:
        return _build_command(intent, slots, text)


# ── Shared command builder ────────────────────────────────────────────────────

def _build_command(intent: str, slots: dict[str, str], text: str) -> tuple[dict[str, Any], str]:  # noqa: C901
    loc = slots.get("location", "")
    light_target = _LOCATION_TARGET.get(loc, f"light.{loc}" if loc else "light.living_room")

    if intent == "turn_on":
        return (
            {"action": "turn_on", "target": light_target,
             "params": {"brightness_pct": 80}, "policy_applied": None},
            f"{loc or '거실'} 불 켰어요.",
        )

    if intent == "turn_off":
        return (
            {"action": "set_brightness", "target": light_target,
             "params": {"brightness_pct": 20}, "policy_applied": "senior_care.min_brightness",
             "rationale": "낙상 방지 최소 조도 20% 유지"},
            f"{loc or '거실'} 불을 약하게 줄였어요. 어두워서 넘어지지 않으시도록요.",
        )

    if intent == "set_brightness":
        level_str = slots.get("level", "약하게")
        pct = 30 if "약하" in level_str else 70
        if m := re.search(r"(\d+)", level_str):
            pct = max(20, int(m.group(1)))
        direction = "약하게" if pct <= 40 else "밝게"
        return (
            {"action": "set_brightness", "target": light_target,
             "params": {"brightness_pct": pct}, "policy_applied": None},
            f"{loc or '방'} 불을 {direction} 했어요.",
        )

    if intent == "medication_reminder":
        from src.data_providers.medication import get_medication_response
        medication = slots.get("medication")
        return (
            {"action": "query_medication_schedule", "target": "scheduler.medication",
             "params": {"query_type": "next_or_now", "medication": medication},
             "policy_applied": "senior_care.medication_enabled"},
            get_medication_response(medication),
        )

    if intent == "emergency_call":
        return (
            {"action": "trigger_emergency", "target": "notification.caregiver",
             "params": {"priority": "high", "include_location": True},
             "policy_applied": "senior_care.emergency"},
            "보호자에게 알렸어요. 곧 도와드리러 와요. 그 자리에 가만히 계세요.",
        )

    if intent == "set_temperature":
        delta = 2
        return (
            {"action": "adjust_temperature", "target": "climate.bedroom",
             "params": {"delta": delta, "unit": "celsius"},
             "policy_applied": "senior_care.suggest_warmth_aid"},
            f"방 온도를 {delta}도 올렸어요. 보온 매트도 켜드릴까요?",
        )

    if intent == "set_medication_schedule":
        from src.data_providers.medication import save_medication_schedule
        medication = slots.get("medication", "약")
        time_val = slots.get("time", "")
        patient = slots.get("patient", "어르신")
        save_medication_schedule(medication, time_val)
        time_msg = f" {time_val}에" if time_val else ""
        return (
            {"action": "update_medication_schedule", "target": "scheduler.medication",
             "params": {"patient": patient, "medication": medication, "time": time_val},
             "policy_applied": "senior_care.medication_enabled"},
            f"알겠어요. {patient}{time_msg} {medication} 드시는 걸로 저장했어요.",
        )

    if intent == "weather_query":
        from src.data_providers.weather import get_weather_response
        return (
            {"action": "query_weather", "target": "weather.local",
             "params": {"date": "today", "attributes": ["temperature", "feels_like"]},
             "policy_applied": "senior_care.appended_advice"},
            get_weather_response(),
        )

    if intent == "time_query":
        now = datetime.now()
        ampm = "오전" if now.hour < 12 else "오후"
        h = now.hour if now.hour <= 12 else now.hour - 12
        m_str = f" {now.minute}분" if now.minute else ""
        return (
            {"action": "query_time", "target": "system.clock",
             "params": {"format": "korean_speech"}, "policy_applied": None},
            f"지금 {ampm} {h}시{m_str}이에요.",
        )

    if intent == "ambient_mode":
        return (
            {"action": "execute_scene", "target": "scene.composite",
             "params": {"steps": [
                 {"action": "set_brightness", "target": "light.bedroom", "params": {"brightness_pct": 20}},
                 {"action": "set_color_temperature", "target": "light.bedroom", "params": {"kelvin": 2200}},
                 {"action": "set_mode", "target": "system", "params": {"mode": "night"}},
             ]},
             "policy_applied": "senior_care.bedtime_scene"},
            "주무실 준비를 해드렸어요. 불은 살짝만 남겨두고, 따뜻한 색으로 바꿨어요.",
        )

    return {}, ""


# ── KoMiniLMTLM ───────────────────────────────────────────────────────────────

class KoMiniLMTLM:
    """Fine-tuned MultiTaskModelWithCRF: intent + slots both from the model."""

    MODEL_PATH = _REPO_ROOT / "models/tlm/kominilm-finetuned"

    def __init__(self) -> None:
        import json
        from transformers import AutoTokenizer
        from src.tlm.model import MultiTaskModelWithCRF, ID2INTENT, ID2SLOT

        mappings_path = self.MODEL_PATH / "label_mappings.json"
        mappings = json.loads(mappings_path.read_text(encoding="utf-8"))
        self._id2intent = {int(k): v for k, v in mappings["id2intent"].items()}
        self._id2slot = {int(k): v for k, v in mappings["id2slot"].items()}

        self._tokenizer = AutoTokenizer.from_pretrained(MultiTaskModelWithCRF.BASE_MODEL)
        self._model = MultiTaskModelWithCRF.load(str(self.MODEL_PATH))

    def predict(self, text: str) -> TLMOutput:
        import torch

        enc = self._tokenizer(
            text.strip(),
            max_length=64,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
            return_offsets_mapping=True,
        )
        input_ids = enc["input_ids"]
        attention_mask = enc["attention_mask"]
        offset_mapping = enc["offset_mapping"][0].tolist()

        with torch.no_grad():
            out = self._model(input_ids, attention_mask)

        # Intent
        probs = torch.softmax(out["intent_logits"], dim=-1)
        confidence = float(probs.max())
        intent = self._id2intent[int(probs.argmax())]

        # Slots via CRF decode
        slot_pred_ids = self._model.predict_slots(out["slot_logits"], attention_mask)[0]
        slots = self._decode_slots(text, slot_pred_ids, offset_mapping, attention_mask[0])

        command, response_text = _build_command(intent, slots, text)

        return TLMOutput(
            intent=intent,
            slots=slots,
            confidence=confidence,
            source="kominilm",
            command=command,
            response_text=response_text,
        )

    def _decode_slots(
        self,
        text: str,
        pred_ids: list[int],
        offset_mapping: list[tuple[int, int]],
        attention_mask,
    ) -> dict[str, str]:
        """Convert BIO predictions back to {slot_type: slot_value} dict."""
        slots: dict[str, str] = {}
        seq_len = int(attention_mask.sum().item())
        current_type: str | None = None
        current_start = current_end = 0

        for i in range(seq_len):
            label = self._id2slot.get(pred_ids[i], "O")
            tok_s, tok_e = offset_mapping[i]
            if tok_s == 0 and tok_e == 0:
                current_type = None
                continue

            if label.startswith("B-"):
                current_type = label[2:]
                current_start, current_end = tok_s, tok_e
            elif label.startswith("I-") and current_type == label[2:]:
                current_end = tok_e
            else:
                if current_type:
                    slots[current_type] = text[current_start:current_end]
                current_type = None
                if label.startswith("B-"):
                    current_type = label[2:]
                    current_start, current_end = tok_s, tok_e

        if current_type:
            slots[current_type] = text[current_start:current_end]

        return slots
