# Voices

One folder per voice. Each holds two files.

| File | What it is |
|---|---|
| `reference.wav` | 15 to 30 seconds of the voice, mono, 24 kHz, 16-bit |
| `reference.txt` | Exactly the words said in that recording, word for word |

Use a voice with `uv run tools/say.py --voice voices/<name> --text "..."`.

`example-narrator` is synthetic. It was made from a written description with the VoiceDesign model, so it is nobody's real voice and is safe to share. Its `voice.json` records how it was made.

Your own `reference.wav` stays out of Git (see `.gitignore`). A recording this short is enough for anyone to clone you, so think twice before pushing one to a public repo. Only clone a voice with its owner's permission.
