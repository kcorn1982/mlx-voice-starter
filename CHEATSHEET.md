# Audio cheat sheet

What you can change about a narration take, where you change it, and the command that does it. Every command here was run on a Qwen3-TTS take with ffmpeg 9 and mlx-audio 0.6.4 on 18 November 2026.

There are three places to change a take. **Before recording** you change the reference and the words. **At recording** you change the model's settings. **After recording** you process the file with ffmpeg or Python. The earlier the change, the more natural the result, so reach for the first two before the third.

Two habits make the rest safe.

- **Keep the raw take untouched** and run every change on a copy, starting from raw each time. Then any change can be undone or retuned.
- **Compare at the same loudness.** The louder of two versions nearly always sounds better, so level both before you judge (`tools/level.py`). Change one thing at a time.

## Contents

- [At recording time (mlx-audio and Qwen3-TTS)](#at-recording-time-mlx-audio-and-qwen3-tts)
- [Tone, bass and treble](#tone-bass-and-treble)
- [Loudness and dynamics](#loudness-and-dynamics)
- [Gaps, pauses and timing](#gaps-pauses-and-timing)
- [Looking and measuring](#looking-and-measuring)
- [Python libraries](#python-libraries)
- [Settings that passed an ear test](#settings-that-passed-an-ear-test)

## At recording time (mlx-audio and Qwen3-TTS)

| Setting | What it changes | Works with | Notes |
|---|---|---|---|
| The reference recording | Pace, energy, accent, mic and room of every take | Base (clone) | The biggest lever by far. Re-record it rather than fight it afterwards |
| The text | Rises, run-ons, mispronunciations | All | Reword the sentence or respell a word in the text sent to the voice. See the README's words list |
| `--takes` | How many takes to choose from | All | Clone takes are batched, so 8 cost about what 2 or 3 would one at a time |
| `--seed` | Which takes you get | All | Same text, voice, model, seed and takes give identical audio |
| `--temperature` | Variety. Default 0.9 | All | Lower (0.7) steadier and flatter, higher livelier with more slips |
| `--top-p` | How far down the list of likely sounds it may pick. Default 1.0 | All | Lower narrows the choice, like a lower temperature |
| top-k | The same idea as a count. Default 50 | All | Not exposed in `say.py`. Pass `top_k=` in your own code |
| `--repetition-penalty` | Discourages repeating sounds. Default 1.05 | All | Raise slightly if a take loops or stutters |
| `max_tokens` | Hard cap on length | All | A safety net against a take that runs on. About 12 tokens a second of speech |
| `--instruct` | Delivery ("calm and warm", "a little faster") | CustomVoice only | Ignored by a cloned voice. The Base model has no way to apply it |
| `--design` | The voice itself, from a description | VoiceDesign | Drifts between runs. Design once, then clone the take you like |
| `--speaker` | One of nine built-in voices | CustomVoice | Ryan and Aiden are the native English speakers |
| `--language` | Language of the text | All | `english` by default in `say.py` |
| `--model` | Size and precision | All | 1.7B or 0.6B, `bf16` down to `4bit`. Smaller is lighter and a little rougher |
| `speed` | Nothing | None | Accepted but not applied by Qwen3-TTS in mlx-audio 0.6.4 ("not directly supported yet"). Change pace after recording |
| `stream=True` | Audio arrives in chunks as it's made | All | For live playback. Not needed for files |

## Tone, bass and treble

All of these run as `ffmpeg -i in.wav -af "<filters, comma separated>" out.wav`. None of them changes the take's length.

| You want | Filter | Example |
|---|---|---|
| More bass, warmth | `bass` or `lowshelf` | `bass=g=3:f=120` or `lowshelf=f=130:g=3` |
| Less rumble, handling noise | `highpass` | `highpass=f=70` |
| Less boxy or muddy | `equalizer` (cut) | `equalizer=f=300:t=q:w=1.2:g=-2` |
| More presence, clearer words | `equalizer` (boost) | `equalizer=f=3500:t=q:w=1:g=2` |
| Less harsh or bright | `treble` or `highshelf` | `treble=g=-1.5:f=7500` |
| Softer "s" sounds | `deesser` | `deesser=i=0.35` |
| Less hiss or background noise | `afftdn` | `afftdn=nr=12:nf=-50:tn=1` |
| A deeper or higher voice | `asetrate` then `aresample` | `asetrate=24000*0.97,aresample=24000` (3% lower) |

`g` is the gain in decibels (plus to boost, minus to cut), `f` the frequency in hertz, `w` how wide the band is. Keep moves small. Two or three decibels is clearly audible on a voice.

**The pitch trick changes length too.** `asetrate` slows the take as it lowers it (10.48 s became 10.80 s at 3%), so do it before you measure timings.

## Loudness and dynamics

| You want | Tool | Example |
|---|---|---|
| To know how loud a take is | `ebur128`, `loudnorm`, `volumedetect` | `ffmpeg -i in.wav -af ebur128 -f null -` (read `I:` in the summary) |
| Turn it up or down, nothing else | `volume` | `volume=3dB` |
| Hit a loudness target | `loudnorm`, or `tools/level.py --limit` | `loudnorm=I=-16:TP=-1.5:LRA=11` |
| Match a set of takes, sound unchanged | `tools/level.py` | `uv run tools/level.py audio/raw/*.wav --out audio/` |
| Even out loud and quiet words | `acompressor` | `acompressor=threshold=-22dB:ratio=2.5:attack=15:release=220:knee=6` |
| Stop peaks going over a ceiling | `alimiter` | `alimiter=limit=0.84:level=false` (0.84 is -1.5 dB) |
| Even out level across a long recording | `speechnorm`, `dynaudnorm` | `speechnorm=e=6.25:r=0.00001:l=1` |

Compression turns the take down. A test take went from -22 to -28 LUFS through the compressor above. So level after any processing, never before.

Be careful with anything that squashes the voice. On my takes a limiter and compressor made every take sound worse, not just louder, and I went back to gain only. Try it on one scene and compare by ear first.

## Gaps, pauses and timing

| You want | Tool | Example |
|---|---|---|
| To find the gaps | `silencedetect` | `ffmpeg -i in.wav -af "silencedetect=n=-35dB:d=0.25" -f null -` |
| Silence after the last word | `apad` | `apad=pad_dur=0.25` |
| Silence before the first word | `adelay` | `adelay=300:all=1` (300 ms) |
| Trim silence off the start | `silenceremove` | `silenceremove=start_periods=1:start_threshold=-50dB` |
| Slower or faster, same pitch | `atempo` | `atempo=0.94` (6% slower, 10.48 s became 11.14 s) |
| No click at the edges | `afade` | `afade=t=in:d=0.02,areverse,afade=t=in:d=0.05,areverse` |
| Join two takes smoothly | `acrossfade` | `ffmpeg -i a.wav -i b.wav -filter_complex "[0][1]acrossfade=d=0.05" ab.wav` |
| Where every word starts and ends | mlx-whisper | `word_timestamps=True`, as in `tools/check.py` |
| Longer pauses between sentences only | Whisper plus numpy | Find sentence ends from word timings, measure the gap, insert silence. No single filter does it |

`silencedetect` prints each gap like this. The 0.73 s one is the pause at a full stop.

```text
silence_start: 5.049292
silence_end: 5.782292 | silence_duration: 0.733
```

`n` is how quiet counts as silence and `d` the shortest gap to report. A gap under about 0.3 s at a full stop usually sounds rushed. A gap in the middle of a clause sounds like a stumble.

**Anything that changes length goes before `tools/manifest.py`**, so the video's timings come from the finished file.

## Looking and measuring

| You want | Tool | Example |
|---|---|---|
| A picture of the waveform | `showwavespic` | `ffmpeg -i in.wav -filter_complex "showwavespic=s=1600x240" -frames:v 1 wave.png` |
| A picture of the frequencies (spot hiss, hum, rumble) | `showspectrumpic` | `ffmpeg -i in.wav -lavfi "showspectrumpic=s=1200x400" spec.png` |
| Length in seconds | `ffprobe` | `ffprobe -v error -show_entries format=duration -of csv=p=0 in.wav` |
| Whether an ending rises like a question | praat-parselmouth | Pitch of the last word against the take's median, in semitones |
| Whether a vowel is right | praat-parselmouth | Formants of the stressed vowel |
| Loudness in Python | pyloudnorm | `pyln.Meter(rate).integrated_loudness(data)` |

## Python libraries

Run any of them with `uv run --with <package> python my_script.py`, with nothing installed globally.

| Library | Good for |
|---|---|
| [pedalboard](https://github.com/spotify/pedalboard) | EQ, compression, gates, reverb and pitch shifting in Python, fast |
| [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) | Loudness in LUFS |
| [soundfile](https://github.com/bastibe/python-soundfile) and numpy | Reading and writing audio, and any edit you can write as arithmetic (inserting silence, cutting at a sample) |
| [praat-parselmouth](https://github.com/YannickJadoul/Parselmouth) | Pitch, formants and voice measures from Praat |
| [mlx-whisper](https://pypi.org/project/mlx-whisper/) | The words in a take and when each one is said |
| [librosa](https://librosa.org) | Analysis, time-stretching and pitch-shifting |
| [noisereduce](https://github.com/timsainb/noisereduce) | Removing steady background noise |
| [pydub](https://github.com/jiaaro/pydub) | Simple slicing and joining (uses ffmpeg) |

The tone settings from the next section, as a pedalboard chain.

```python
from pedalboard import Pedalboard, HighpassFilter, LowShelfFilter, PeakFilter, HighShelfFilter
from pedalboard.io import AudioFile

with AudioFile("in.wav") as f:
    audio, sr = f.read(f.frames), f.samplerate
board = Pedalboard([
    HighpassFilter(70),
    LowShelfFilter(cutoff_frequency_hz=130, gain_db=3),
    PeakFilter(cutoff_frequency_hz=3500, gain_db=2, q=1),
    HighShelfFilter(cutoff_frequency_hz=7500, gain_db=-1.5),
])
with AudioFile("out.wav", "w", sr, audio.shape[0]) as f:
    f.write(board(audio, sr))
```

## Settings that passed an ear test

Settings I chose by listening, as starting points.

| Job | Setting | What it fixed |
|---|---|---|
| A dull voice with noise between words | `afftdn=nr=12:nf=-50:tn=1, equalizer=f=300:t=q:w=1.2:g=-2, equalizer=f=3500:t=q:w=1:g=2, lowshelf=f=130:g=3` | "A little cleaner and with slightly more bass". Picked from five versions. A deeper pitch was tried and not chosen |
| General clean-up for a server-made voice | `highpass=f=70, deesser=i=0.35, acompressor=threshold=-22dB:ratio=2.5:attack=15:release=220:knee=6, treble=g=-1.5:f=7500` | Rumble, sibilance, uneven words, edge on top |
| Qwen3-TTS takes through mlx-audio | Gain only, to one level every take reaches, no limiter | The raw sound was preferred to every processed version |
| The end of every take | 0.25 s of silence (`apad`) | Last consonants cut off at the end of the file |
| Pauses at full stops | Stretched to 0.6 s where shorter, commas left alone | Lines felt rushed. A full second everywhere broke the flow |
| Pace | Longer pauses, not slower words | `atempo` slowing was tried and not chosen |
