# Demo Asset Folder Guide

이 폴더는 AmiConnect MVP 데모 영상 제작 자산을 정리하기 위한 위치다.

권장 구조:

```text
demo/assets/
  voice/                 # Typecast/CLOVA로 만든 음성
  generated_clips/       # Kling/Runway에서 만든 AI 영상
  terminal_recordings/   # OBS로 녹화한 실제 MVP 터미널 화면
  edit_exports/          # CapCut/Vrew 중간 export
  final/                 # 최종 제출 영상
```

Git은 빈 폴더를 추적하지 않으므로, 실제 제작 시 필요한 폴더를 직접 만들면 된다.

## Voice File Names

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

## Generated Clip Names

```text
generated_clips/01_opening_living_room.mp4
generated_clips/02_donggu_photo.mp4
generated_clips/03_living_light_command.mp4
generated_clips/04_living_light_result.mp4
generated_clips/05_medication_command.mp4
generated_clips/06_medication_result.mp4
generated_clips/07_cold_command.mp4
generated_clips/08_cold_result.mp4
generated_clips/09_emergency_command.mp4
generated_clips/10_emergency_notification.mp4
generated_clips/11_bedtime_command.mp4
generated_clips/12_bedtime_result.mp4
generated_clips/13_privacy_mode.mp4
generated_clips/14_ending.mp4
```

## Terminal Recording Names

```text
terminal_recordings/01_living_light_terminal.mp4
terminal_recordings/02_medication_terminal.mp4
terminal_recordings/03_cold_terminal.mp4
terminal_recordings/04_emergency_terminal.mp4
terminal_recordings/05_bedtime_terminal.mp4
terminal_recordings/06_privacy_intro_terminal.mp4
```

## Screenshot Card Names

```text
terminal_recordings/01_living_light_card.png
terminal_recordings/02_emergency_card.png
terminal_recordings/03_prugio_bedtime_card.png
```

## Final Exports

```text
final/amiconnect_demo_video.mp4
final/amiconnect_demo_video_subtitled.mp4
```
