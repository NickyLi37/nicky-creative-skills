# Look and finish

## Measure the look before you describe it

HONG KONG took its colour baseline from the fan edit the user supplied, 12 frames measured:

| Measure | Value |
| --- | --- |
| mean luma | 0.26: most of the frame below mid-grey |
| mean saturation | 0.48 |
| shadows / mid-tones / highlights, RGB | 26, 28, 20 / 100, 107, 97 / 199, 207, 184: green shadows, yellow-green highlights |
| hue share | red-orange 28 %, teal-green 42 %, little else |

The rules that came out of it, for a 1990s Hong Kong night film:

1. Dark. Large areas of black with a few pools of coloured light.
2. Two colours: fluorescent teal-green and neon blood-red. Yellow only for sodium lamps, fireworks, the gold shop
   and her scarf.
3. Something dark and out of focus in the foreground covers part of the frame: railings, wet glass, plastic strip
   curtains, umbrella rims.
4. The subject sits past the 38 % or 62 % line, with a large dark area on the other side.
5. Wide lens, close. Faces and cats never centred.
6. Shallow focus: the background melts into colour shapes and discs, so no sign can be read.
7. Wet. The ground is always wet and throws the colour back up.

Write a colour script per scene (`example/hong-kong/colors.md`): base, mid, accent, light.

## The finishing pass (`scripts/film_look.py`)

Order per frame: pick the source frame (step print) → handheld drift → soft filter → gate flicker → grade with bloom
and halation → grain → logo. Text goes on before the grade so bloom and grain sit over it; the logo goes on after,
so it stays clean.

The HONG KONG grade, at 1920-wide scale (the script scales every size with the frame width):

- a gentle S-curve mixed at 28 %
- shadows (luma below 0.42) pushed by RGB × (0.96, 1.02, 0.88), highlights (above 0.55) by (0.99, 1.005, 0.94)
- saturation +6 %
- bloom from everything brighter than 0.62, sigma 26 px, screened at 20 %; a tighter halo (sigma 11 px) added to red
  (+0.14 R, +0.05 from G) and a little to green: the red halation round neon and tail-lights
- 20 % of a 0.8 px blur, then a vignette of up to 16 % in the corners
- grain from 12 luma plates and 5 colour plates, cropped at random per frame, strongest in the mid-tones
  (0.008 + 0.011 × mid-tone weight)

Settings that took the AI sheen off in the eighth version (`example/hong-kong/finish_spec.json`): grain × 1.2 on
every shot, a 10 % soft filter everywhere, corners softer (`edge_soft` 0.22), exposure breathing of 0.4 % per frame
(`flicker` 0.004), and a handheld drift of 3 px at 4K. A stronger soft filter (0.3) on her close-ups, the way Hong
Kong camera crews softened their leading women.

Everything random is seeded by the frame number, so chunks rendered in parallel join into exactly the same film as one
run. On an M1 Max, 9 processes rendered HONG KONG's 5,232 song frames at 4K in 34.5 minutes, about 3.6 s per frame
per process (measured on a run without the lyric layer).
Intermediates are ProRes (every frame a keyframe), so a patched range replaces exact frames and the film is encoded
once at the end.

## Step print (抽帧)

The user liked it, and asked for more of it through the middle of the film. 12 fps on a 24 fps film, each image held
for two frames.

- **Blend** the pair (average two neighbouring frames) only when the subject barely moves: drifting crowds, slow
  pans. On a cat walking towards the lens a blend reads as double eyes; the eighth-version review called it a hard
  defect.
- **Hold** one frame for two, no blend, for anything that moves fast or walks.
- A shot with an odd frame count: the last frame pairs with itself, never with the next shot.
- **Speed changes go gradually.** Swapping whole frames 2, 1, 2, 1 to slow down reads as long-short stutter. Ease over
  three or four steps (1.8, 1.6, 1.4, 1.2 source frames a step) and draw the in-between positions with optical flow
  (`scripts/flow_ramp.py`). Check every in-between at full size: eyes, ear edges, whiskers.
- Do not fill a clip's own duplicate frames with optical flow during fast action. Seedance repeated one frame in
  four in B3 while a cat jumped; the flow in-betweens gave half-transparent single frames and a doubled neon sign.
  The original stayed.

## Picture fades, holds and black

- Fade the picture on its own track, separately from the text, so a title can outlast the shot under it.
- A roller shutter that stops dead with fingers on it looked awkward; the picture faded to black over 0.4 s while it
  was still falling, so the frame where it stops is already black. The black lasted about 1.9 s.

## Colour and format

- Convert every clip to BT.709 before it touches any compositing tool, and tag the outputs (`-color_primaries bt709
  -color_trc bt709 -colorspace bt709`).
- Master: 3840×2160, 24 fps, H.264 High at CRF 15, AAC 320 kbps. HONG KONG: 248.17 s, 102.3 Mbps, 3.17 GB.
- A 1080p delivery for social platforms: 13.7 Mbps, 425.6 MB, SSIM 0.97 against the 4K master scaled down, same
  audio packets.

## Audio sync

Keep one continuous audio track from the user's file. Cut points sit on the beat grid in whole frames.

Measure where the accents fall against the grid with a calibrated onset detector (`scripts/beat_grid.py phase`),
then shift the whole track if needed; never move the cuts one by one.

Calibrate first. A spectral-flux envelope labelled by the start of each analysis frame reads every hit about 36 ms
early (1024-sample window at 22.05 kHz). HONG KONG measured its accents at 49 ms ahead of the grid that way and
delayed the audio by 48 ms. Recomputed with calibrated labels, the accents sit about 13 ms ahead, so the finished
film's audio runs about 35 ms behind the cuts: under one frame (41.7 ms), and audio that comes slightly late is the
direction viewers forgive most. `beat_grid.py` now carries the calibration, and its test checks it on clicks.
