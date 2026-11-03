# QA and delivery

Run the whole pass before final delivery. During revisions, recheck the changed part and its timing, visual or audio dependencies; repeat the full pass when changes affect the film globally. Report checks that could not be run.

## Checks

| Check | Command | Pass |
|---|---|---|
| Narration survives the mix | `ffmpeg -i vo_track.wav -ac 1 -ar 16000 dry16.wav` (same for the mix), then `qa_asr.py --script script.txt --vo-js vo.js dry16.wav mix16.wav` | mix CER within a few points of dry; lines marked `<<` were heard and accepted, or the bed was lowered there |
| No unplanned jumps | `qa_jumps.py out/preview` | every flagged run is a designed cut (chapter start) or a known fast camera move |
| Years agree | `node qa_years.mjs --timeline render/src/timeline.js` | the ticker shows the year a line names while the line is spoken; "N years later" moves the ticker inside the line |
| Re-voiced lines match | `qa_pitch.py vo/lines/*.wav` | median pitch inside the narration's p10–p90 range |
| Score enters at once | level of the first 2 s of the mix | the score is audible within the first second |
| Loudness | `ffmpeg -i film.mp4 -af ebur128=peak=true -f null -` | about −15 LUFS integrated, true peak below 0 dBTP after AAC |
| Picture | `contact_sheet.py` at every chapter start, cut, climax, and the last 3 s | no board edges, no fallback fonts, no stray layers, subtitles inside the safe area |

Also confirm the duration (`ffprobe`) matches `FILM_END / 24`, and that the SRT has one cue per line.

## Previews

Render a full 540p preview (`capture.mjs --scale 0.5`, ~11 min) and send it before any 4K render. Encode it under the chat-app size cap:

```bash
scripts/encode_phone.sh out/preview vo/mix.wav out/film_preview_540p.mp4 540 28 96
```

## Masters

```bash
node scripts/capture.mjs --root . --page render/index.html --out out/frames_4k --from 0 --to <FILM_END> --scale 2 --workers 4
scripts/encode.sh out/frames_4k vo/mix.wav out/film_4K.mp4            # x264 crf 14, AAC 320k
scripts/encode_phone.sh out/frames_4k vo/mix.wav out/film_1080p.mp4   # two-pass, under 29 MiB
node scripts/make_srt.mjs --timeline render/src/timeline.js --out out/film.srt
```

- Use limiter 0.9 for the master and 0.87 for low-bitrate AAC. AAC overshoots: a 96k encode hit +0.3 dBTP from a 0.93 limit.
- Expect the 4K master at about 3.4 GB for 4 minutes at crf 14, and the PNG frames at about 60 GB. Check free disk before starting.
- A 4K render takes hours. Start it in the background as soon as the preview is approved, and keep working on docs while it runs.

## Deliverables

- the 4K master, the phone version, the bilingual SRT
- a production summary for the user to post from:
  - length, frame count, resolution
  - year span, map extent, building count
  - data sources with licenses
  - the AI models used for voice and music, and the total credits spent
  - render time
  - what changed in each feedback round
- the plan doc kept current: chapters, fact sheet with sources, and a status log per round
