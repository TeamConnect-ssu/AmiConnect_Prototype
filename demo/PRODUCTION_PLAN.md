# AmiConnect Demo Video Production Plan

## Goal

제출용 MVP 영상을 만든다. 완성도 기준은 "시니어케어 정책과 프라이버시 모드가 이해되고, 실제 MVP가 돌아간다는 점이 보이는 영상"이다.

확정 스택:

| 작업 | 툴 |
|---|---|
| 생활 장면 AI 영상 | Kling 우선, Runway 보조 |
| 한국어 AI 음성 | Typecast 우선, CLOVA Dubbing 백업 |
| 터미널 녹화 | OBS |
| 한국어 자막 정리 | Vrew |
| 최종 편집 | CapCut |
| 실제 MVP 화면 | `demo/video_demo_runner.py` |

## Phase 1. Script Lock

먼저 음성 대사를 잠근다. 이 단계 이후에는 문장을 바꾸지 않는다.

할머니 명령:

```text
동구야.
동구야, 거실 불 꺼줘.
동구야, 약 먹을 시간 됐나?
동구야, 추워.
동구야, 도와줘.
동구야, 자기 전 분위기로 해줘.
```

AmiConnect 응답:

```text
거실 불을 약하게 줄였어요. 어두워서 넘어지지 않으시도록요.
혈압약은 30분 뒤인 오전 9시에 드시면 돼요.
방 온도를 2도 올렸어요. 보온 매트도 켜드릴까요?
보호자에게 알렸어요. 곧 도와드리러 와요. 그 자리에 가만히 계세요.
주무실 준비를 해드렸어요. 불은 살짝만 남겨두고, 따뜻한 색으로 바꿨어요.
```

내레이션:

```text
혼자 있는 시간이 길어진 집.
하지만 할머니에게는 아직 익숙한 이름 하나가 남아 있습니다.

동구.

예전에 곁을 지켜주던 이름.
이제 AmiConnect는 그 이름으로,
할머니의 일상을 조용히 돕습니다.
```

프라이버시 내레이션:

```text
민감한 생활 공간의 음성은, 밖으로 나가지 않아야 하니까.
프라이버시 모드에서는 외부 LLM 호출을 차단하고,
핵심 돌봄 명령은 로컬에서 처리합니다.
```

엔딩:

```text
AmiConnect는 명령을 그대로 실행하지 않습니다.
시니어케어 환경에서는 안전과 프라이버시를 먼저 생각합니다.

동구야, 오늘도 곁에 있어줘.
```

## Phase 2. Voice Production

Typecast에서 한국어 어르신 여성 음성을 고른다. 실제 사람 목소리 복제는 사용하지 않는다.

작업 순서:

1. 할머니 명령 6개를 생성한다.
2. AmiConnect 응답 5개를 생성한다.
3. 내레이션 3개를 생성한다.
4. 문장마다 2-3개 버전을 뽑고 가장 자연스러운 것을 선택한다.
5. `demo/assets/voice/`에 파일명 규칙대로 저장한다.

파일명:

```text
01_grandma_wake_donggu.wav
02_grandma_living_light_off.wav
03_ai_living_light_response.wav
04_grandma_medication.wav
05_ai_medication_response.wav
06_grandma_cold.wav
07_ai_temperature_response.wav
08_grandma_help.wav
09_ai_emergency_response.wav
10_grandma_bedtime.wav
11_ai_bedtime_response.wav
12_narration_opening.wav
13_narration_privacy.wav
14_narration_ending.wav
```

품질 기준:

- 할머니 음성은 느리지만 과하게 힘없지 않아야 한다.
- AmiConnect 응답은 따뜻하고 또박또박해야 한다.
- 한국어 억양이 어색하면 CLOVA Dubbing으로 같은 대사를 백업 생성한다.

## Phase 3. AI Video Clip Production

Kling에서 기준 이미지를 먼저 만들고, 그 이미지를 이용해 장면별 5-10초 영상을 만든다.

중요 규칙:

- 영상 생성 프롬프트는 영어로 작성한다.
- 한국어 글자는 AI 영상에 직접 생성하지 않는다.
- 한국어 UI, 알림, 자막은 Vrew/CapCut에서 직접 오버레이한다.
- 한 번에 긴 영상을 만들지 않는다.

필수 클립:

| 파일명 | 내용 |
|---|---|
| `01_opening_living_room.mp4` | 조용한 거실 오프닝 |
| `02_donggu_photo.mp4` | 동구 사진/이름표 클로즈업 |
| `03_living_light_command.mp4` | 거실 불 꺼줘 장면 |
| `04_living_light_result.mp4` | 조명 20% 유지 결과 |
| `05_medication_command.mp4` | 약통/복약 질문 장면 |
| `06_medication_result.mp4` | 복약 안내 결과 |
| `07_cold_command.mp4` | 추워 장면 |
| `08_cold_result.mp4` | 온도 상승/보온 매트 제안 장면 |
| `09_emergency_command.mp4` | 도와줘 장면 |
| `10_emergency_notification.mp4` | 보호자 휴대폰 알림 |
| `11_bedtime_command.mp4` | 자기 전 분위기 명령 |
| `12_bedtime_result.mp4` | 따뜻한 조명/야간 모드 |
| `13_privacy_mode.mp4` | Privacy Mode ON 그래픽 |
| `14_ending.mp4` | 엔딩 장면 |

## Phase 4. Terminal Recording

OBS로 실제 MVP 판단 화면을 녹화한다.

이미지 캡처용 3장:

```bash
python demo/mvp_runner_dongu.py
python demo/mvp_runner_prugio.py
```

`mvp_runner_dongu.py`는 동구 호출어 장면 2개를 실제 세션처럼 연속 실행한다.
위쪽은 조명 안전 디밍 캡처, 아래쪽은 긴급 도움 요청 캡처로 나눠 찍는다.
`mvp_runner_prugio.py`는 푸르지오 호출어 장면 1개만 실행한다.

1. 동구야 / 거실 불 꺼줘
2. 동구야 / 도와줘
3. 헤이 푸르지오 / 자기 전 분위기로 해줘

각 장면은 대화가 먼저 보이고, 그 아래에 system analysis로 STT/Intent/Slots/Policy/Action이 이어진다.
3번째 캡처는 아파트형 호출어 예시로 `"헤이 푸르지오"`를 사용한다. 실제 라우팅은 호출어 이후 명령인 `"자기 전 분위기로 해줘"`를 처리하는 형태로 보여준다.

전체 장면 녹화:

```bash
python demo/video_demo_runner.py --privacy-intro --delay 1 --width 120
```

장면별 녹화:

```bash
python demo/video_demo_runner.py --scene 01 --width 120
python demo/video_demo_runner.py --scene 02 --width 120
python demo/video_demo_runner.py --scene 03 --width 120
python demo/video_demo_runner.py --scene 04 --width 120
python demo/video_demo_runner.py --scene 05 --width 120
```

OBS 설정:

- 터미널 폰트: 18-22px
- 화면비: 16:9
- 배경: 검정 또는 어두운 남색
- 녹화 해상도: 1920x1080
- 터미널 컷 길이: 장면당 7-10초

터미널에서 강조할 항목:

```text
음성 인식
Intent
Slots
Policy
Command
응답
Privacy ON
Cloud LLM BLOCKED
```

## Phase 5. Editing

CapCut에서 전체 시퀀스를 만든다. Vrew는 자막 정리용으로 사용한다.

반복 패턴:

```text
AI 생활 장면
→ 할머니 음성 명령
→ 실제 MVP 터미널 녹화
→ 생활 장면 결과 적용
→ AmiConnect 응답 음성
```

편집 순서:

1. AI 생활 클립을 콘티 순서대로 배치한다.
2. Typecast 음성을 장면에 맞춰 배치한다.
3. 각 명령 직후 터미널 녹화 컷을 넣는다.
4. 터미널 컷에서 `Policy`와 `Command`를 확대하거나 박스로 강조한다.
5. Vrew/CapCut 자동 자막을 생성한다.
6. 한국어 자막을 직접 교정한다.
7. 프라이버시 장면에서 `Cloud LLM: BLOCKED`, `Local TLM only`를 크게 보여준다.
8. 최종 색감은 따뜻하고 차분하게 맞춘다.

핵심 자막:

```text
같은 "불 꺼줘"라도, 시니어케어에서는 다르게 동작합니다.
낙상 방지를 위해 최소 조도를 유지합니다.
복약 일정은 로컬 시스템에서 확인합니다.
긴급 요청은 보호자 알림으로 연결됩니다.
프라이버시 모드에서는 외부 LLM 호출을 차단합니다.
핵심 돌봄 명령은 로컬에서 계속 처리됩니다.
```

## Acceptance Checklist

- [ ] "동구" 설정이 오프닝 20초 안에 이해된다.
- [ ] 첫 기능에서 시니어케어 차별점인 최소 조도 유지가 보인다.
- [ ] 5개 기능 장면마다 실제 MVP 터미널 컷이 들어간다.
- [ ] 터미널 컷에 `Policy`와 `Command`가 명확히 보인다.
- [ ] 프라이버시 모드가 `Privacy ON`, `Cloud LLM BLOCKED`, `Local TLM only`로 보인다.
- [ ] 한국어 자막이 깨지거나 과하게 길지 않다.
- [ ] AI 영상 안에 깨진 한국어 텍스트가 없다.
- [ ] 엔딩이 안전과 프라이버시 메시지로 닫힌다.
