"""Read/write demo medication schedule and return Korean response_text."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_PATH = _REPO_ROOT / "data/demo/medication_schedule.json"


def _parse_time_to_min(t: str) -> int | None:
    """'09:00' 또는 '오전 9시' 형식을 분 단위로 변환. 파싱 불가 시 None."""
    import re
    t = t.strip()
    # HH:MM 형식
    if re.match(r"^\d{1,2}:\d{2}$", t):
        h, m = map(int, t.split(":"))
        return h * 60 + m
    # 오전/오후 N시 형식
    m = re.match(r"(오전|오후)?\s*(\d{1,2})\s*시", t)
    if m:
        ampm, hour = m.group(1), int(m.group(2))
        if ampm == "오후" and hour < 12:
            hour += 12
        if ampm == "오전" and hour == 12:
            hour = 0
        return hour * 60
    return None


def save_medication_schedule(medication: str, time_val: str) -> None:
    """Add or update a medication entry in the schedule file."""
    if not SCHEDULE_PATH.exists():
        data: dict = {"patient": "어르신", "medications": []}
    else:
        data = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))

    # 같은 약 이름이 있으면 시간 업데이트, 없으면 추가
    for med in data["medications"]:
        if med["name"] == medication:
            if time_val and time_val not in med["times"]:
                med["times"].append(time_val)
            break
    else:
        data["medications"].append({
            "name": medication,
            "times": [time_val] if time_val else [],
            "with_meal": "식후" in time_val or "식전" in time_val,
            "note": time_val if time_val else None,
        })

    SCHEDULE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_medication_response(medication: str | None = None) -> str:
    if not SCHEDULE_PATH.exists():
        return "복약 일정 파일을 찾을 수 없어요."

    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    now = datetime.now()
    now_min = now.hour * 60 + now.minute

    upcoming: list[tuple[int, str, str]] = []  # (diff_min, med_name, time_str)

    for med in schedule["medications"]:
        # 특정 약 이름이 주어진 경우 해당 약만 필터링
        if medication and medication not in med["name"] and med["name"] not in medication:
            continue
        for t in med["times"]:
            med_min = _parse_time_to_min(t)
            if med_min is None:
                continue
            diff = med_min - now_min
            if diff < -30:
                diff += 24 * 60
            upcoming.append((diff, med["name"], t, med.get("note")))

    if not upcoming:
        if medication:
            return f"{medication} 복약 일정이 등록되어 있지 않아요."
        return "등록된 복약 일정이 없어요."

    upcoming.sort(key=lambda x: x[0])
    diff, name, t, note = upcoming[0]

    note_str = f" {note}에 드세요." if note else ""

    if diff < 0:
        return f"{t}에 {name} 드셨어야 했어요. 지금이라도 드세요."
    elif diff == 0:
        return f"지금 {name} 드실 시간이에요!{note_str}"
    elif diff <= 30:
        return f"{name} 드실 시간이 {diff}분 남았어요.{note_str}"
    else:
        h = diff // 60
        m = diff % 60
        time_str = f"{h}시간 {m}분" if h else f"{m}분"
        return f"다음 복약은 {t}에 {name}이에요. {time_str} 남았어요."
