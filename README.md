# AmiConnect_Prototype

AmiConnect_Prototype은 시니어 케어 상황을 가정한 한국어 스마트홈 음성 명령 MVP입니다.
마이크 또는 텍스트 입력부터 명령 이해, 실행 결과 출력, 음성 응답까지 하나의 터미널 파이프라인으로 연결합니다.

```text
마이크 / WAV / 텍스트
  -> Moonshine STT
  -> Router
  -> local TLM 또는 Mindlogic Gateway fallback
  -> mock 스마트홈 executor
  -> TTS 응답
```

이 저장소는 완성형 제품이 아니라, 한국어 음성 명령 기반 스마트홈 파이프라인이 실제로 어떻게 동작하는지 보여주는 프로토타입입니다.

## 주요 기능

- 텍스트, WAV 파일, 마이크 입력을 통한 한국어 명령 테스트
- fine-tuned TLM checkpoint 기반 local command routing
- 일부 복합 명령에 대한 Mindlogic Gateway fallback
- cloud LLM 호출을 막는 privacy mode
- "불 꺼줘" 요청 시 완전 소등 대신 최소 밝기를 유지하는 시니어 케어 정책 예시
- 실제 기기 제어 대신 command JSON을 출력하는 mock executor
- macOS `say` 기반 TTS 응답
- 선택적으로 MeloTTS backend 사용 가능

## 저장소 구성

```text
src/orchestrator.py      전체 파이프라인 실행 진입점
src/router/             local/cloud 라우팅
src/tlm/                TLM 추론 코드
src/cloud_llm/          Mindlogic Gateway NLU fallback
src/stt/                Moonshine STT wrapper
src/tts/                system/MeloTTS wrapper
src/executor/           mock command executor
scripts/eval_nlu.py     KoMiniLM NLU 평가 스크립트
models/tlm/...          MVP 재현용 fine-tuned TLM checkpoint
data/demo/              데모용 복약 일정 데이터
data/processed/valid.jsonl  NLU 검증용 validation split
```

학습 데이터, 생성된 음성 파일, 개인 환경 변수 파일, 내부 팀 문서는 포함하지 않았습니다.
검증 재현을 위한 작은 validation split만 포함했습니다.

## 빠른 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Gateway fallback을 테스트하려면 `.env`에 `FACTCHAT_API_KEY`를 설정해야 합니다.
`.env` 파일은 절대 커밋하지 않습니다.

## 실행 예시

cloud 호출 없이 local route만 확인:

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
```

Gateway fallback route 확인:

```bash
AMICONNECT_LOCAL_CONFIDENCE_THRESHOLD=0.99 \
python -m src.orchestrator --text "자기 전 분위기로 해줘" --tts-backend system
```

음성 출력 없이 routing만 확인:

```bash
python -m src.orchestrator --text "자기 전 분위기로 해줘" --tts-backend none
```

마이크 입력 전체 파이프라인:

```bash
python -m src.orchestrator --mic --tts-backend system
```

STT는 코드에 포함되어 있으며, 마이크 모드는 로컬 마이크 권한과 Moonshine 모델 다운로드/캐시 상태에 따라 첫 실행 시간이 달라질 수 있습니다.
샘플 WAV 파일은 저장소에 포함하지 않았습니다. 로컬 WAV를 넣어 테스트하려면 다음처럼 실행합니다.

```bash
python -m src.orchestrator --audio-file path/to/sample.wav --privacy --tts-backend none
```

## KoMiniLM 체크포인트 사용

이 저장소에는 MVP 재현을 위한 fine-tuned KoMiniLM checkpoint가 포함되어 있습니다.

```text
models/tlm/kominilm-finetuned/model.pt
models/tlm/kominilm-finetuned/config.json
models/tlm/kominilm-finetuned/label_mappings.json
```

`Router`는 위 checkpoint가 있으면 자동으로 `KoMiniLMTLM`을 로드합니다. 모델이 없을 때만 `RuleTLM` fallback을 사용합니다.

간단한 텍스트 입력 예시:

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend none
python -m src.orchestrator --text "약 먹을 시간 됐나" --privacy --tts-backend none
python -m src.orchestrator --text "도와줘" --privacy --tts-backend none
python -m src.orchestrator --text "자기 전 분위기로 해줘" --privacy --tts-backend none
```

출력에는 intent, slot, route, confidence, command, 응답 텍스트가 포함됩니다.

## 검증 결과

아래 숫자는 현재 저장소에 포함된 `models/tlm/kominilm-finetuned/model.pt`와
`data/processed/valid.jsonl`을 사용해 직접 측정한 결과입니다.
모델 로드와 tokenizer warm-up 시간은 latency에서 제외했습니다.

```bash
python scripts/eval_nlu.py
```

```text
dataset: data/processed/valid.jsonl
cases: 46
intent accuracy: 43/46 = 93.5%
slot entity precision/recall/F1: 100.0% / 98.3% / 99.1%
strict slot exact match 참고값: 45/46 = 97.8%
joint exact match: 43/46 = 93.5%
NLU latency: warm inference mean 약 10ms, p95 약 10-12ms
```

`intent accuracy`는 사용자의 발화를 어떤 작업으로 분류했는지 보는 주 지표입니다.
`slot entity F1`은 KoMiniLM BIO/CRF 출력에 도메인 slot normalizer를 적용한 뒤의 entity 단위 micro F1이며, slot 성능을 볼 때 주로 사용하는 지표입니다.
`strict slot exact match`는 한 문장의 모든 slot 문자열이 조사/어미 포함 여부까지 정확히 일치해야 하는 엄격한 참고 지표입니다.
latency는 실행 기기와 백그라운드 상태에 따라 조금 달라지므로, 현재 환경의 정확한 값은 `python scripts/eval_nlu.py`로 다시 확인합니다.

## 구성 요소

- STT: `src/stt/moonshine.py`의 Moonshine wrapper가 WAV 또는 마이크 입력을 텍스트로 변환합니다.
- NLU/TLM: `src/tlm/infer.py`의 fine-tuned KoMiniLM이 intent와 confidence를 예측하고, BIO/CRF slot 출력에 도메인 slot normalizer를 적용합니다.
- LLM fallback: `src/cloud_llm/gateway.py`의 Mindlogic Gateway client가 복합 발화를 JSON command로 변환합니다.
- LLM prompt: `src/cloud_llm/gateway.py`의 `SYSTEM_PROMPT`에 시니어 케어 스마트홈 NLU 지시문이 들어 있습니다.
- TTS: `src/tts/system.py`는 macOS `say`, `src/tts/melo.py`는 MeloTTS 파일 생성 방식을 사용합니다.

## 예시 명령

```text
거실 불 꺼줘
약 먹을 시간 됐나
지금 몇 시야
오늘 날씨 어때
자기 전 분위기로 해줘
```

## TTS Backend

```text
system  macOS say 사용
melo    MeloTTS 사용
auto    MeloTTS 먼저 시도 후 system fallback
none    음성 출력 비활성화
```

macOS에서 가장 안정적으로 데모하려면 `--tts-backend system`을 권장합니다.

## 환경 변수

환경 변수는 `.env`에서 로드됩니다.

```env
FACTCHAT_API_KEY=your-factchat-api-key-here
FACTCHAT_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway
FACTCHAT_MODEL=gemini-3.1-flash-lite-preview
AMICONNECT_PRIVACY_MODE=false
AMICONNECT_LOCAL_CONFIDENCE_THRESHOLD=0.65
AMICONNECT_TTS_BACKEND=system
```

API key는 로컬 `.env`에만 두어야 합니다.
이 저장소에는 placeholder가 들어간 `.env.example`만 포함합니다.

## 문서

- `QUICKSTART.md`: 설치 및 실행 명령
- `docs/MVP_PIPELINE.md`: 현재 파이프라인 상세 정리

## 참고

- executor는 실제 IoT 기기 제어가 아니라 데모용 mock layer입니다.
- fine-tuned KoMiniLM checkpoint는 GitHub 단일 파일 제한에 맞는 약 89MB 파일로 포함됩니다.
- Gateway fallback은 별도 `FACTCHAT_API_KEY`가 있어야 동작합니다. Privacy mode/local demo는 키 없이도 실행됩니다.
- Gateway fallback은 특정 문장을 하드코딩하지 않고, local NLU confidence가 `AMICONNECT_LOCAL_CONFIDENCE_THRESHOLD`보다 낮을 때 사용합니다.
- Gateway fallback은 API와 네트워크 상태에 따라 latency가 달라질 수 있습니다.
- MeloTTS는 파일 생성 기반으로 동작하며, macOS에서는 `say`가 가장 간단한 TTS 옵션입니다.
