# Story and board

## Start from the song

1. Get the exact audio the user wants and keep it as one continuous track for the whole film. Measure its length,
   the silence at the head and tail, its tempo and first beat (`scripts/beat_grid.py estimate`), and its sections
   (intro, verses, choruses, bridge, outro) by ear-free means: loudness strip, onset density, repeats.
2. Decide the film's length from the song. HONG KONG ran to the song's fade (218 s) and left out the last 7 s of
   silence; the credit cards came after, on black.
3. Ask for what the brief leaves open: aspect ratio, final resolution, on-screen text, a credit cap for paid
   generation, the logo, and whether photos of real people may be used, and for what.

## Write the story before any image

A music video built from many 4 s clips needs a story that survives cutting. The HONG KONG story fitted in one line:
*the crossing where she left by taxi, the two cats guard every night until the neon signs are gone and she comes back.*
It was written as a fable with a real texture: how the cats cross the sea, live that long or change clothes is never
explained.

Rules that carried the HONG KONG film, worth reusing for any animal lead:

- **Shoot at the lead's height.** Street shots sit at cat height. Adults show only legs, hands and backs. Allow a
  few exceptions and list them (a window looking down on the crossing, a plane, the peak, one overhead shot, the
  final crane up).
- **Hold the human face back.** The woman's face first appears at 171 s, and she is the only face in the film. That
  shot then carries the reunion.
- **Tie the characters with things.** The cream cat's red jacket and the grey cat's floral shirt are her handiwork:
  the jacket has the same black four-hole buttons as her coat, the shirt is cut from the same cloth as her scarf.
  The payoff is a close-up where the flowers line up.
- **Let time pass through clothes and the city, not through ageing.** The cats never age (the user rejected aged
  cats as too sad). In the boom section they wear whatever the neighbourhood gives them; every night they return to
  the same green signal cabinet, at the same camera position, in a different outfit, so each cut back moves time on.
  Later the signs come down, the cabinet is replaced by a taller grey one with a sloping top, the cat slips off,
  and from then on both sit on the ground and see only legs.
- **Give the animals a cue the audience can follow.** The cats cannot see her return; they hear the rhythm of her
  suitcase's bent wheel. Plant the wheel in the first scene.
- **Revisit few places.** The second half re-shoots four set-ups from the first half (windowsill, tram, Nathan
  Road, rooftop), with the cats at fixed screen positions, so the change reads at once.
- **Get the place right.** Hong Kong drives on the left, the taxis are red and right-hand drive, and the crossing is
  two white lines and road studs, not zebra stripes. Signs and shop names are invented; only one readable sign is
  added in post.
- **Keep the period quiet.** One year number on screen (2000), no phones, no political symbols.

Write down the reason for every turn of the plot (why she left, who feeds the cats, why they sit on the ground,
how they recognise her). HONG KONG's list answered the blind reviewer's questions before the board was drawn. A few
questions remained open on purpose; list those for the user too.

Have a fresh agent read the story cold (`review-gates.md`, gate A) and retell it before you draw anything. HONG KONG
went through four story versions and two blind reads.

## Board

One JSON file drives everything after the story. HONG KONG's `example/hong-kong/shots.json` has 69 shots; the last ends at
215.32 s and holds under the title to 218 s.
Each shot:

| Field | Use |
| --- | --- |
| `id`, `section` | shot code (P prologue, B boom, C chorus, I interlude, V verse, R reunion, O outro) and the song section |
| `start`, `end`, `film_s` | position in the film, seconds; boundaries on the beat grid |
| `wear` | which costumes are on screen |
| `size`, `angle`, `camera`, `moves`, `next` | shot size, camera height and angle, locked or moving, the actions, how it cuts out |
| `ground`, `mid`, `accent`, `subject` | the colour script and where the subject sits (x, y, height share) for the board render |
| `task` | `i2v` (first frame) or `first_last` (first and last frames) |
| `hard` | marks the shots to pilot first |
| `zh` | the shot in one sentence, in the user's language |

Cut on the grid. Run `beat_grid.py snap BOARD.json --bpm … --first …` after every edit of the board: every
boundary moves to the nearest beat (or half beat) and becomes a whole frame, and shots under 12 frames are flagged.
Generated clips are 4 s or longer (Seedance 2.5 has no 3 s option), so an editorial shot of 1.2 s still costs a 4 s
generation; budget by generation seconds, not film seconds.

Two artefacts go to the user at this gate: the board as a colour contact sheet and the same sheet in grey, plus a
per-scene colour table (`example/hong-kong/colors.md`). The user stops here only for the story, the look, the
spend and the rough cut.

## Characters

- People: a reference board with a headless front body, a back view that keeps the head, and a large face
  close-up; expressions on a separate sheet. A small face inside a full-body view is the face a video model copies
  badly.
- Cats: one board with a large face plus front and back full bodies; expressions on a separate sheet.
- Costumes: one board per look. HONG KONG had 13 extra looks for the boom section, glasses and headwear included.
  In GPT Image never ask for a chin strap or elastic on a cat's hat: it draws a thin loop round the whole face
  (five boards were redone). Say the cap rests on the head. Headphones get one wire from one ear pad.
- Keep the heroine young: the user rejected a crying panel with wrinkles and a dark spot on a tooth. Her smiles stay
  closed-lip.
