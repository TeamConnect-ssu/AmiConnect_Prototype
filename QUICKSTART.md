# AmiConnect — Mac MVP Quickstart

라즈베리파이 없이 맥북 터미널에서 돌리는 1차 MVP입니다.
파이프라인: **마이크 → VAD → STT(Moonshine) → Router(Local rule | Mindlogic Gateway) → Rich 콘솔 출력**

## 현재 협업 기준

- 팀 협업용 MVP 기준 문서: [MVP_TEAM_GUIDE.md](./MVP_TEAM_GUIDE.md)
- 현재 데모 목표는 예시 명령어 10개를 끝까지 처리하는 것
- 이번 단계에서는 샘플별 `expected_route`를 기준으로 `TLM(rule)` 또는 `LLM`으로 고정 라우팅
- 어려운 명령은 일반 모드에서 바로 `LLM`으로 전달
- `privacy mode`는 현재 MVP 검증 대상이 아님
- 정식 버전에서 `IoT_TLM_v1.2` 기반 라우팅으로 교체 예정

## 1. 가상환경 + 패키지

```bash
cd ~/TeamConnect/amiconnect
python3.11 -m venv .venv  # python3.11 명령이 없으면: python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

> macOS 마이크 권한: 처음 실행할 때 터미널/iTerm에 "마이크 접근 허용"이 떠야 합니다. 안 뜨면 `시스템 설정 → 개인정보 보호 및 보안 → 마이크`에서 직접 허용.

## 2. 환경변수

```bash
cp .env.example .env
# .env 열어서 FACTCHAT_API_KEY 채우기
```

## 3. 텍스트로 먼저 동작 확인 (마이크 X)

```bash
python -m src.orchestrator --text "거실 불 꺼줘"
python -m src.orchestrator --text "약 먹을 시간 됐나?"
python -m src.orchestrator --text "자기 전 분위기로"   # 룰에 없으면 Gateway로 폴백
python -m src.orchestrator --chat                    # 채팅처럼 여러 명령 연속 입력
```

## 4. 마이크 모드

```bash
python -m src.orchestrator --mic
# 입력 장치 직접 지정:
python -m src.orchestrator --mic --mic-index 0
```

장치 목록 확인:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

## 5. 도경 STT 샘플 확인

샘플 WAV 파일을 `samples/senior_care/` 아래에 둔 뒤 실행한다. 공개 repo에는 실제 음성 파일을 포함하지 않는다.

단일 음성 파일을 STT JSON으로 확인:

```bash
python -m src.stt.moonshine samples/senior_care/001_living_light_off.wav \
  --request-id demo_001
```

단일 음성 파일을 STT → Router까지 확인:

```bash
python -m src.orchestrator \
  --audio-file samples/senior_care/001_living_light_off.wav \
  --privacy
```

10개 샘플을 한 번에 평가하고 JSONL로 저장:

```bash
python -m src.stt.evaluate_samples \
  --output-jsonl results/stt_samples.jsonl
```

기본 모델은 `UsefulSensors/moonshine-tiny-ko`다. 다른 모델 파일을 따로 받은 경우에는 세 명령 모두에 같은 모델 경로를 넘긴다.

```bash
python -m src.stt.evaluate_samples \
  --model /path/to/moonshine-model \
  --output-jsonl results/stt_samples.jsonl
```

평가 결과에는 원문 완전 일치 여부인 `exact_match`와 구두점/공백 차이를 보기 위한 `normalized_exact_match`, `similarity`가 함께 나온다.
공식 통과 기준은 팀 합의 후 확정한다.

```bash
python -m src.stt.evaluate_samples \
  --output-jsonl results/stt_samples.jsonl
```

## 6. 옵션: Privacy 모드 실험

```bash
python -m src.orchestrator --mic --privacy
```

현재 팀 MVP 검증 대상은 아니고, 필요할 때만 별도로 실험한다.
룰에 매칭 안 되는 발화는 `복합 명령은 지금 처리할 수 없습니다` 폴백.

---

## 다음 단계 (이번 MVP 범위 밖)

- `src/tlm/infer.py`의 `RuleTLM`을 KoMiniLM 파인튜닝 모델로 교체
- 웨이크워드(openWakeWord) 추가
- TTS(MeloTTS) 추가 → 음성 응답
- Hue/Matter 컨트롤러 연결
- GitHub 레포 생성 후 협업 시작

## 알려진 이슈

- `UsefulSensors/moonshine-tiny-ko`가 로컬 캐시에 없으면 처음 실행할 때 Hugging Face에서 모델을 받아야 합니다.
- 영어 기본 모델인 `moonshine/tiny`는 한국어 샘플에서 빈 transcript가 나올 수 있으므로 MVP 검증에는 쓰지 않습니다.
