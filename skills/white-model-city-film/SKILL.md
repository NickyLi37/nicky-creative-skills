---
name: white-model-city-film
description: Create data-driven white-model (白模) city documentaries with Three.js, geographic building data, historical map layers, narration and music through Sumi Studio MCP. Use for 3D city-history films, map-based urban-growth animations, or adapting the included Suzhou documentary to another city.
---

# White-model city film

The worked example is 《人家尽枕河》 (*Homes Pillowed on the River*), a 4-minute 4K film about Suzhou. It covers 92,681 buildings over 32 × 21 km, runs from paddy fields 6,000 years ago to 2025, and has 38 narration lines with bilingual subtitles. Its full code is in `example/suzhou/`. Read `example/suzhou/制作总结.md` first for the story of how it was made.

The Suzhou aesthetic, bilingual copy, continuous score and editorial choices are defaults for this style, not requirements for every city film. Follow the user's brief. The bundled example and encoders use 24 fps; changing that requires keeping capture, timing, audio and encoding consistent. The example excludes data, audio, fonts and brand assets; rebuild them using `example/suzhou/README.md` before rendering.

## How the pieces fit

```
prep/ (Python)            render/ (Three.js in headless Chrome)                 vo/ + music/ (Sumi MCP)
CMAB + OSM + old maps ──► world.js   builds the board, water, roads, buildings      TTS lines, score takes
→ local-metre layers      timeline.js  stateAt(frame): camera, layers, HUD, year      │
  (buildings.bin, *.json)  hud.js     DOM overlay: chapter cards, subtitles, callouts │
                          main.js    window.renderFrame(f) → one deterministic frame  │
                                 │                                                    ▼
                    scripts/capture.mjs → PNG frames ◄── vo.js (plan_warp.py) ◄── line lengths + pauses
                                 │                                                    │
                    scripts/encode.sh ◄──────────── mix.wav (build_vo.mjs + mix_duck.py)
```

Three contracts hold it together. Keep them and every other part can change:

1. **The frame number is the only clock.** `window.renderFrame(f)` must draw frame `f` from nothing but `f`. No `Date.now()`, no accumulated state, no animation loop. That makes rendering resumable, parallel, and cheap to patch: a change re-renders only the frames it touches.
2. **Visuals are authored in story frames; the narration sets film length.** Author camera keys, layer tracks and HUD cards once, on a fixed story timeline (Suzhou: 3,960 story frames). Each narration line owns a story slot. `scripts/plan_warp.py` gives every line its natural spoken length and writes `vo.js`, which holds the line placements plus a smooth film→story warp. Re-voicing a line or adding a pause never means re-animating anything.
3. **For the Suzhou style, keep the score continuous.** Pick the take whose sections fit, start it at frame 0, and move lines onto its sections by lengthening pauses (`scripts/align_extras.py`). Adapt this choice if the brief calls for music edits. If no take fits, propose another take within the authorized generation budget.

## Workflow

Work in stages and look at real output at the end of each one. If the user wants it finished autonomously, check each stage yourself and keep going. Either way, a 540p preview of the whole film comes before any 4K render.

1. **Brief and reference.** If there is a reference film, break it into frames: measure its length, fps, cut rhythm, HUD layout and material look. Settle the length budget, languages, aspect ratio, watermark and final resolution. Read `references/storyboard-and-facts.md`.
2. **Script and fact sheet.** Pick one through-line for the city (Suzhou: homes and water). Write chapter by chapter. Every line gets a source in a fact sheet, and anything inferred is labelled 示意 / illustrative on screen. Choose the historical scope from the user's brief; Suzhou's omissions were project-specific. Run on-screen copy past the user's style rules (the Suzhou brief avoided slogan-like symmetric pairs such as 「A没了，B还在」).
3. **Data.** Choose the extent and a local metre frame. Clip and pack the buildings, then fetch OSM water, roads and walls. Georeference old maps with a least-squares affine. Read `references/data.md`. Known trap: CMAB heights are compressed (max ≈100 m), so override supertall towers with OSM `height`.
4. **Render.** Start from `example/suzhou/render/`. Build the board and the layers, then the timeline: chapters, camera keys, tracks, subtitles, callouts and the year ticker. Render sample frames at chapter starts before writing the whole timeline. Read `references/render.md`.
5. **Narration.** Generate the whole script in one TTS take for a consistent voice, then split it per line. Re-voice single lines with the same voice and settings. Fix readings of place names with `pronunciationDict`. Read `references/voice-and-music.md`.
6. **Plan the timing.** Run `plan_warp.py` to get `vo.js`, then render the 540p preview.
7. **Score.** Generate takes within the user's budget, after checking currently available Sumi models and parameters (Suzhou used Suno v6, instrumental, full film length). Map each take with `music_profile.py`. Choose the take and the lines to land on its sections, then solve the pauses with `align_extras.py`.
8. **Mix.** `build_vo.mjs` lays the voice track, then `mix_duck.py` mixes it. Only the speech band of the score dips, and only as much as it competes with the voice.
9. **QA.** Read `references/qa-and-delivery.md` and run every check: per-line ASR on the dry voice vs the mix, frame-jump scan, year ticker vs narration, pitch of re-voiced lines, loudness and true peak, and contact sheets including the last second.
10. **Deliver.** Make a 540p preview, then the 4K master (`encode.sh`). Make a phone version under the chat-app size cap (`encode_phone.sh`) and the bilingual SRT (`make_srt.mjs`). Write a summary with numbers, sources and models so the user can post about it.

## Scripts (`scripts/`)

| Script | Does |
|---|---|
| `plan_warp.py` | story slots + line lengths + pauses → `vo.js` (placements, film length, smooth warp) |
| `align_extras.py` | pauses that land chosen lines on chosen score seconds |
| `capture.mjs` + `server.mjs` | deterministic PNG capture, resumable, N parallel workers, any scale (0.5 = 540p, 2 = 4K) |
| `build_vo.mjs` | voice lines → one film-length voice track |
| `mix_duck.py` | score under voice, speech-band-only, level-aware dip, score from any film second |
| `make_srt.mjs` | bilingual SRT from the timeline's subtitles |
| `encode.sh`, `encode_phone.sh` | 4K master; two-pass size-capped phone/preview version |
| `music_profile.py` | loudness strip + brightness per second of a score take |
| `qa_asr.py`, `qa_jumps.py`, `qa_years.mjs`, `qa_pitch.py`, `contact_sheet.py` | the QA pass |

Setup: `npm i` in `scripts/` (playwright-core; a local Google Chrome is used) and `pip install -r scripts/requirements.txt`. `ffmpeg`, `ffprobe`, `zsh` and `bc` must be on PATH. The included `qa_asr.py` requires Apple silicon/macOS; on other platforms use an available ASR workflow and report that substitution.

## Working with Sumi Studio MCP

Narration and music come from the user's own Sumi account, so every call spends their credits. State what a call will do and roughly what it costs before making it, unless the user has pre-approved that kind of generation. Use `get_model` to read parameters. Submit with `create_generation_task` and a stable `idempotencyKey`. Wait with `wait_task`, fetch the original with `get_asset_download_url`, and keep the files in the project. In Suzhou, narration was `speech-2.8-hd` (MiniMax TTS 2.8 HD) and the score was `chirp-v6` (Suno v6). The whole film cost about 147 credits over five rounds of revisions. These models and costs describe the November 2026 project; check live availability and quotes for a new production, and stop when the authorized budget is exhausted.

## Lessons that cost a revision round each

- Read narration at natural speed and let the film get longer. A 1.2× sped-up voice sounded rushed.
- Read a quoted poem or closing line in the same voice and settings as the rest. "Poetic" and "low" restylings both read as fake.
- Start the score at frame 0. Delaying it to line up a section is audible at once.
- A loud score under the voice should keep its swells. Dip only the speech band, a few dB.
- Show the place the narration names. If a line mentions a garden, the camera goes to that garden.
- Grow buildings one by one by their own year. Switching whole zones on in batches reads as popping.
- Check the last second. A receding end camera can expose the edge of the map board during the fade.

More in `references/lessons.md`.

## Credits

Every film made this way must credit its data on the end card and in the post: CMAB (CC BY 4.0), © OpenStreetMap contributors (ODbL), and each historical image with its own license. Name the AI models used for voice and music. If the film follows another creator's format, thank them by name.
