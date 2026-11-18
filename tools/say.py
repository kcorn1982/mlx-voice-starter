# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["mlx-audio==0.6.4"]
# ///
"""
Speaks a line with Qwen3-TTS through mlx-audio, on your Mac's GPU, and writes one or more takes.

Three ways to pick the voice, one per Qwen3-TTS model family:

    # Your own voice, cloned from a reference recording (Base model)
    uv run tools/say.py --voice voices/me --text "Hello there." --takes 8

    # A built-in speaker, with an optional delivery note (CustomVoice model)
    uv run tools/say.py --speaker Ryan --instruct "Calm and warm." --text "Hello there."

    # A new voice described in words (VoiceDesign model)
    uv run tools/say.py --design "A warm, low male voice, unhurried, British accent." --text "Hello there."

Text can come from --text or --text-file (one scene per file works well). Takes are written to
--out (default out/takes/<timestamp>/) as take-1.wav, take-2.wav and so on, mono 16-bit 24 kHz,
with a takes.json beside them recording the model, voice, text and seed. The same text, voice,
model, seed and number of takes give the same audio again, so a take you like is never lost.
"""

import argparse
import json
import os
import sys
import time
import wave

import mlx.core as mx
import numpy as np
from mlx_audio.tts.utils import load_model

MODELS = {
    "clone": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16",
    "speaker": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16",
    "design": "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16",
}


def write_wav(path: str, audio, sr: int) -> float:
    a = np.asarray(audio, dtype=np.float32).reshape(-1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype("<i2").tobytes())
    return len(a) / sr


def joined(results) -> mx.array:
    parts = [r.audio for r in results]
    return mx.concatenate(parts) if len(parts) > 1 else parts[0]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    who = p.add_mutually_exclusive_group(required=True)
    who.add_argument("--voice", help="folder holding reference.wav and reference.txt (clones that voice)")
    who.add_argument("--speaker", help="a CustomVoice speaker, such as Ryan or Aiden")
    who.add_argument("--design", help="a description of the voice you want")
    what = p.add_mutually_exclusive_group(required=True)
    what.add_argument("--text")
    what.add_argument("--text-file")
    p.add_argument("--instruct", help="delivery note for --speaker (ignored by the other two)")
    p.add_argument("--takes", type=int, default=1)
    p.add_argument("--seed", type=int, help="default: a random one, printed and logged")
    p.add_argument("--out", help="folder for the takes (default out/takes/<timestamp>)")
    p.add_argument("--model", help="override the model, for example the 0.6B or a quantised version")
    p.add_argument("--language", default="english")
    p.add_argument("--temperature", type=float)
    p.add_argument("--top-p", type=float)
    p.add_argument("--repetition-penalty", type=float)
    a = p.parse_args()

    text = a.text if a.text is not None else open(a.text_file).read()
    text = " ".join(text.split())
    mode = "clone" if a.voice else "speaker" if a.speaker else "design"
    model_id = a.model or MODELS[mode]
    seed = a.seed if a.seed is not None else int.from_bytes(os.urandom(3), "big")
    out = a.out or os.path.join("out", "takes", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(out, exist_ok=True)
    sampling = {
        k: v
        for k, v in {"temperature": a.temperature, "top_p": a.top_p, "repetition_penalty": a.repetition_penalty}.items()
        if v is not None
    }

    if mode == "clone":
        ref_wav = os.path.join(a.voice, "reference.wav")
        ref_txt = os.path.join(a.voice, "reference.txt")
        if not (os.path.exists(ref_wav) and os.path.exists(ref_txt)):
            sys.exit(f"{a.voice} needs reference.wav and reference.txt (see voices/README.md)")
        ref_text = " ".join(open(ref_txt).read().split())

    print(f"loading {model_id} (the first run downloads it)", file=sys.stderr)
    t0 = time.perf_counter()
    model = load_model(model_id)
    load_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    takes: list[mx.array] = []
    if mode == "clone":
        # Every take of a clone is generated together in one batch: about as quick as one take on its own.
        mx.random.seed(seed)
        if a.takes == 1:
            takes = [joined(model.generate(text=text, ref_audio=ref_wav, ref_text=ref_text, lang_code=a.language, **sampling))]
        else:
            batch = model.batch_generate(
                texts=[text] * a.takes, ref_audio=ref_wav, ref_text=ref_text, lang_code=a.language, **sampling
            )
            takes = [audio for _, audio in sorted((r.sequence_idx, r.audio) for r in batch)]
    else:
        # The other two run one take at a time, each with its own seed (seed, seed + 1, ...).
        for i in range(a.takes):
            mx.random.seed(seed + i)
            if mode == "speaker":
                gen = model.generate_custom_voice(text=text, speaker=a.speaker, language=a.language, instruct=a.instruct, **sampling)
            else:
                gen = model.generate_voice_design(text=text, instruct=a.design, language=a.language, **sampling)
            takes.append(joined(gen))
    generate_s = time.perf_counter() - t1

    log = {
        "model": model_id,
        "mode": mode,
        "voice": a.voice or a.speaker or a.design,
        "instruct": a.instruct if mode == "speaker" else None,
        "text": text,
        "seed": seed,
        "takes": a.takes,
        "sampling": sampling,
        "files": [],
    }
    for i, audio in enumerate(takes, start=1):
        path = os.path.join(out, f"take-{i}.wav")
        seconds = write_wav(path, audio, model.sample_rate)
        log["files"].append({"take": i, "path": path, "seconds": round(seconds, 2)})
        print(f"take {i}: {seconds:.2f}s  {path}")
    with open(os.path.join(out, "takes.json"), "w") as f:
        json.dump(log, f, indent=2)
    peak = (mx.get_peak_memory() if hasattr(mx, "get_peak_memory") else mx.metal.get_peak_memory()) / 1e9
    print(f"seed {seed}; model loaded in {load_s:.1f}s, {a.takes} take(s) in {generate_s:.1f}s, peak memory {peak:.1f} GB; log in {out}/takes.json")


if __name__ == "__main__":
    main()
