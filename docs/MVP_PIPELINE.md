# AmiConnect Pipeline

이 문서는 현재 구현된 MVP 파이프라인을 기준으로 정리한다.
기획서 수준의 목표 구조가 아니라, `src/orchestrator.py`로 실제 실행되는 흐름을 설명한다.

## 1. 전체 흐름

```text
Text / Chat / WAV / Mic
        |
        v
STT: Moonshine-tiny-ko
        |
        v
Router
  - Privacy mode: local TLM only
  - Known LLM demos: Mindlogic Gateway direct
  - General input: local TLM first, unknown이면 Gateway fallback
        |
        v
PipelineResult
  - transcript
  - intent
  - slots
  - route
  - command
  - response_text
  - error
        |
        v
Executor mock
        |
        v
TTS
  - system: macOS say
  - melo: MeloTTS
  - auto: MeloTTS 실패 시 system fallback
  - none: 음성 출력 없음
```

메인 진입점은 `src/orchestrator.py`다.
입력 방식은 텍스트 단발, 텍스트 채팅, WAV 파일, 마이크 입력을 지원한다.

## 2. 실행 모드

### Text

STT 없이 텍스트를 바로 Router에 넣는다. 라우팅과 TTS를 빠르게 확인할 때 사용한다.

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
python -m src.orchestrator --text "자기 전 분위기로 해줘" --tts-backend system
python -m src.orchestrator --text "오늘따라 좀 답답하네 환기 좀 해줘" --tts-backend none
```

### Chat

여러 문장을 연속 입력한다.

```bash
python -m src.orchestrator --chat --tts-backend system
```

### WAV File

녹음된 WAV 파일을 `MoonshineSTT`로 인식한 뒤 Router로 넘긴다.

```bash
python -m src.orchestrator --audio-file samples/example.wav --tts-backend system
```

### Mic

마이크 입력을 `MicVADStream`으로 받아 발화 구간을 자른 뒤 STT로 넘긴다.

```bash
python -m src.orchestrator --mic --tts-backend system
python -m src.orchestrator --mic --mic-index 0 --tts-backend system
```

마이크 모드는 macOS 마이크 권한과 PortAudio 입력 장치가 필요하다.

## 3. STT

구현 위치:

- `src/stt/moonshine.py`
- `src/audio/microphone.py`

기본 모델:

```text
UsefulSensors/moonshine-tiny-ko
```

처리 방식:

1. WAV 또는 마이크 오디오를 mono 16 kHz float32로 맞춘다.
2. Moonshine backend를 로드한다.
3. 한국어 transcript를 생성한다.
4. transcript를 Router로 넘긴다.

`MoonshineSTT`는 두 backend를 지원한다.

- Transformers backend: Hugging Face 모델 경로 또는 `UsefulSensors/...` 모델
- ONNX backend: 로컬 ONNX 모델 이름 또는 경로

파일 단독 STT 테스트:

```bash
python -m src.stt.moonshine samples/example.wav
```

## 4. Router

구현 위치:

- `src/router/router.py`
- `src/tlm/infer.py`
- `src/cloud_llm/gateway.py`

Router는 최종적으로 `PipelineResult`를 만든다.

```python
PipelineResult(
    transcript="...",
    intent="...",
    slots={...},
    route="rule | llm | privacy_fallback",
    command={...},
    response_text="...",
    error="",
)
```

### Privacy Mode

`--privacy`를 주면 cloud LLM을 절대 호출하지 않는다.

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
```

동작:

1. local TLM만 사용한다.
2. local TLM이 `unknown`이면 cloud fallback 없이 `privacy_fallback`을 반환한다.

환경 변수로도 켤 수 있다.

```env
AMICONNECT_PRIVACY_MODE=true
```

### Local TLM

Router는 local TLM을 lazy-load한다.
즉, LLM으로 바로 보내는 demo 문장에서는 KoMiniLM weight를 먼저 로드하지 않는다.

모델 경로:

```text
models/tlm/kominilm-finetuned
```

`models/tlm/kominilm-finetuned/model.pt`가 있으면 `KoMiniLMTLM`을 사용한다.
없으면 regex 기반 `RuleTLM`을 fallback으로 사용한다.

지원되는 주요 local intent:

- `turn_on`
- `turn_off`
- `set_brightness`
- `set_temperature`
- `weather_query`
- `time_query`
- `medication_reminder`
- `set_medication_schedule`
- `emergency_call`
- `ambient_mode`

Senior-care 정책 예시:

- `turn_off`는 실제 전원 OFF가 아니라 최소 밝기 20%로 낮춘다.
- 취침 장면은 침실 조명 20%, 색온도 2200K, night mode를 적용한다.
- 복약 조회/저장은 `data/medication_schedule.json`을 사용한다.

### Mindlogic Gateway LLM

Mindlogic Gateway는 local TLM으로 처리하기 어렵거나 복합적인 자연어 명령을 처리한다.

필수 환경 변수:

```env
FACTCHAT_API_KEY=...
FACTCHAT_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway
FACTCHAT_MODEL=gemini-3.1-flash-lite-preview
```

현재 Gateway 설정:

- OpenAI 호환 Chat Completions: `/chat/completions/`
- JSON 응답 요청: `response_format={"type":"json_object"}`
- deterministic 출력: `temperature=0.0`
- 최대 출력: `max_tokens=320`

LLM으로 바로 보내는 demo 문장:

```text
자기 전 분위기로 해줘
오늘따라 좀 답답하네 환기 좀 해줘
```

이 문장들은 privacy mode가 아닐 때 local TLM 로딩 없이 Gateway로 바로 간다.

## 5. Command와 Executor

구현 위치:

- `src/executor/__init__.py`

Router 결과에 `command`가 있으면 executor가 먼저 실행된다.
현재 executor는 실제 Matter/IFTTT 호출이 아니라 콘솔 출력 mock이다.

출력 예시:

```text
[EXEC] scene.composite <- execute_scene {...}  (policy: senior_care.bedtime_scene)
```

command 기본 구조:

```json
{
  "action": "set_brightness",
  "target": "light.living_room",
  "params": {
    "brightness_pct": 20
  },
  "policy_applied": "senior_care.min_brightness"
}
```

실제 기기 연동은 이 executor 레이어를 Matter, Hue, IFTTT 등으로 교체하면 된다.

## 6. TTS

구현 위치:

- `src/tts/system.py`
- `src/tts/melo.py`
- `src/orchestrator.py`

TTS는 `response_text`가 있을 때만 실행된다.

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
```

지원 backend:

| backend | 동작 |
| --- | --- |
| `system` | macOS `say` 사용. WAV 파일을 만들지 않고 바로 말한다. |
| `melo` | MeloTTS 사용. WAV 생성 후 재생한다. 실패 시 fallback 없이 skip한다. |
| `auto` | MeloTTS를 먼저 시도하고 실패하면 macOS `say`로 fallback한다. |
| `none` | TTS를 끈다. 라우팅/LLM latency 확인에 사용한다. |

기본값은 `system`이다.

### macOS System TTS

macOS 내장 `say`를 사용한다.

기본 voice:

```env
AMICONNECT_SYSTEM_TTS_VOICE=Yuna
AMICONNECT_SYSTEM_TTS_RATE=185
```

명령 예시:

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
```

### MeloTTS

MeloTTS는 로컬 Python package지만 API 서버가 아니다.
코드에서 `melo.api.TTS`를 import하는 방식이다.

MeloTTS는 streaming PCM API가 아니라 파일 기반 API다.
현재 wrapper는 짧은 chunk로 나누어 WAV를 만들고, 각 chunk가 생성되면 바로 재생한다.

기본 동작:

1. `results/tts` 아래 WAV 생성
2. `afplay`로 재생
3. `AMICONNECT_TTS_CLEANUP=true`이면 재생 후 바로 삭제

Melo 단독 테스트:

```bash
conda run -n AI-25 python -m src.tts.melo "테스트 문장입니다."
```

파일을 남기고 싶을 때:

```bash
conda run -n AI-25 python -m src.tts.melo "테스트 문장입니다." --keep-file
```

재생 없이 WAV만 만들 때:

```bash
conda run -n AI-25 python -m src.tts.melo "테스트 문장입니다." --no-play --output results/tts/test.wav
```

오케스트레이터에서 Melo 사용:

```bash
conda run -n AI-25 python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend melo
```

Melo 관련 환경 변수:

```env
AMICONNECT_TTS_LANGUAGE=KR
AMICONNECT_TTS_SPEAKER=KR
AMICONNECT_TTS_DEVICE=auto
AMICONNECT_TTS_SPEED=1.0
AMICONNECT_TTS_PLAY=true
AMICONNECT_TTS_CLEANUP=true
AMICONNECT_TTS_CHUNKED=true
AMICONNECT_TTS_OUTPUT_DIR=results/tts
```

주의:

- `.venv` Python 3.13에서는 MeloTTS 설치가 잘 맞지 않을 수 있다.
- 현재 로컬에서는 `AI-25` conda env에 MeloTTS를 별도로 설치해서 테스트한다.
- MeloTTS는 첫 실행 때 Hugging Face 모델과 tokenizer를 내려받기 때문에 오래 걸릴 수 있다.
- 한국어 처리에 `num2words`, `anyascii`, `jamo`, `g2pkk`, `python-mecab-ko` 등이 필요할 수 있다.

## 7. Latency 해석

콘솔의 `Latency`는 오케스트레이터 단계별 시간을 보여준다.

Text mode:

```text
Latency nlu: 2082ms
```

Mic mode:

```text
Latency audio: ... | stt: ... | nlu: ...
```

의미:

- `audio`: VAD가 잘라낸 오디오 길이
- `stt`: Moonshine STT 처리 시간
- `nlu`: Router 처리 시간. LLM route면 Gateway API 호출 시간이 포함된다.

LLM route의 `nlu`는 같은 문장이어도 2초와 9초처럼 차이가 날 수 있다.
현재 temperature는 `0.0`이라 출력 랜덤성은 줄였지만, API 왕복 시간과 Gateway 서버 상태는 여전히 영향을 준다.

TTS 재생 시간은 현재 `Latency`에 포함되지 않는다.
`run_text` 기준으로는 Router 시간을 잰 뒤 `_process()`에서 executor/TTS가 실행된다.

## 8. 대표 데모 명령

Local/privacy route:

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
python -m src.orchestrator --text "약 먹을 시간 됐나" --privacy --tts-backend system
python -m src.orchestrator --text "지금 몇 시야" --privacy --tts-backend system
python -m src.orchestrator --text "오늘 날씨 어때" --privacy --tts-backend system
```

LLM route:

```bash
python -m src.orchestrator --text "자기 전 분위기로 해줘" --tts-backend system
python -m src.orchestrator --text "오늘따라 좀 답답하네 환기 좀 해줘" --tts-backend system
```

라우팅만 보고 싶을 때:

```bash
python -m src.orchestrator --text "자기 전 분위기로 해줘" --tts-backend none
```

## 9. 디버깅 체크리스트

### KoMiniLM 대신 RuleTLM이 뜰 때

확인할 것:

```bash
ls models/tlm/kominilm-finetuned/model.pt
```

이 파일이 없으면 Router는 `RuleTLM 사용 (학습 모델 없음)`을 출력한다.

### Gateway API key 오류

`.env`에 `FACTCHAT_API_KEY`가 있는지 확인한다.

```bash
python - <<'PY'
from pathlib import Path
for line in Path(".env").read_text().splitlines():
    if line.startswith("FACTCHAT_API_KEY="):
        print("FACTCHAT_API_KEY:", "set" if line.split("=", 1)[1].strip() else "empty")
    if line.startswith("FACTCHAT_MODEL="):
        print("FACTCHAT_MODEL:", line.split("=", 1)[1].strip())
PY
```

### TTS가 안 들릴 때

macOS system TTS부터 확인한다.

```bash
say -v Yuna "테스트입니다."
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
```

Melo는 먼저 WAV 생성 여부를 확인한다.

```bash
conda run -n AI-25 python -m src.tts.melo "테스트 문장입니다." --no-play --output results/tts/test.wav
afinfo results/tts/test.wav
afplay results/tts/test.wav
```

WAV가 정상인데 안 들리면 macOS 출력 장치나 음량 문제다.
WAV 생성이 실패하면 MeloTTS 의존성, Hugging Face 모델 다운로드, conda env를 확인한다.

## 10. 현재 한계

- executor는 실제 IoT 제어가 아니라 mock 출력이다.
- MeloTTS는 진짜 streaming TTS가 아니라 chunked WAV 생성 후 재생 방식이다.
- LLM route는 네트워크/API 상태에 따라 latency 편차가 크다.
- `--privacy`에서는 cloud fallback이 막히므로 복합 명령 처리 범위가 local TLM에 제한된다.
- TTS 시간은 현재 콘솔 latency에 포함되지 않는다.
