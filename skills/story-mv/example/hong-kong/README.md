# Example: HONG KONG (cat music video)

The planning files of the finished film (v15: 248.17 s, 5,956 frames, 4K, 24 fps), as they stood at delivery on
7 November 2026; the production summary adds a note from 9 November. Not included: the film, clips, frames, character and costume boards, the song, the lyrics, fonts and
the logo (rights and size), and the 154 project scripts; `scripts/` in the skill holds general versions of the
reusable ones.

| Path | What it is |
| --- | --- |
| `制作总结.md` | production summary: specs, tools, cost, process, every repair and what was left as is (Chinese) |
| `story.md` | story v4, the version the board was drawn from: four rules, characters, the crossing's plan, sections with timings, reasons for every turn (Chinese) |
| `look.md` | the look: measured reference, seven picture rules, motion, section colours, the look paragraph used in every image prompt (Chinese) |
| `colors.md` | colour script per scene with hex values (Chinese) |
| `shots.json` | the board: 69 shots with timing on the 69 BPM grid, costume, size, angle, camera, moves, colours, subject position, task and a one-line description |
| `prompts/` | eight Seedance 2.5 prompts in the six-block format, and the template. P1, B7, B14 and R2 are first-frame shots, R8 uses first and last frames, and C8, V17 and O1 are the round-13 re-shoots from first and last frames |
| `finish_spec.json` | the per-shot settings of the final finish, in the format `scripts/film_look.py --spec` reads |
| `credit_cards.txt` | the four closing cards with their full-light times; `scripts/card_timing.py` flags card 3, as the final review did |

Some files show the plan at a given moment. `story.md` says there are no lyrics on screen: the user asked for them
later, and `references/lyrics.md` describes how they were done. `look.md` plans blended step print for crowds and
runners; the eighth review showed that walking subjects need held frames instead.
`shots.json` is the board the frames were drawn from: round 13 later re-shot C8, V16 and V17 from first and last frames,
and their `task` still reads `i2v`. Its `rate` field is the planning estimate of credits per generated second at 720p;
the film was generated at 1080p.

Rebuilding the film needs your own song file and lyric file, your own character boards, frames and generations, and
your own logo. The prompts refer to frames that are not included; read them as examples of the format.
