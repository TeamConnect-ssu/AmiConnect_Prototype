"""Evaluate the fine-tuned KoMiniLM NLU checkpoint on a JSONL validation set."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.tlm.infer import KoMiniLMTLM


def load_cases(path: Path) -> list[dict]:
    cases: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def slot_dict(case: dict) -> dict[str, str]:
    return {slot["slot_type"]: slot["slot_value"] for slot in case.get("slots", [])}


def normalize_slot_value(value: str) -> str:
    return " ".join(str(value).split())


def slot_entities(slots: dict[str, str]) -> set[tuple[str, str]]:
    return {(slot_type, normalize_slot_value(value)) for slot_type, value in slots.items()}


def safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, round((len(ordered) - 1) * p))
    return ordered[idx]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        default="data/processed/valid.jsonl",
        help="Validation JSONL path with text, intent, slots fields.",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    cases = load_cases(data_path)
    if not cases:
        raise SystemExit(f"No cases found: {data_path}")

    model = KoMiniLMTLM()

    # Exclude model load and tokenizer warm-up from latency measurement.
    model.predict(cases[0]["text"], build_command=False)

    latencies_ms: list[float] = []
    intent_ok = 0
    slot_ok = 0
    joint_ok = 0
    slot_tp = 0
    slot_pred_total = 0
    slot_gold_total = 0

    for case in cases:
        started = time.perf_counter()
        pred = model.predict(case["text"], build_command=False)
        latencies_ms.append((time.perf_counter() - started) * 1000)

        expected_intent = case["intent"]
        expected_slots = slot_dict(case)
        expected_entities = slot_entities(expected_slots)
        predicted_entities = slot_entities(pred.slots)
        got_intent = pred.intent == expected_intent
        got_slots = pred.slots == expected_slots

        intent_ok += int(got_intent)
        slot_ok += int(got_slots)
        joint_ok += int(got_intent and got_slots)
        slot_tp += len(expected_entities & predicted_entities)
        slot_pred_total += len(predicted_entities)
        slot_gold_total += len(expected_entities)

    total = len(cases)
    slot_precision = safe_div(slot_tp, slot_pred_total)
    slot_recall = safe_div(slot_tp, slot_gold_total)
    slot_f1 = safe_div(2 * slot_tp, slot_pred_total + slot_gold_total)
    metrics = {
        "dataset": str(data_path),
        "cases": total,
        "intent_accuracy": intent_ok / total,
        "slot_entity": {
            "true_positive": slot_tp,
            "predicted": slot_pred_total,
            "gold": slot_gold_total,
            "precision": slot_precision,
            "recall": slot_recall,
            "f1": slot_f1,
        },
        "slot_exact_match": slot_ok / total,
        "joint_exact_match": joint_ok / total,
        "latency_ms": {
            "mean": statistics.fmean(latencies_ms),
            "p50": statistics.median(latencies_ms),
            "p95": percentile(latencies_ms, 0.95),
            "max": max(latencies_ms),
        },
    }

    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
