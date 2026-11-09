---
name: story-mv
description: Make an original-story music video from many short AI clips. Story and storyboard on the song's beat grid, first and last frames with GPT Image, Seedance 2.5 clips and 4K upscale through Sumi Studio MCP, a film-look finish with step print, lyric typography timed without the agent reading the lyrics, credit cards, cover and release package. Use for 剧情 MV、猫猫 MV、给一首歌拍 AI 短片、港片/胶片质感、卡点剪辑、歌词排版, or adapting the included HONG KONG cat MV to another song.
---

# Story MV

The worked example is **HONG KONG**, a 4-minute fan-made music video for The Weeknd's *HONG KONG (feat. 王菲季候風)*:
two teahouse cats wait every night at a Kowloon crossing for the woman who left by taxi. 4K, 24 fps, 248.17 s,
69 shots, 88 Seedance 2.5 clips, 62,805 Sumi credits, 15 film versions. Read `example/hong-kong/制作总结.md` first for
how it was made, then `references/lessons.md`.

The Hong Kong look, the cats and the Chinese copy are this example's choices. Follow the user's brief for the song,
the lead and the look.

## Five contracts

Keep these and everything else can change:

1. **One continuous song; cuts on its beat grid, in whole frames.** Measure tempo and first beat, snap every shot
   boundary (`scripts/beat_grid.py`). If the accents sit off the grid, shift the whole audio track once and leave
   the cuts where they are. Calibrate the onset detector first (`references/look-and-finish.md`, audio sync).
2. **Frames and clips stay clean; the look is added in post.** Grain, bloom, halation, step print, handheld drift and
   the logo come from `scripts/film_look.py`, seeded by frame number, so any range can be re-rendered and joined.
3. **The agent never reads or writes the lyrics.** The user supplies the file, tools read it at run time and print
   numbers, reviews use placeholder glyphs, the user proofreads. Details in `references/lyrics.md`.
4. **Every paid call is quoted and approved, every task logged.** Inside a cap the user has given, carry on and log.
   Do not treat the account balance as approval to spend.
5. **Nothing is overwritten.** Every take and version goes to a new file; pick at the end.

## Workflow

Stop for the user four times: story, look, spend, rough cut. If the user hands over the run ("做到底"), check each
gate yourself and keep going inside the cap.

1. **Brief.** Song file, length, aspect ratio, final resolution, on-screen text, logo, credit cap, and which photos of
   real people may be used for what. Measure the song (`beat_grid.py estimate`, then `phase`).
2. **Story.** One line, then sections against the song's real timings. A cold read by a fresh agent (gate A) before
   any image. `references/story-and-board.md` has the rules HONG KONG used: the camera at the lead's height,
   the human face held back until the payoff, objects that tie characters together, time carried by clothes and the
   city, a cue the animals can hear.
3. **Board.** `shots.json` with one entry per shot; `beat_grid.py snap` after every edit. Colour and grey contact
   sheets plus a per-scene colour table for the user.
4. **Look and characters.** Measure the reference, write the look rules (`references/look-and-finish.md`), make one
   style frame per section and get the user's sign-off. Character boards and separate expression sheets; costume
   boards per look.
5. **First and last frames.** GPT Image, clean, one fixed look paragraph in every prompt. Count limbs at full
   resolution in every frame (`references/frames-and-prompts.md`).
6. **Video prompts.** Six blocks: Style, Camera, Layout, Cast, Beats, Limits (plus Sound when the clip has generated
   audio). Timed beats are written 0.5 s early, at real speed; do not write "slow motion". Gate C, a fresh reviewer
   agent, must write "通过" before anything is submitted. Quote, report shots, seconds and credits, wait for approval.
7. **Generate.** Hardest shots first. Download every take, check cuts and limbs, log the task.
8. **Repair.** Try fixes in this order: move the in-point, retime part of the shot, cover the fault, repaint a
   clean plate, retime one region of the frame. Re-shoot with new frames or a new prompt only after that
   (`references/repairs.md`). Re-rolling an unchanged prompt does not help.
9. **Rough cut and upscale.** Assemble at 1080p on the grid, then upscale in chunks that end on shot boundaries
   (`scripts/upscale_chunks.py`, `references/generation-and-upscale.md`). Mix the 1080p back where the enhancer draws
   lines into skin or fur.
10. **Finish.** `film_look.py` per shot spec, lyric layer, credit cards sized by `scripts/card_timing.py`, picture
    fades, one encode. Patch later fixes by re-rendering only the affected frame range.
11. **Blind review (gate D)** on the placeholder-text version, every round, by a fresh agent. Ship when only minor
    issues remain after the user's own notes (`references/review-gates.md`).
12. **Deliver.** 4K master, a 1080p copy for social platforms, a cover (`scripts/title_cover.py`), release copy per
    platform, a ZIP for sending (`scripts/share_pack.py`), and a summary with numbers, credits and what was not
    checked (`references/credits-and-publish.md`).

## Scripts (`scripts/`)

| Script | Does |
| --- | --- |
| `beat_grid.py` | tempo and first-beat estimate; where accents sit against the grid (calibrated); snap a board's cuts to the grid in frames |
| `film_look.py` | the finish: grade, bloom, red halation, grain, soft filter, gate flicker, handheld drift, 12 fps step print (blend or hold), logo; per-shot spec; chunk-safe |
| `flow_ramp.py` | a shot retimed as a step print with its own speed curve, optical-flow in-betweens for gradual changes |
| `plate_repair.py` | median clean plate of a locked-off shot; lay a repainted plate back into every frame and keep the shot's own rain |
| `upscale_chunks.py` | group the cut into upscale chunks at shot boundaries, with expected and held credits, and a frame map |
| `card_timing.py` | words per card against full-light time, at 4 (and 5) words a second |
| `subject_mask.swift` | macOS Vision subject cut-out for covers (float masks) |
| `title_cover.py` | giant squeezed title behind the cut-out subject; reports whether everything sits inside the centred 4:3 |
| `share_pack.py` | ZIP a delivery folder: NFC UTF-8 names, media stored, text deflated, ZIP64, CRC checked |
| `lyric_cut_test.py` | where a sung word really starts, by forcing Whisper from moving start points (Apple silicon, mlx-whisper) |

The lyric layer itself (placement and the neon rendering) is not included; `references/lyrics.md` describes how to
build one.

Setup: Python 3.10+, `pip install -r scripts/requirements.txt` (numpy, opencv-python, Pillow), ffmpeg and ffprobe on
PATH. `card_timing.py`, `share_pack.py`, `upscale_chunks.py` and `beat_grid.py snap` need only the standard library.
`subject_mask.swift` builds with `swiftc` on macOS 14+. `lyric_cut_test.py` needs Apple silicon and
`pip install mlx-whisper`. Tests: `python3 tests/test_scripts.py` (synthetic media only).

## Working with Sumi Studio MCP

Generation and upscale run on the user's own Sumi account. `get_model` for live parameters, `quote_task` before every
batch, `create_generation_task` with a stable `idempotencyKey`, `wait_task`, then `get_asset_download_url` into the
project. HONG KONG used `seedance-2.5` at 1080p with `generateAudio: false` and `outputFormat: "mov"` (tagged BT.709),
first frames via `imageAssetIds`, and `mediakit-video-enhance` at tier `4k`, tool version `professional`, for the
upscale. Its prices date from November 2026: check live availability and prices, and stop when the authorized
budget is spent.

## Lessons that cost a round each

- Lyric word starts from forced alignment were up to 3.1 s early on first words. Time them with the cut test.
- A line's last word must not land alone in the next shot. Keep the line as one block across the cut.
- Blending step-print pairs on a walking subject gives double eyes. Hold frames for anything that moves.
- A speed change by swapping 2, 1, 2, 1 frames stutters. Ease it with optical-flow in-betweens.
- A first frame that shows the end of an action freezes it. Draw the start state.
- After replacing a shot, check the props against its neighbours (a sign that came back after it was gone).
- Credit cards sized by eye were unreadable twice. Count words first.
- An onset detector labelled by frame start reads hits 36 ms early. Calibrate on clicks before shifting audio.

More in `references/lessons.md`.

## Rights and people

- The song, its lyrics and any sampled recording belong to their owners. Make the film as a fan work and say so on a
  card. A public or gallery copy leaves out the song and the lyrics unless the rights holder allows them; the HONG
  KONG gallery copy is silent and has no lyrics.
- Use photos of a real person only with the user's assurance that they may be used, only to design that character,
  and never in a public release of the skill or the project. Do not write real people's or directors' names in
  prompts; describe what the picture shows.
- If the platform silently removes an uploaded image, do not upload it again or route around it; reuse what the
  platform already holds and tell the user.
- Credit the animals' home, the tools and any film or creator whose look or format you follow.
