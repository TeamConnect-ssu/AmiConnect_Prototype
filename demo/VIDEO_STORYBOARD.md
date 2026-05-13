# AmiConnect MVP Demo Video Storyboard

## 1. Core Concept

영상의 중심 메시지는 다음 한 문장이다.

> AmiConnect는 명령을 그대로 실행하지 않는다. 시니어케어 환경에서는 안전과 프라이버시를 먼저 생각한다.

이번 MVP는 완성된 앱 화면보다 터미널 기반 음성 파이프라인에 가깝다. 그래서 영상은 터미널을 숨기는 방향이 아니라, 실제 MVP 로직을 증거처럼 보여주는 방향으로 구성한다.

반복 구조:

```text
생활 장면
→ 할머니가 "동구야" 하고 음성 명령
→ 실제 MVP 터미널 화면으로 전환
→ STT / Intent / Policy / Command 확인
→ 다시 생활 장면으로 돌아와 결과가 적용됨
```

이 구조를 쓰면 AI로 만든 생활 장면이 단순한 컨셉 영상처럼 보이지 않고, 실제 MVP 판단 결과가 생활 공간에 반영되는 느낌을 줄 수 있다.

## 2. Service Setting

### 2.1. Service Name

- 서비스명: AmiConnect
- 호출명: 동구야
- 도메인: 시니어케어 스마트홈
- 공간: 혼자 사는 어르신의 집 또는 시니어 케어 주거 공간

### 2.2. Why "Donggu"

동구는 할머니가 예전에 아끼던 반려견의 이름이라는 설정으로 간다.

이 설정이 좋은 이유:

- "동구야"라는 호출이 자연스럽다.
- 시니어케어 영상에 필요한 따뜻한 감정선이 생긴다.
- 손자 이름보다 AI 호출명으로 덜 헷갈린다.
- 아파트 브랜드명보다 권리 문제와 광고 느낌이 적다.

추천 문장:

```text
동구는 할머니가 오래 아끼던 이름입니다.
예전에 곁을 지켜주던 이름.
이제 AmiConnect는 그 이름으로, 할머니의 일상을 조용히 돕습니다.
```

### 2.3. Tone

- 너무 슬프게 만들지 않는다.
- 감정은 담백하게, 기능은 명확하게 보여준다.
- 광고처럼 과장하지 않고, "믿을 수 있는 돌봄 기술" 느낌으로 간다.
- 응급 장면도 과하게 연출하지 않고 실제 생활의 불편함 정도로 표현한다.

## 3. Recommended Production Pipeline

### 3.1. Overall Workflow

실행용 제작 순서는 `demo/PRODUCTION_PLAN.md`를 기준으로 한다. 실제 MVP 터미널 화면은 `demo/video_demo_runner.py`로 녹화한다.

```text
1. 콘티 확정
2. 할머니 / 집 / 동구 기준 이미지 생성
3. 장면별 5-10초 AI 영상 생성
4. 실제 MVP 터미널 화면 녹화
5. 할머니 음성, 내레이션, TTS 대사 녹음
6. CapCut 또는 DaVinci Resolve에서 교차 편집
7. 자막, 정책 강조 그래픽, privacy mode UI 추가
8. 최종 렌더링
```

### 3.2. Recommended Tools

| 목적 | 추천 툴 | 사용 이유 |
|---|---|---|
| 생활 장면 AI 영상 | Runway | 실사톤, 카메라 무빙, 감성 장면에 강함 |
| 인물 일관성/짧은 장면 | Kling | 이미지 기반 영상, 캐릭터 유지, 립싱크 기능에 강함 |
| 빠른 감성 컷 | Luma Dream Machine | 짧은 생활 컷 생성에 좋음 |
| 숏폼 스타일 컷 | Pika | 빠른 생성과 짧은 영상 실험에 적합 |
| 전체 편집 | CapCut | 자막, 전환, 음악, 화면분할 작업이 빠름 |
| 고급 편집 | DaVinci Resolve | 색보정, 정교한 편집에 좋음 |
| 화면 녹화 | OBS / QuickTime | 실제 터미널 실행 화면 녹화 |
| 음성 생성/보정 | ElevenLabs 등 | 할머니 목소리, 내레이션, TTS 느낌 제작 가능 |

추천 조합:

```text
Kling 또는 Runway
+ OBS 터미널 녹화
+ CapCut 편집
+ 별도 녹음한 할머니 음성
```

## 4. Full Storyboard

목표 길이: 4분 30초-5분

### 4.1. Scene Table

| 시간 | 장면 | 화면/연출 | 음성/자막 | 실제 MVP 연결 |
|---|---|---|---|---|
| 0:00-0:08 | 오프닝 | 조용한 거실. 오래된 사진, 약통, 스탠드 조명. 할머니가 혼자 앉아 있음. | 자막: "혼자 있는 시간이 길어진 집." |  |
| 0:08-0:18 | 동구 소개 | 작은 강아지 사진 또는 목걸이 클로즈업. 이름표에 "동구". | 내레이션: "동구는 할머니가 오래 아끼던 이름입니다." |  |
| 0:18-0:28 | 호출 | 할머니가 익숙하게 말함. | 할머니: "동구야." / 자막: "이제 그 이름은, 할머니 곁을 지키는 AI가 되었습니다." | Wake word 느낌 |
| 0:28-0:40 | 첫 명령 | 밤 거실. 할머니가 일어나려 함. | 할머니: "동구야, 거실 불 꺼줘." | 입력 문장 |
| 0:40-0:52 | 실제 MVP 화면 | 터미널 화면으로 컷. 실제 실행 결과 표시. | 자막: "AmiConnect 실제 MVP 처리 화면" | STT / Intent / Command |
| 0:52-1:05 | 결과 적용 | 다시 거실. 조명이 완전히 꺼지지 않고 20% 정도로 은은하게 남음. | TTS: "거실 불을 약하게 줄였어요. 어두워서 넘어지지 않으시도록요." | senior_care.min_brightness |
| 1:05-1:20 | 복약 장면 | 아침 식탁. 약통 옆에서 할머니가 묻는다. | 할머니: "동구야, 약 먹을 시간 됐나?" | 입력 문장 |
| 1:20-1:30 | MVP 화면 | 터미널 컷. | Intent: medication_reminder / Command: query_medication_schedule | 복약 조회 |
| 1:30-1:42 | 결과 적용 | 약통 알림 카드 또는 자막. | TTS: "혈압약은 30분 뒤인 오전 9시에 드시면 돼요." | 복약 안내 |
| 1:42-1:58 | 추위 장면 | 할머니가 담요를 덮으며 말함. | 할머니: "동구야, 추워." | 입력 문장 |
| 1:58-2:08 | MVP 화면 | 터미널 컷. | Intent: set_temperature / Command: adjust_temperature +2C | 난방 제어 |
| 2:08-2:20 | 결과 적용 | 온도 표시가 올라가고, 보온 매트 아이콘 또는 콘센트 장면. | TTS: "방 온도를 2도 올렸어요. 보온 매트도 켜드릴까요?" | senior_care.suggest_warmth_aid |
| 2:20-2:36 | 응급 장면 | 할머니가 불편한 듯 손잡이를 잡고 앉음. 과하게 연출하지 않음. | 할머니: "동구야, 도와줘." | 입력 문장 |
| 2:36-2:48 | MVP 화면 | 터미널 컷. | Intent: emergency_call / Command: trigger_emergency -> notification.caregiver | 보호자 알림 |
| 2:48-3:02 | 결과 적용 | 보호자 휴대폰에 알림: "긴급 도움 요청 / 위치: 거실". | TTS: "보호자에게 알렸어요. 곧 도와드리러 와요. 그 자리에 가만히 계세요." | 응급 대응 |
| 3:02-3:18 | 취침 모드 | 밤. 할머니가 침실로 이동. | 할머니: "동구야, 자기 전 분위기로 해줘." | 복합 명령 |
| 3:18-3:30 | MVP 화면 | 터미널 컷. | Intent: ambient_mode / Command: execute_scene | 취침 장면 |
| 3:30-3:42 | 결과 적용 | 침실 조명이 따뜻하게 낮아지고 야간 모드 표시. | TTS: "주무실 준비를 해드렸어요. 불은 살짝만 남겨두고, 따뜻한 색으로 바꿨어요." | brightness 20% + warm 2200K + night mode |
| 3:42-3:58 | 프라이버시 모드 전환 | 화면에 Privacy Mode ON. 클라우드 아이콘이 차단되는 그래픽. | 내레이션: "민감한 생활 공간의 음성은, 밖으로 나가지 않아야 하니까." | Privacy Mode |
| 3:58-4:12 | 실제 MVP 화면 | 터미널에서 --privacy 실행 화면. | 자막: "Cloud LLM 호출 차단 / Local TLM only" | route=KoMiniLM, confidence 강조 |
| 4:12-4:28 | 프라이버시 적용 장면 | 할머니가 다시 말함. | 할머니: "동구야, 거실 불 꺼줘." | 단순 명령 로컬 처리 |
| 4:28-4:40 | 결과 적용 | 터미널 컷 후 조명 20% 적용. | 자막: "프라이버시 모드에서도 핵심 돌봄 명령은 로컬에서 처리" | set_brightness 20% |
| 4:40-4:55 | 마무리 | 할머니가 편안히 앉아 있고, 조명은 은은함. | 내레이션: "AmiConnect는 명령을 그대로 실행하지 않습니다. 시니어케어 환경에서는 안전과 프라이버시를 먼저 생각합니다." |  |
| 4:55-5:00 | 엔딩 | AmiConnect 로고 또는 텍스트. | "동구야, 오늘도 곁에 있어줘." |  |

## 5. Voice Recording Plan

할머니 음성은 미리 녹음해두는 것이 좋다. AI 영상 생성 후 립싱크를 맞추거나, 실제 영상 위에 음성만 얹을 수 있다.

### 5.1. Voice Types

필요한 음성은 세 종류다.

| 타입 | 용도 | 예시 |
|---|---|---|
| 할머니 음성 | 사용자 명령 | "동구야, 거실 불 꺼줘." |
| AmiConnect 응답 음성 | 시스템 TTS처럼 들리는 안내 | "거실 불을 약하게 줄였어요." |
| 내레이션 | 영상 설명 | "동구는 할머니가 오래 아끼던 이름입니다." |

할머니 음성은 너무 힘없는 톤보다, 느리고 편안한 말투가 좋다. 시니어케어 서비스가 "보호 대상"을 과하게 연출하는 느낌을 피해야 한다.

### 5.2. 할머니 음성 녹음 대사

```text
동구야.
동구야, 거실 불 꺼줘.
동구야, 약 먹을 시간 됐나?
동구야, 추워.
동구야, 도와줘.
동구야, 자기 전 분위기로 해줘.
```

옵션 대사:

```text
동구야, 오늘 추워?
동구야, 방 불 좀 약하게 해주게.
동구야, 지금 몇 시야?
```

### 5.3. AmiConnect 응답 녹음 대사

```text
거실 불을 약하게 줄였어요. 어두워서 넘어지지 않으시도록요.
혈압약은 30분 뒤인 오전 9시에 드시면 돼요.
방 온도를 2도 올렸어요. 보온 매트도 켜드릴까요?
보호자에게 알렸어요. 곧 도와드리러 와요. 그 자리에 가만히 계세요.
주무실 준비를 해드렸어요. 불은 살짝만 남겨두고, 따뜻한 색으로 바꿨어요.
```

### 5.4. 내레이션 대사

오프닝:

```text
혼자 있는 시간이 길어진 집.
하지만 할머니에게는 아직 익숙한 이름 하나가 남아 있습니다.

동구.

예전에 곁을 지켜주던 이름.
이제 AmiConnect는 그 이름으로,
할머니의 일상을 조용히 돕습니다.
```

프라이버시:

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

### 5.5. Recording Tips

- 같은 문장을 3번씩 녹음한다.
- 문장 앞뒤로 1초 정도 침묵을 둔다.
- 휴대폰 녹음도 가능하지만, 가능하면 조용한 방에서 녹음한다.
- 할머니 명령 대사는 약간 느리게 말한다.
- 응답 음성은 또박또박, 너무 기계적이지 않게 녹음한다.
- 파일명은 장면 번호 기준으로 정리한다.

추천 파일명:

```text
voice/01_grandma_wake_donggu.wav
voice/02_grandma_living_light_off.wav
voice/03_ai_living_light_response.wav
voice/04_grandma_medication.wav
voice/05_ai_medication_response.wav
voice/06_grandma_cold.wav
voice/07_ai_temperature_response.wav
voice/08_grandma_help.wav
voice/09_ai_emergency_response.wav
voice/10_grandma_bedtime.wav
voice/11_ai_bedtime_response.wav
voice/12_narration_opening.wav
voice/13_narration_privacy.wav
voice/14_narration_ending.wav
```

## 6. Terminal Screen Plan

### 6.1. Goal

터미널은 개발 로그가 아니라 "실제 MVP 판단 화면"처럼 보여야 한다.

강조할 항목:

- 음성 인식 문장
- Intent
- Slots
- Policy
- Command
- Response
- Privacy mode
- Local route

### 6.2. Recommended Terminal Layout

가능하면 영상용 출력은 다음처럼 보이게 만든다.

```text
┌────────────────── AmiConnect MVP ──────────────────┐
│ Mode        Senior Care                             │
│ Privacy     ON                                      │
│ Input       "거실 불 꺼줘"                           │
├─────────────────────────────────────────────────────┤
│ 음성 인식   거실 불 꺼줘                             │
│ Intent      turn_off / toggle_device                │
│ Slots       device=불, location=거실                 │
│ Policy      senior_care.min_brightness              │
│ Command     light.living_room -> brightness 20%      │
│ Response    거실 불을 약하게 줄였어요...              │
└─────────────────────────────────────────────────────┘
```

현재 `src.orchestrator`의 Rich 패널 출력도 사용할 수 있다. 다만 영상에서는 불필요한 warning이 나오면 몰입이 깨지므로 실행 환경 변수를 같이 준다.

### 6.3. Terminal Recording Commands

음성을 별도로 편집할 경우 `--tts-backend none`을 권장한다.

영상 녹화용 권장 명령:

```bash
python demo/video_demo_runner.py --privacy-intro --delay 1 --width 120
```

장면별로 끊어서 녹화할 때:

```bash
python demo/video_demo_runner.py --scene 01 --width 120
python demo/video_demo_runner.py --scene 02 --width 120
python demo/video_demo_runner.py --scene 03 --width 120
python demo/video_demo_runner.py --scene 04 --width 120
python demo/video_demo_runner.py --scene 05 --width 120
```

기존 orchestrator를 직접 녹화할 수도 있다.

```bash
TOKENIZERS_PARALLELISM=false PYTHONWARNINGS=ignore python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend none
TOKENIZERS_PARALLELISM=false PYTHONWARNINGS=ignore python -m src.orchestrator --text "약 먹을 시간 됐나" --privacy --tts-backend none
TOKENIZERS_PARALLELISM=false PYTHONWARNINGS=ignore python -m src.orchestrator --text "추워" --privacy --tts-backend none
TOKENIZERS_PARALLELISM=false PYTHONWARNINGS=ignore python -m src.orchestrator --text "도와줘" --privacy --tts-backend none
TOKENIZERS_PARALLELISM=false PYTHONWARNINGS=ignore python -m src.orchestrator --text "자기 전 분위기로 해줘" --privacy --tts-backend none
```

시스템 TTS까지 실제로 들려주고 싶으면 `--tts-backend system`을 사용한다.

```bash
TOKENIZERS_PARALLELISM=false PYTHONWARNINGS=ignore python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
```

### 6.4. Terminal Visual Rules

- 폰트 크기: 18-22px
- 배경: 검정 또는 어두운 남색
- 글자: 흰색 중심
- 포인트 컬러: 초록은 성공/로컬 처리, 노랑은 정책, 빨강은 cloud 차단
- 한 장면당 터미널 노출: 7-10초
- `Policy`와 `Command`는 편집에서 확대하거나 박스로 강조
- warning, dependency log, 긴 stack trace는 노출하지 않는다.

### 6.5. OBS Scene Recommendation

OBS에서 다음 장면을 미리 만들어두면 편하다.

| Scene | 구성 |
|---|---|
| Scene 1 | AI 생활 영상 전체 화면 |
| Scene 2 | 터미널 전체 화면 |
| Scene 3 | 터미널 왼쪽 + 오른쪽 상태 패널 |
| Scene 4 | Privacy Mode 그래픽 |
| Scene 5 | 엔딩 로고 |

오른쪽 상태 패널 예시:

```text
AmiConnect MVP

Mode: Senior Care
Privacy: ON
Cloud LLM: BLOCKED

Current Policy:
senior_care.min_brightness

Device:
Living Room Light -> 20%
```

## 7. AI Video Prompt Pack

AI 영상 생성은 캐릭터 기준 이미지를 먼저 만들고, 그 이미지를 기준으로 image-to-video를 돌리는 방식이 좋다.

### 7.1. Character Reference Image

```text
A warm realistic Korean senior woman in her late 70s, gentle expression, short gray hair, wearing a soft cardigan, sitting in a modest modern apartment living room, evening warm light, realistic documentary style, natural skin texture, calm atmosphere
```

### 7.2. Living Room Opening

```text
A quiet Korean apartment living room at night, an elderly woman sitting near a small table with a medicine box and a warm floor lamp, a framed photo of an old small dog named Donggu on the shelf, cinematic realistic documentary style, soft warm lighting
```

### 7.3. Donggu Photo Close-up

```text
Close-up of a small framed photo of an old beloved dog on a wooden shelf, a small name tag says Donggu, warm nostalgic lighting, realistic documentary style, shallow depth of field
```

### 7.4. Light Dimming Scene

```text
The elderly woman says a short voice command, the living room light dims gently but does not turn completely dark, warm low light remains for safety, calm realistic camera, subtle movement
```

### 7.5. Medication Scene

```text
Morning kitchen table in a Korean apartment, an elderly woman looks at a small medicine box and asks a question, soft daylight, realistic documentary style, gentle camera push in
```

### 7.6. Cold Scene

```text
An elderly Korean woman sitting in a bedroom with a blanket over her shoulders, she looks slightly cold and speaks softly, warm realistic indoor light, calm documentary style
```

### 7.7. Emergency Notification Scene

```text
A caregiver smartphone receives an urgent care notification, clean Korean mobile notification interface, message says emergency help request from living room, realistic close-up shot
```

### 7.8. Bedtime Scene

```text
A cozy bedroom at night, warm bedside light dims to a soft amber color, elderly woman preparing to sleep, safe low brightness remains, peaceful realistic style
```

### 7.9. Privacy Mode Graphic

```text
Minimal technology visual overlay, privacy mode on, cloud icon blocked, local processing only, clean UI animation style, dark background, subtle blue and green highlights
```

## 8. Subtitle and Caption Copy

### 8.1. Key Captions

```text
같은 "불 꺼줘"라도, 시니어케어에서는 다르게 동작합니다.
낙상 방지를 위해 최소 조도를 유지합니다.
복약 일정은 로컬 시스템에서 확인합니다.
긴급 요청은 보호자 알림으로 연결됩니다.
프라이버시 모드에서는 외부 LLM 호출을 차단합니다.
핵심 돌봄 명령은 로컬에서 계속 처리됩니다.
```

### 8.2. Opening Copy

```text
혼자 있는 시간이 길어진 집.
하지만 할머니에게는 아직 익숙한 이름 하나가 남아 있습니다.

동구.

예전에 곁을 지켜주던 이름.
이제 AmiConnect는 그 이름으로,
할머니의 일상을 조용히 돕습니다.
```

### 8.3. Ending Copy

```text
AmiConnect는 명령을 그대로 실행하지 않습니다.
시니어케어 환경에서는 안전과 프라이버시를 먼저 생각합니다.

동구야, 오늘도 곁에 있어줘.
```

## 9. MVP Feature Mapping

| 영상 장면 | 사용자 발화 | MVP Intent | Command | Senior Care Policy |
|---|---|---|---|---|
| 거실 조명 | 거실 불 꺼줘 | toggle_device / turn_off | set_brightness -> light.living_room | senior_care.min_brightness |
| 복약 | 약 먹을 시간 됐나 | medication_reminder | query_medication_schedule | senior_care.medication_enabled |
| 추위 | 추워 | set_temperature | adjust_temperature +2C | senior_care.suggest_warmth_aid |
| 응급 | 도와줘 | emergency_call | trigger_emergency -> notification.caregiver | senior_care.emergency |
| 취침 | 자기 전 분위기로 해줘 | ambient_mode | execute_scene | senior_care.bedtime_scene |
| 프라이버시 | 거실 불 꺼줘 | local rule route | set_brightness -> 20% | cloud call blocked |

## 10. Final Direction

최종 영상은 "AI가 만든 예쁜 컨셉 영상"보다 "실제 MVP가 판단하고 적용하는 데모"로 보여야 한다.

가장 중요한 연출 원칙:

```text
생활 장면만 보여주지 않는다.
터미널만 보여주지도 않는다.
둘을 연결해서 실제 로직이 생활 장면을 바꾸는 것처럼 보여준다.
```

최종 메시지:

```text
AmiConnect는 명령을 그대로 실행하지 않습니다.
시니어케어 환경에서는 안전과 프라이버시를 먼저 생각합니다.
```
