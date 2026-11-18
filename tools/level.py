# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Brings takes to the same loudness so snippets match when they are joined. Uses ffmpeg.

    uv run tools/level.py audio/raw/*.wav --out audio/            # gain only (default)
    uv run tools/level.py audio/raw/*.wav --out audio/ --limit    # reach the target with a limiter

Loudness is measured in LUFS, the scale streaming services use. -16 LUFS is the usual target for
speech on the web and phones. Two ways to get there:

- Gain only (the default) turns the whole take up or down, nothing else, so it sounds exactly like
  the raw take. It stops short of the target if the take's loudest peak would pass -1.5 dBTP
  first. If some takes stop short, the script says so: pick a --lufs every take can reach (it
  prints the number), or use --limit.
- --limit gets to the target, or within a unit of it, with ffmpeg's loudnorm, which limits the loudest peaks.
  Louder, and more even, and to some ears flatter.

Writes mono 16-bit 48 kHz (the video standard) with the same file names into --out. A take's start
and length are never changed, so anything timed from the audio stays in place.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import wave

TRUE_PEAK = -1.5
RATE = 48000


def measure(path: str, extra: str = "") -> dict:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", f"{extra}loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr)
    if not m:
        sys.exit(f"could not measure {path}: {r.stderr.strip().splitlines()[-1:]}")
    return {k: float(v) if k != "normalization_type" else v for k, v in json.loads(m.group(0)).items()}


def seconds(path: str) -> float:
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--lufs", type=float, default=-16.0)
    p.add_argument("--limit", action="store_true")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)

    landed = []
    for src in a.files:
        dst = os.path.join(a.out, os.path.basename(src))
        if os.path.abspath(dst) == os.path.abspath(src):
            sys.exit(f"{src}: --out must be a different folder from the takes")
        m = measure(src)
        if a.limit:
            chain = (
                f"loudnorm=I={a.lufs}:TP={TRUE_PEAK}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
                f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
            )
            note = ""
        else:
            gain = min(a.lufs - m["input_i"], TRUE_PEAK - 0.1 - m["input_tp"])
            chain = f"volume={gain:.2f}dB"
            note = f"  gain {gain:+.1f} dB"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", src, "-af", f"{chain},aresample={RATE}", "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", dst],
            check=True,
        )
        drift = abs(seconds(dst) - seconds(src))
        if drift > 0.005:
            os.remove(dst)
            sys.exit(f"{src}: length changed by {drift * 1000:.0f} ms, refused")
        after = measure(dst)
        landed.append(after["input_i"])
        print(f"{after['input_i']:6.1f} LUFS  {after['input_tp']:5.1f} dBTP  {dst}{note}")

    short = [x for x in landed if x < a.lufs - 1]
    if short and not a.limit:
        print(
            f"{len(short)} of {len(landed)} takes stopped short of {a.lufs} LUFS to keep their peaks under {TRUE_PEAK} dBTP. "
            f"For takes that match, run again with --lufs={min(landed):.0f}, or use --limit."
        )


if __name__ == "__main__":
    main()
