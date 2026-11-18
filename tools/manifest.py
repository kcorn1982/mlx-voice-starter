# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Measures a folder of numbered snippets and writes manifest.json: every scene's length in seconds
and in video frames, and where it starts. A video tool such as Remotion reads this file instead of
anyone guessing how long a line takes to say.

    uv run tools/manifest.py audio/ --fps 30 --gap 0.5 --scenes scenes/ --relative-to . --out manifest.json

Snippets play in file-name order, so name them 01-hook.wav, 02-problem.wav and so on. The scene id
is the name without its number. --gap is the hold after each snippet before the next scene starts.
--scenes, if given, adds each scene's text from the matching .txt file (01-hook.txt). --relative-to
sets what the file paths in the manifest are relative to (for Remotion, its public/ folder, so each
path works with staticFile()).
"""

import argparse
import glob
import json
import math
import os
import re
import wave


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("audio_dir")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--gap", type=float, default=0.5, help="seconds held after each snippet")
    p.add_argument("--scenes", help="folder of matching .txt files")
    p.add_argument("--relative-to", default=".")
    p.add_argument("--out", default="manifest.json")
    a = p.parse_args()

    files = sorted(glob.glob(os.path.join(a.audio_dir, "*.wav")))
    if not files:
        raise SystemExit(f"no .wav files in {a.audio_dir}")
    scenes, start = [], 0
    for path in files:
        stem = os.path.splitext(os.path.basename(path))[0]
        if not re.match(r"^\d{2}-", stem):
            raise SystemExit(f"{path}: name it with a two-digit order first, like 01-{stem}.wav")
        with wave.open(path) as w:
            seconds = w.getnframes() / w.getframerate()
        frames = math.ceil((seconds + a.gap) * a.fps)
        scene = {
            "id": stem[3:],
            "file": os.path.relpath(path, a.relative_to),
            "seconds": round(seconds, 3),
            "startFrame": start,
            "durationInFrames": frames,
        }
        if a.scenes:
            txt = os.path.join(a.scenes, f"{stem}.txt")
            if os.path.exists(txt):
                scene["text"] = " ".join(open(txt).read().split())
        scenes.append(scene)
        start += frames

    manifest = {"fps": a.fps, "gapSeconds": a.gap, "totalFrames": start, "scenes": scenes}
    with open(a.out, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    for s in scenes:
        print(f"{s['startFrame']:6d}  {s['durationInFrames']:5d} frames  {s['seconds']:6.2f}s  {s['id']}")
    print(f"{len(scenes)} scenes, {start} frames ({start / a.fps:.1f}s at {a.fps} fps) -> {a.out}")


if __name__ == "__main__":
    main()
