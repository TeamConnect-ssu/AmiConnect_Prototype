"""KoMiniLM multi-task model: intent classification + slot filling (BIO + CRF)."""
from __future__ import annotations

import json
from pathlib import Path

import torch
import torch.nn as nn
from transformers import AutoModel
from torchcrf import CRF


INTENTS = [
    "ambient_mode",
    "emergency_call",
    "medication_reminder",
    "set_brightness",
    "set_medication_schedule",
    "set_temperature",
    "time_query",
    "turn_off",
    "turn_on",
    "weather_query",
]

INTENT2ID = {intent: i for i, intent in enumerate(INTENTS)}
ID2INTENT = {i: intent for i, intent in enumerate(INTENTS)}

# BIO label space built from 9 slot types
_SLOT_TYPES = [
    "attribute", "device", "level", "location",
    "medication", "mode", "patient", "time", "value",
]
SLOT_LABELS = ["O"] + [f"B-{t}" for t in _SLOT_TYPES] + [f"I-{t}" for t in _SLOT_TYPES]
SLOT2ID = {label: i for i, label in enumerate(SLOT_LABELS)}
ID2SLOT = {i: label for i, label in enumerate(SLOT_LABELS)}


class MultiTaskModelWithCRF(nn.Module):
    """Intent classification head + slot filling head with CRF (BIO tagging)."""

    BASE_MODEL = "BM-K/KoMiniLM"

    def __init__(
        self,
        num_intents: int = len(INTENTS),
        num_slot_labels: int = len(SLOT_LABELS),
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.encoder = AutoModel.from_pretrained(self.BASE_MODEL)
        hidden = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.intent_classifier = nn.Linear(hidden, num_intents)
        self.slot_classifier = nn.Linear(hidden, num_slot_labels)
        self.crf = CRF(num_slot_labels, batch_first=True)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        intent_labels: torch.Tensor | None = None,
        slot_labels: torch.Tensor | None = None,
    ) -> dict:
        out = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )
        seq = self.dropout(out.last_hidden_state)   # (B, L, H)
        cls = self.dropout(out.last_hidden_state[:, 0, :])  # (B, H)

        intent_logits = self.intent_classifier(cls)   # (B, num_intents)
        slot_logits = self.slot_classifier(seq)        # (B, L, num_slot_labels)

        result: dict = {"intent_logits": intent_logits, "slot_logits": slot_logits}

        if intent_labels is not None and slot_labels is not None:
            result["intent_loss"] = nn.CrossEntropyLoss()(intent_logits, intent_labels)
            slot_mask = attention_mask.bool()
            result["slot_loss"] = -self.crf(slot_logits, slot_labels, mask=slot_mask, reduction="mean")

        return result

    def predict_slots(
        self, slot_logits: torch.Tensor, attention_mask: torch.Tensor
    ) -> list[list[int]]:
        return self.crf.decode(slot_logits, mask=attention_mask.bool())

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path / "model.pt")
        self.encoder.config.save_pretrained(path)
        mappings = {
            "intent2id": INTENT2ID,
            "id2intent": {str(k): v for k, v in ID2INTENT.items()},
            "slot2id": SLOT2ID,
            "id2slot": {str(k): v for k, v in ID2SLOT.items()},
        }
        (path / "label_mappings.json").write_text(
            json.dumps(mappings, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str | Path) -> "MultiTaskModelWithCRF":
        path = Path(path)
        mappings = json.loads((path / "label_mappings.json").read_text(encoding="utf-8"))
        num_intents = len(mappings["intent2id"])
        num_slot_labels = len(mappings["slot2id"])
        model = cls(num_intents=num_intents, num_slot_labels=num_slot_labels)
        model.load_state_dict(torch.load(path / "model.pt", map_location="cpu"))
        model.eval()
        return model
