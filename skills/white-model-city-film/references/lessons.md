# Lessons from five revision rounds

What the user asked for in each round of the Suzhou film, and the general rule it taught.

| Round | User feedback | Fix | Rule |
|---|---|---|---|
| 1 | The cut from Tiger Hill to the Pingjiang map was abrupt; show the real stele first; add narration | the stele photo appears, dissolves into traced lines, then the model, then satellite; restrained male narration following the subtitles | Introduce a historical source as itself before abstracting it. |
| 2 | Narration felt sped up; buildings grew in batches; the music ducked so hard it lost its peaks | natural-speed narration and a longer film via the story-time warp; per-building reveal by year; speech-band-only dip | Never time-compress a voice. Never toggle geometry in zones. Duck by band, not by volume. |
| 2 (QA) | — | "four years later" was spoken while the ticker still said 1990; the ticker now ramps inside the line | After re-timing narration, re-check every number the narration says against the HUD. |
| 3 | Camera missed 拙政园 when gardens were named; add vertical calligraphy 「苏州」 to the end card; the poem should be slower and more poetic; the score was plain | camera keys onto the garden; Ma Shan Zheng calligraphy with a per-character mask wipe; four new score takes with an explicit late build | Show what the narration names. Score prompts should describe an arc, not "leave room". |
| 4 | Drop the wall demolition and canal filling (sensitive); credit protection and restoration; somber score at the fire, rising after; lower the poem | chapter rewritten as protection; hard cut from the fire to today; the take with a dark middle passage, aligned by pauses | Keep sensitive modern history out. Choose takes by their section map. |
| 5 | Score must start at the first frame; the low poem was creepy, read it like the rest | the other take from the same batch, started at 0 with three pauses added; the poem line from the original full take; end camera pulled in after the board edge showed | One continuous score from frame 0. A line inside the narration is read like the narration. Check the last second. |

## Process lessons

- **Show a full low-res preview before every 4K render.** 11 minutes of 540p catches what a still cannot: pacing, music, sync.
- **Stop a running render when the timeline changes.** Workers hold the old module, and existing frames are skipped.
- **Keep every take and every alignment.** Name them by round (`align_r3.json`, `poem_q2_used_r4.wav`) so a rejected idea can be compared with or restored.
- **Measure audio instead of guessing.** Loudness strips, spectral centroid, pitch medians and per-line ASR made each decision checkable and quick.
- **Write the plan doc as you go.** One doc with chapters, a fact sheet with links, decisions and a status log per round makes the final summary and the credits a copy job.
- **When the user hands over autonomy, keep checking each stage yourself.** Each stage still ends in a real artefact (sample frames, preview, mix) that you inspect before moving on.
