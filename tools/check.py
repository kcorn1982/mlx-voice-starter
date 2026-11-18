# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["mlx-whisper==0.4.3"]
# ///
"""
Listens to takes with Whisper, locally, and compares what it hears with what the text says.

    uv run tools/check.py out/takes/<run>/take-*.wav --text "The line the takes should say."
    uv run tools/check.py voices/me/reference.wav --text-file voices/me/reference.txt

For each file it prints the share of the text's words heard in order, the words that were missing
or extra, the take's length and its speaking rate. Takes are listed best first. A take much shorter
or faster than the others in its batch is usually rushed or has swallowed words, even when it scores
well. A take at 100% can still sound wrong, so listen to the top few. This only tells you which ones
are worth your ears.

Use it on a new reference recording too. The transcript has to match the recording word for word,
because the model clones by carrying on from the reference: a word in the text that the audio
never says tends to turn up at the start of every take.
"""

import argparse
import difflib
import re
import wave

import mlx_whisper

MODEL = "mlx-community/whisper-small-mlx"


def words(text: str) -> list[str]:
    """Lower case, punctuation gone, hyphens as spaces, so "built-in" and "built in" match."""
    return [w for w in (re.sub(r"[^a-z0-9']", "", t.lower()) for t in re.split(r"[\s\-]+", text)) if w]


def seconds(path: str) -> float:
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def check(path: str, script: str) -> dict:
    result = mlx_whisper.transcribe(path, path_or_hf_repo=MODEL, word_timestamps=True, language="en", verbose=None)
    heard = [w for s in result["segments"] for w in s.get("words", [])]
    a = words(script)
    b = words(" ".join(w["word"] for w in heard))
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    matched = sum(block.size for block in sm.get_matching_blocks())
    missing, extra = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace"):
            missing.append(" ".join(a[i1:i2]))
        if op in ("insert", "replace"):
            extra.append(" ".join(b[j1:j2]))
    return {
        "path": path,
        "score": matched / max(1, len(a)),
        "missing": missing,
        "extra": extra,
        "seconds": seconds(path),
        "rate": len(b) / heard[-1]["end"] if heard and heard[-1]["end"] > 0 else 0.0,
        "heard": result["text"].strip(),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+")
    what = p.add_mutually_exclusive_group(required=True)
    what.add_argument("--text")
    what.add_argument("--text-file")
    a = p.parse_args()
    script = a.text if a.text is not None else open(a.text_file).read()
    results = sorted((check(f, script) for f in a.files), key=lambda r: -r["score"])
    for r in results:
        print(f"{r['score']:6.1%}  {r['seconds']:5.2f}s  {r['rate']:.1f} words/s  {r['path']}")
        if r["missing"]:
            print(f"        missing: {' | '.join(r['missing'])}")
        if r["extra"]:
            print(f"        extra:   {' | '.join(r['extra'])}")
        if r["score"] < 1:
            print(f"        heard:   {r['heard']}")


if __name__ == "__main__":
    main()
