# AmiConnect_Prototype

AmiConnect is a Korean smart-home voice command MVP for senior-care scenarios.
It demonstrates a local-first voice pipeline that can run from a Mac terminal:

```text
Mic / WAV / Text
  -> STT
  -> Router
  -> Local TLM or Gemini fallback
  -> Mock executor
  -> TTS
```

The project is intentionally published as an MVP prototype.
It is not production-ready, not medical-grade software, and does not control real devices by default.

## What It Shows

- Korean STT with Moonshine
- Rule/TLM based local command handling
- Gemini fallback for complex natural language commands
- Senior-care safety policies such as minimum brightness instead of full lights-off
- Mock command execution for smart-home actions
- TTS output through macOS `say` or MeloTTS
- Privacy mode that blocks cloud LLM calls

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Set `GEMINI_API_KEY` in `.env` only if you want to test Gemini fallback.
Never commit `.env`.

### Local/privacy command

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
```

### Gemini fallback command

```bash
python -m src.orchestrator --text "자기 전 분위기로 해줘" --tts-backend system
```

### Routing only

```bash
python -m src.orchestrator --text "자기 전 분위기로 해줘" --tts-backend none
```

## TTS Options

```bash
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend system
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend auto
python -m src.orchestrator --text "거실 불 꺼줘" --privacy --tts-backend none
```

Backend summary:

- `system`: macOS `say`
- `melo`: MeloTTS
- `auto`: MeloTTS first, then system fallback
- `none`: disable speech output

## Documentation

- `QUICKSTART.md`: setup and command examples
- `docs/MVP_PIPELINE.md`: current MVP pipeline

## Current Limitations

- The executor is a mock console output, not real Matter/IFTTT control.
- MeloTTS uses generated WAV chunks, not true streaming PCM.
- Gemini fallback depends on API and network latency.
- Privacy mode disables cloud fallback, so complex commands are limited by local routing.
- The snapshot includes one fine-tuned TLM checkpoint for MVP reproduction.
- Generated audio files are not included.

## Security

API keys must stay in local `.env` files only.
The AmiConnect_Prototype repo should include `.env.example` with placeholders, but never `.env`.
