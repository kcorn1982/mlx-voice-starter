# CLAUDE.md

This project records narration with Qwen3-TTS through mlx-audio on a Mac, one short scene at a time, and measures the result so a video tool can use it. The README explains everything; read it before changing anything.

## Rules

- Never estimate how long a line takes to say. Durations come from the `.wav` files through `tools/manifest.py`.
- Never hand-edit `manifest.json` or anything in `audio/`. Change the scene text or the take, then regenerate.
- Never put narration text, durations or audio paths in video code. They arrive from `manifest.json`.
- Record and redo one scene at a time. Record the first scene or two and let the person listen before recording the rest. Redo only the scene they flag.
- A take is chosen by the person listening, not by the checker. `tools/check.py` only says which takes are worth hearing.
- If mlx-audio can't record, stop and report the error. Don't fall back to another text-to-speech service or placeholder audio.
- A step is done when its output has been checked, not when the command exits.

## Commands

```bash
uv run tools/say.py --voice voices/<name> --text-file scenes/01-hook.txt --takes 8 --out out/takes/01-hook
uv run tools/check.py out/takes/01-hook/take-*.wav --text-file scenes/01-hook.txt
cp out/takes/01-hook/take-<n>.wav audio/raw/01-hook.wav      # the take the person chose
uv run tools/level.py audio/raw/*.wav --out audio/
uv run tools/manifest.py audio/ --scenes scenes/
```
