# Narration, score and mix

## Sumi Studio MCP basics

The Sumi MCP generates with the connected user's own account, so every paid call spends their credits.

The model names, parameters, prices and preferred musical treatment below record the Suzhou production in November 2026. Check current model schemas and quotes before submitting; choose the number of takes within the user's authorized budget and stop at that limit.

- Before a paid call, say what it does and roughly what it costs, unless the user has already approved that kind of generation for this project. `estimate_task` is free; `quote_task` gives a binding quote.
- `get_model {model}` lists a model's parameters (voices, emotions, prosody ranges, extra params).
- `create_generation_task {taskType, modelKey, input, idempotencyKey}` charges and returns a task id at once. Reuse the same idempotency key only to retry the same request.
- `wait_task {taskId}` until it succeeds; `get_asset_download_url {assetId}` for the original file (each download counts toward a monthly quota). Download with curl into the project and keep every take with a descriptive name.

## Narration: MiniMax TTS 2.8 HD (`speech-2.8-hd`)

```json
{"taskType": "text_to_audio", "modelKey": "speech-2.8-hd",
 "input": {"prompt": "<the whole script, one line per sentence>",
           "voice": "Chinese (Mandarin)_Lyrical_Voice", "emotion": "calm", "speed": 1,
           "audioFormat": "wav", "sampleRate": "44100", "languageBoost": "Chinese",
           "pronunciationDict": ["阊门/(chang1)(men2)", "相门/(xiang1)(men2)", "枕河/(zhen3)(he2)"]}}
```

- **One take for the whole script,** split into lines at the silences (`example/suzhou/vo/split.py`). A single take keeps the voice, room and energy consistent across the film.
- **Natural speed.** The first cut sped narration up 1.2× to fit 165 s and the user heard it as rushed. At speed 1 the film went from 165 s to about 260 s, and the picture stretched to fit (`plan_warp.py`).
- **Re-voice single lines with the same voice, emotion and speed,** and check the new take's pitch against the rest with `qa_pitch.py`. The Suzhou narration sat at 94–108 Hz (p10–p90 of line medians).
  - The closing poem at 114 Hz (no emotion, expressive) read as declamatory.
  - The poem at 87 Hz (sad, pitch −3, speed 0.8) read as eerie.
  - The fix was the poem line from the original full take, with 0.25 s more silence at the comma.
- **Place names:** add `pronunciationDict` entries for every name with a non-default reading. 相门 came out as xiàng until marked xiang1. Whisper will still mishear some names (枕河 → 整合). That is a recognition limit, not a TTS error, so confirm by ear and by pitch.
- Pauses inside a line: `<#0.6#>` inserts 0.6 s. Use it sparingly, because a long pause in one line makes it stand apart from the rest.
- Cost: about 0.55 credits per short line.

## Score: Suno v6 (`chirp-v6`)

```json
{"taskType": "music_generation", "modelKey": "chirp-v6",
 "input": {"prompt": "contemplative ambient piano and strings with pipa and sanxian (Suzhou pingtan colour), a touch of dizi flute; slow build; electronic pulse enters at the modern section; warm, gentle, historical",
           "customMode": true, "forceInstrumental": true, "title": "Suzhou Jingwei",
           "tags": "cinematic ambient, neoclassical, chinese traditional, pipa, piano, strings, instrumental",
           "negativeTags": "vocals, singing, choir, humming, rap, EDM drop, dubstep, rock guitar, heavy metal, trap hi-hats",
           "durationSec": 262, "styleWeight": 0.7, "audioFormat": "wav"}}
```

Prompt and tags are the first cut's (168 s). The later 262 s rounds added the duration, style weight and negative tags, and asked for an explicit late build: a long crescendo to a climax, then a quiet coda.

- In Suzhou, each task returned two takes for about 13.7 credits, and a round used two tasks (four takes). Treat this as a production example; choose a batch size within the current quote and authorized budget.
- **Describe the instruments and the arc.** Name the palette that belongs to the city (here pipa and sanxian for pingtan, a little dizi), say where the modern section changes colour, and say where the build and the coda go.
- **List what to keep out** in `negativeTags` (vocals, choir, humming, genres that would break the mood).
- **Do not ask it to "keep the middle open for narration".** That produced a flat score the user called 普 (bland). The mix already makes room for the voice.
- **Map every take** with `music_profile.py`: a quarter-second loudness strip and a per-second spectral centroid (low centroid = dark, warm). Mark the dark passages, the full entries, the brightest stretch and the coda. Two takes from the same prompt often have their sections in different places, which is exactly what you choose between.
- **Start the score at frame 0.** Delaying it by 10 s to land a section was the first thing the user heard and rejected. If a take's sections don't fit with a 0 start, use the other take or generate more.

## Landing lines on the score

`plan_warp.py` places every line at natural length. Pauses can only be added, so lines can only move later. Pick 3–5 targets, each a line and the score second it should start at, and let `align_extras.py` spread the pushes over chosen gaps:

```bash
python scripts/align_extras.py --slots slots.json --lines lines.json --music-start 0 \
  --base '{"24": 24}' --targets '[[37, 244.0, [36]]]'
```

The Suzhou final alignment with take E1 from frame 0:

| Score section | Line on it |
|---|---|
| darkest, quietest passage (150–162 s) | the two 1860 fire lines |
| full ensemble entry (162.75 s) | "1982, Suzhou becomes one of the first national historic cities" |
| brightest stretch (212–216 s) | "the tallest tower in the east is Suzhou IFS, 450 m" |
| drop (220.75 s) | the low old-city heights, then "from above" |
| coda arrives (240 s) | no voice, picture alone |
| inside the coda (244 s) | the closing poem |

Only three pauses were added: 1 s between the fire lines, 2 s after "from above", 3.3 s before the poem. Keep the alignment in a small JSON (`vo/align.json`: extras, score file, start) and keep the previous rounds' files, so a rejected change can be undone.

## Mix

Before mixing, convert downloaded audio to 48 kHz integer PCM: `ffmpeg -i input.wav -ar 48000 -ac 2 -c:a pcm_s16le score.wav`. The bundled mixer accepts mono/stereo 16- or 32-bit integer PCM, not floating-point or 24-bit WAV input.

`build_vo.mjs` lays the lines on a film-length track with a little presence (+2 dB at 3.2 kHz), a high-pass at 75 Hz and gentle 2.5:1 levelling. `mix_duck.py` then:

- sets the score 4 dB under the voice overall;
- splits the score into low (<250 Hz), mid (250 Hz–5 kHz) and high (>5 kHz) with zero-phase filters that sum back exactly;
- under each line, dips **only the mid band**, by however far it sits above (voice level − 9 dB), capped at 4.5 dB, with a 0.45 s lead and 0.9 s release, smoothed so it never pumps;
- eases the whole score by a fifth of that dip;
- fades the last 3 s.

The Suzhou mix dipped 2.0 dB on average while speaking and not at all for 31% of spoken time. Per-line ASR error went from 4.2% dry to 6.5% in the mix. A deep full-band duck (the first cut) flattened every emotional peak, and the user asked for it back.
