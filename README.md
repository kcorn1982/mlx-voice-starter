# MLX Voice Starter

Narration in your own voice, made on your own Mac. Nothing is uploaded and nothing is paid for per word.

This is the setup behind my explainer videos, stripped back to the parts anyone can reuse. It runs Qwen3-TTS, an open text-to-speech model from Alibaba's Qwen team, through mlx-audio, which runs models on the graphics chip inside every Apple silicon Mac. You give it a short recording of a voice and the exact words in it. It then reads any text you like in that voice.

**Two ways to use this.** If you use Claude Code, open this folder and tell it what you want narrated. `CLAUDE.md` gives it the working rules. It runs the commands, checks the takes, and stops for you to listen, because you choose every take by ear. If you'd rather run it yourself, everything is below, with the command for each step.

**Where this started.** My first attempts went through [Voicebox](https://voicebox.sh), a free, open-source app for cloning voices and generating speech on your own computer. It runs Qwen3-TTS too, and has an MCP server so agents can use it. On a Mac, working directly with Claude Code, I found that calling mlx-audio from scripts gave quicker and more accurate takes than going through the Voicebox MCP, so that's what this repo does. If you'd rather work in an app than through an agent, Voicebox is a really good project and well worth a look. It runs on Windows and Linux as well as macOS.

The README covers four things, in order. How to set it up. Which models to download and what each one is for. How to make your own voice, or use another one, and tweak it until it sounds right. And the working rhythm I use for real videos, short snippets recorded one at a time and then joined by an agent into a finished video in a tool like Remotion.

## Contents

- [What's in the box](#whats-in-the-box)
- [What you need](#what-you-need)
- [Set up](#set-up)
- [The models](#the-models)
- [Make your own voice](#make-your-own-voice)
- [Use another voice](#use-another-voice)
- [Getting it to sound right](#getting-it-to-sound-right)
- [Checking takes](#checking-takes)
- [The cadence](#the-cadence)
- [Joining snippets with an agent](#joining-snippets-with-an-agent)
- [Troubleshooting](#troubleshooting)
- [Going further](#going-further)
- [Audio cheat sheet](CHEATSHEET.md)
- [Credits and licences](#credits-and-licences)

## What's in the box

| Path | What it does |
|---|---|
| `tools/say.py` | Speaks a line and writes one or more takes. Your cloned voice, a built-in speaker, or a voice described in words |
| `tools/check.py` | Listens to takes with Whisper, locally, and ranks them by how closely they match the text |
| `tools/level.py` | Brings takes to the same loudness so joined snippets match |
| `tools/manifest.py` | Measures the finished snippets and writes `manifest.json`, the timings a video tool reads |
| `voices/` | One folder per voice. `example-narrator` is a synthetic voice you can try straight away |
| `scenes/` | The script, one short text file per scene |
| `CLAUDE.md` | Working rules for an AI agent (Claude Code or similar) in this project |
| `CHEATSHEET.md` | Everything you can change about a take, from model settings to bass, treble and gaps, with the command for each |

Each script carries its own dependencies in its header, so `uv` builds the right Python environment the first time you run it. There is no `pip install` step and no virtual environment to manage.

## What you need

- **A Mac with Apple silicon** (M1 or later). MLX only runs on Apple's own chips, so Intel Macs, Windows and Linux are out.
- **Memory.** 32 GB is comfortable. Measured on an M5 with 32 GB, the 1.7B model peaks at about 10 GB for a batch of eight takes and the 0.6B 8-bit model at about 7 GB, so a 16 GB Mac should manage with fewer takes or a smaller model. I haven't tried one.
- **Disk.** About 4 GB for each full-size 1.7B model, less for the smaller ones, plus under 1 GB for Whisper. Models are stored once, in `~/.cache/huggingface/hub`, and shared by every project on the Mac.
- **Homebrew**, to install the two command-line tools below. Get it from [brew.sh](https://brew.sh).

## Set up

**1. Install uv and ffmpeg.** `uv` runs the Python scripts and fetches their packages. `ffmpeg` handles audio files.

```bash
brew install uv ffmpeg
```

**2. Get this repo.**

```bash
git clone <this repo's URL> mlx-voice-starter
cd mlx-voice-starter
```

**3. Make your first sound with a built-in speaker.** The first run downloads the model (about 4 GB, a few minutes), so be patient once.

```bash
uv run tools/say.py --speaker Ryan --text "This is my first line, spoken on my own Mac." --out out/first
open out/first/take-1.wav
```

**4. Try the cloned voice.** This uses the example voice in `voices/example-narrator` and downloads the Base model on its first run.

```bash
uv run tools/say.py --voice voices/example-narrator --text "This voice was cloned from a twenty second recording." --takes 4 --out out/clone
open out/clone
```

If you hear both, everything works. You'll see a warning starting `[transformers] You are using a model of type qwen3_tts`. It's harmless, so ignore it.

Every run writes the takes, plus a `takes.json` recording the model, voice, text and seed. The same text, voice, model, seed and number of takes produce the identical audio again (I checked byte for byte), so a take you like is never lost.

## The models

Qwen3-TTS comes in three kinds. Each kind does a different job, and `say.py` picks the right one from the flag you use.

| Kind | What it does | Flag | Default model |
|---|---|---|---|
| **Base** | Clones a voice from a short recording and its transcript | `--voice` | `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16` |
| **CustomVoice** | Nine built-in speakers, and takes a delivery note such as "calm and warm" | `--speaker`, `--instruct` | `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16` |
| **VoiceDesign** | Invents a voice from a written description | `--design` | `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16` |

**Sizes.** 1.7B is the better model and the one I use. 0.6B is smaller and comes in Base and CustomVoice only (no VoiceDesign).

**Precision.** Each model is published at several precisions, the last part of its name. `bf16` is the full model. `8bit`, `6bit`, `5bit` and `4bit` are compressed copies, smaller to download and lighter on memory, at some cost to quality. Swap any of them in with `--model`.

```bash
uv run tools/say.py --voice voices/example-narrator --model mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit --text "..." --takes 8
```

In my test the 0.6B 8-bit model cloned well, but one take in eight cut off its last word. Start with 1.7B `bf16` and only step down if memory forces you to.

**The built-in speakers.** CustomVoice has nine, listed with Qwen's own descriptions on the [model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice). Pass the name exactly as written to `--speaker`.

| Speaker | Qwen's description | Native language |
|---|---|---|
| Ryan | Dynamic male voice with strong rhythmic drive | English |
| Aiden | Sunny American male voice with a clear midrange | English |
| Vivian | Bright, slightly edgy young female voice | Chinese |
| Serena | Warm, gentle young female voice | Chinese |
| Uncle_Fu | Seasoned male voice with a low, mellow timbre | Chinese |
| Dylan | Youthful Beijing male voice with a clear, natural timbre | Chinese (Beijing dialect) |
| Eric | Lively Chengdu male voice with a slightly husky brightness | Chinese (Sichuan dialect) |
| Ono_Anna | Playful Japanese female voice with a light, nimble timbre | Japanese |
| Sohee | Warm Korean female voice with rich emotion | Korean |

Every speaker can read all ten of the model's languages (Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish and Italian), but sounds best in its own. For English narration, start with Ryan or Aiden. The others read English with an accent.

**Other models.** mlx-audio runs many other text-to-speech models too (Kokoro, Chatterbox, Dia, Sesame CSM, Spark and more; see [its repo](https://github.com/Blaizzy/mlx-audio)). This starter is built and tested on Qwen3-TTS only, and the scripts call Qwen3-TTS functions directly.

## Make your own voice

The Base model doesn't learn your voice by training. It listens to your recording, reads its transcript, and then carries on talking as if it were still you. That has one big consequence. **Every take sounds the way your reference sounds.** Its pace, energy, accent, microphone and room all come through. So the reference is worth twenty minutes of care.

**1. Write what you'll say.** Three to five sentences, 20 to 30 seconds read aloud, in the style you want every video to have. If you narrate calmly, read calmly. Mine is a 27-second paragraph read like the opening of a tutorial.

**2. Record it.** A quiet room with soft furnishings, the microphone a hand's width or two from your mouth, one clean take with no music and no edits in the middle of a sentence. A phone's voice memo app works. A USB microphone is better. Leave half a second of silence at each end.

**3. Convert it** to the format the model expects (mono, 24 kHz, 16-bit).

```bash
mkdir -p voices/me
ffmpeg -i my-recording.m4a -ac 1 -ar 24000 -sample_fmt s16 voices/me/reference.wav
```

To cut it down, add `-ss 1.2 -to 26.5` (start and end in seconds) before the output file.

**4. Write the transcript** into `voices/me/reference.txt`. It must match the recording word for word, including any slip you left in. This matters more than anything else on this page. The model clones by continuing the reference, so a word in the text that the audio never says tends to turn up at the start of every take. Check it.

```bash
uv run tools/check.py voices/me/reference.wav --text-file voices/me/reference.txt
```

You want 100%. Anything less, and it prints what it heard, so fix the text or re-record.

**5. Try it.**

```bash
uv run tools/say.py --voice voices/me --text "A short test line in my own voice." --takes 8 --out out/me-test
```

If it doesn't sound like you, the fix is almost always a better reference, not a setting.

**Keep it private.** A recording this short is enough for anyone to clone you. `.gitignore` keeps every `reference.wav` out of Git except the synthetic example. And only ever clone a voice with its owner's permission.

## Use another voice

**A built-in speaker** needs nothing but a name. CustomVoice is also the only kind that follows a delivery note.

```bash
uv run tools/say.py --speaker Aiden --instruct "Upbeat and friendly, a little faster." --text "..."
```

**A designed voice** comes from a description.

```bash
uv run tools/say.py --design "A warm, low female voice, unhurried, Scottish accent." --text "..." --takes 3
```

VoiceDesign invents the voice afresh on every run, so the same description can drift from one line to the next. A video needs the same voice in every scene, so **design once, then clone**. Generate a 20-second paragraph with your description, pick the take you like, and make it a reference. That's exactly how `voices/example-narrator` was made (its `voice.json` has the details).

```bash
mkdir -p voices/my-narrator
uv run tools/say.py --design "<your description>" --text-file my-paragraph.txt --takes 3 --out out/design
cp out/design/take-2.wav voices/my-narrator/reference.wav     # the take you liked
cp my-paragraph.txt voices/my-narrator/reference.txt
uv run tools/check.py voices/my-narrator/reference.wav --text-file voices/my-narrator/reference.txt
```

From then on `--voice voices/my-narrator` gives you that voice every time.

## Getting it to sound right

These are the levers, biggest first. Change one at a time and keep `--seed` fixed while you compare, so you're only hearing the change.

**1. The reference.** If every take is too fast, too flat or too bright, the reference is. Re-record it the way you want the takes to sound. A delivery note (`--instruct`) won't help here. The Base model has no way to apply one to a cloned voice, so `say.py` only sends it with `--speaker`.

**2. The words.** Most bad takes are bad sentences. These patterns failed again and again in my videos, and rewording fixed them where more takes didn't.

- A short sentence ending on a plain noun ("You choose the recipe.") tends to rise like a question. Give it a fuller ending or join it to the next sentence.
- A sentence that opens with And, But or So gets run straight on from the one before. Drop the joining word.
- A verbless list or fragment as its own sentence ("A club, a side project, a hobby.") goes high. Put it inside a full sentence.
- A question answered in a fragment ("Can it be fixed? Some of it can.") sings the question and rushes the answer. Make it a statement.
- Colons make the voice pause unpredictably. Write two sentences instead.
- Ending on a pronoun or a preposition ("will fix it", "find them in") rises. End on a content word of two or more syllables where you can.
- Years and figures come out better written as words ("twenty twelve", not "2012").
- Keep each scene to about 12 to 20 seconds. Every sentence boundary is another chance for a take to go wrong.

For words it says wrongly, respell them in the text you send to the voice only, never in your script or on-screen text. "Cache" came out as "catching" until I sent "cash". Acronyms read better spaced ("S Q L"). Keep a list of these and apply it to each scene before recording.

**3. More takes.** Takes of a clone are generated together in one batch, so eight cost roughly what two or three would cost one at a time. On an M5 with 32 GB, eight takes of a seven to ten second line usually took 20 to 45 seconds, now and then over a minute, and a single take on its own about 16 seconds. Record eight, check them, listen to the best few.

**4. Sampling settings.** The model's defaults are temperature 0.9, top-k 50, top-p 1.0 and repetition penalty 1.05. In general, a lower temperature (try 0.7) gives steadier, flatter takes and a higher one livelier takes with more mistakes. Try `--temperature`, `--top-p` and `--repetition-penalty` only after the reference and the words are right.

**5. After recording.** Loudness is set with `tools/level.py` (see [the cadence](#the-cadence)). Pace is a judgement call. I found the model's own pauses between sentences a little short and now lengthen them after recording rather than asking for slower speech, which it ignores. Bass, treble, noise, gaps and pace all have a command in [the cheat sheet](CHEATSHEET.md).

**What doesn't work.** Fiddling with punctuation to fix a delivery problem. I once swapped a colon for a comma and measured no change at all. Rewriting the sentence fixed it.

## Checking takes

```bash
uv run tools/check.py out/takes/01-hook/take-*.wav --text-file scenes/01-hook.txt
```

Whisper listens to each take on your Mac and the script prints them best first.

```text
100.0%   7.52s  2.3 words/s  out/test/speaker/take-1.wav
 88.2%   4.24s  4.1 words/s  out/test/speaker/take-2.wav
        missing: mac's own
        extra:   max owned
        heard:   This is a first test of a built-in voice running on the Max-owned graphics chip.
```

The percentage is how many of your words it heard, in order. Below 100% it shows what went missing and what it heard instead. Length and speaking rate catch rushed takes. Take 2 above said "Max-owned" for "Mac's own" and ran at nearly twice the speed of take 1.

**The checker only tells you which takes deserve your ears.** It can't hear a sentence that rises like a question, a stutter, or a word that's one letter off ("catching" for "caching" sounds wrong to you but passes). So listen to the top two or three and choose by ear.

## The cadence

Don't record a whole script in one go. A long take has more places to go wrong, and if the voice is off you find out after the whole lot is done. Work in short snippets, one scene at a time, and listen as you go.

**The unit.** One scene is one idea, 12 to 20 seconds, one text file and one audio file. Number the files in the order they play (`01-hook`, `02-how-it-works`) so every folder sorts in listening order.

**The loop.**

1. **Write the scenes** as `scenes/01-hook.txt`, `scenes/02-how-it-works.txt` and so on. Read them aloud once and fix anything from [the words](#getting-it-to-sound-right) list before you record.
2. **Record the first scene.** Eight takes, then check them.

   ```bash
   uv run tools/say.py --voice voices/me --text-file scenes/01-hook.txt --takes 8 --out out/takes/01-hook
   uv run tools/check.py out/takes/01-hook/take-*.wav --text-file scenes/01-hook.txt
   ```

3. **Listen to the best two or three and keep one.** It goes into `audio/raw/` under the scene's name.

   ```bash
   mkdir -p audio/raw
   cp out/takes/01-hook/take-3.wav audio/raw/01-hook.wav
   ```

4. **Stop after the first scene or two and listen properly.** If the voice is wrong, fix the reference now, before ten scenes are recorded in it.
5. **Record the rest, one scene at a time.** If a scene has no good take after two batches, reword the line. Another batch rarely saves a sentence the voice can't land.
6. **Redo only what's flagged.** One scene changes, one scene is re-recorded. The `takes.json` beside each take keeps its seed, so any take can be made again exactly.
7. **Level them all together** so the scenes match.

   ```bash
   uv run tools/level.py audio/raw/*.wav --out audio/
   ```

   By default this only turns each take up or down, so it sounds exactly like the raw take, and it stops short of the target (-16 LUFS, the usual level for speech online) rather than let a peak distort. If any take stops short it tells you a level every take can reach. Run again with that (`--lufs=-19`, say) so all scenes match. Or use `--limit` to hit -16 every time with a limiter. Louder and more even, but to my ear flatter. I chose gain only.

8. **Measure them.**

   ```bash
   uv run tools/manifest.py audio/ --scenes scenes/ --fps 30 --gap 0.5
   ```

   This writes `manifest.json`, every scene's file, length, text, and its start and duration in video frames. `--gap` is how long each scene holds after its last word. Here is the real one for the three example scenes in `scenes/`.

```json
{
  "fps": 30,
  "gapSeconds": 0.5,
  "totalFrames": 809,
  "scenes": [
    {
      "id": "hook",
      "file": "audio/01-hook.wav",
      "seconds": 7.76,
      "startFrame": 0,
      "durationInFrames": 248,
      "text": "Every word you hear in this video was made on a laptop, from a line of text and a short recording of a voice."
    },
    {
      "id": "how-it-works",
      "file": "audio/02-how-it-works.wav",
      "seconds": 10.48,
      "startFrame": 248,
      "durationInFrames": 330,
      "text": "The model listens to that recording, along with the exact words it says. Then it carries on speaking in the same voice, reading whatever text you give it next."
    },
    {
      "id": "close",
      "file": "audio/03-close.wav",
      "seconds": 7.2,
      "startFrame": 578,
      "durationInFrames": 231,
      "text": "Record one scene at a time, listen as you go, and keep only the takes that sound right to you."
    }
  ]
}
```

**A project folder ends up like this.**

```text
scenes/          01-hook.txt, 02-how-it-works.txt, ...     the script
out/takes/       01-hook/take-1.wav ... takes.json         every take, kept until you're done
audio/raw/       01-hook.wav, ...                          the take you chose, untouched
audio/           01-hook.wav, ...                          levelled, what the video uses
manifest.json                                              timings, written by manifest.py
```

## Joining snippets with an agent

Once the snippets exist, an agent such as Claude Code can build the video around them. The trick is to give it a contract it can't fudge. **The audio sets the timing, and the manifest is the only place timings come from.** An agent left to itself will guess that a line takes "about eight seconds" and hard-code it. Then you re-record a scene and the picture drifts out of step.

`CLAUDE.md` in this repo holds those rules. Copy them into your video project's own `CLAUDE.md`. The ones that matter most are these.

- Never estimate a duration. Read it from `manifest.json`.
- Never put narration text, durations or audio paths in components. They arrive from the manifest as props.
- Never hand-edit `manifest.json` or the audio. Regenerate them.
- Redo one scene at a time, and the person listening chooses the take.

**With Remotion**, put the levelled snippets in Remotion's `public/` folder and write the paths relative to it, so they work with `staticFile()`.

```bash
mkdir -p ../my-video/public/audio
cp audio/*.wav ../my-video/public/audio/
uv run tools/manifest.py ../my-video/public/audio --scenes scenes/ --relative-to ../my-video/public --out ../my-video/src/manifest.json
```

Then one component plays every scene in order, with nothing hard-coded.

```tsx
import { AbsoluteFill, Audio, Composition, Sequence, staticFile } from "remotion";
import manifest from "./manifest.json";

export const Narration = () => (
  <AbsoluteFill>
    {manifest.scenes.map((scene) => (
      <Sequence key={scene.id} from={scene.startFrame} durationInFrames={scene.durationInFrames}>
        <Audio src={staticFile(scene.file)} />
        {/* your visuals for this scene, picked by scene.id */}
      </Sequence>
    ))}
  </AbsoluteFill>
);

export const Root = () => (
  <Composition id="Narration" component={Narration} durationInFrames={manifest.totalFrames} fps={manifest.fps} width={1920} height={1080} />
);
```

**A prompt to start the agent with.**

```text
Read CLAUDE.md and manifest.json. Build a Remotion composition that plays each scene's
audio in order, using startFrame and durationInFrames from the manifest and nothing else
for timing. Each scene gets its own visual, chosen by scene.id. Show me the first two
scenes in the studio before building the rest.
```

**When a scene changes**, re-record that scene, run `level.py` and `manifest.py` again, and copy the new file across. The video picks up the new length by itself.

## Troubleshooting

| What you see | What to do |
|---|---|
| The first run sits for minutes | It's downloading the model. Later runs load in a couple of seconds |
| `[transformers] You are using a model of type qwen3_tts...` | Harmless. Ignore it |
| The same stray words at the start of every take | `reference.txt` doesn't match the recording. Run `check.py` on the reference and fix the text |
| A take is much shorter or faster than the rest | It's rushed or has swallowed words. Discard it |
| The last word is cut off | Listen for it, and prefer sentences that end on a vowel or a longer word. Short words ending in "-ts" ("costs", "acts") are the usual victims |
| Out of memory, or the Mac crawls | Fewer `--takes`, an 8-bit model, or the 0.6B. Close other apps using the graphics chip |
| `There is no Stream(gpu, N) in current thread` | This happens when MLX is driven from a server's worker threads. Run one process per job, as `say.py` does |
| A word is said wrongly every time | Respell it in the text sent to the voice (see [the words](#getting-it-to-sound-right)) |

## Going further

My own pipeline adds checks this starter leaves out. It catches sentences that rise at the end by measuring pitch, lengthens short pauses between sentences after recording, and writes subtitles from Whisper's word timings. They're worth building once the basics are second nature, and they're the natural next additions here.

## Credits and licences

- [mlx-audio](https://github.com/Blaizzy/mlx-audio), MIT licence. Pinned at 0.6.4 in `say.py`.
- [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base) by the Qwen team at Alibaba, Apache 2.0. The MLX conversions are from [mlx-community](https://huggingface.co/mlx-community).
- [Whisper](https://github.com/openai/whisper) by OpenAI, through [mlx-whisper](https://pypi.org/project/mlx-whisper/), for checking takes.
