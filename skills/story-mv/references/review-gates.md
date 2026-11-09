# Review gates

Each gate is a fresh agent with a narrow brief: what to read, what not to open, what to measure, what counts as a
blocking problem, and a time limit. It writes its report to a file and changes nothing else. It reviews; the director
decides. Each repair round gets its own independent re-review, because fixes break things too.

## A. Story, cold read

Give it only the story. It retells the plot in its own words, then lists every point where it was confused, every
motive it had to guess, and every image it could not picture. HONG KONG's two cold reads shaped versions 3 and 4.

This skill has no gate B: frames are checked by counting limbs at full resolution as they are drawn
(`references/frames-and-prompts.md`) and again at gate C.

## C. Prompts and frames, before any paid submission

Give it the prompts, the first and last frames, the board and the character boards. It checks, shot by shot:

- the prompt's first and last states match the frames exactly (poses, doors, eyes, who sits where);
- the camera line matches the frames (a locked-off line on frames that differ by a push-in is a block);
- every limb, ear, tail and finger counted at full resolution on every frame;
- the beats fit the clip length once written 0.5 s early;
- no limit contradicts a beat (no new objects against new fireworks);
- composited frames have no seams, ghosts or afterimages when brightened.

It records the SHA-1 of every file it read and ends with "通过" (pass) or the list of blocking problems. Nothing is
submitted without a pass, and the files submitted are the files hashed.

## Clip QC, after every download

- Detect hard cuts inside the clip and look at every candidate.
- Two passes over all clips at full resolution, counting paws, ears, tails and fingers (HONG KONG: 48 shots in the first
  pass and 22 in the second, no extra paws or ears found, one hand wrong).
- Look for floating, sliding, faces changing age, costume changes, text appearing.

## D. The film, blind

Give it only the film, in the placeholder-text version (see `lyrics.md`). It times every card, cut and text block from
the frames, reads every card at full size, flags anything a viewer notices without pausing as a hard defect and
everything else as minor, and lists the questions a viewer would ask. HONG KONG ran gate D on versions 2 to 15.

- Gate D found what the director missed: a face ten years older than the next shot, wet hair that read as long hair,
  six last words cut off before they had lit, a doubled cat face from a step-print blend, a prop that came back after
  it was gone, cards too short to read.
- Tell the director's own numeric checks apart from the reviewer's judgement: identity of unchanged frames, frame
  counts, audio packets and loudness are measured by the director, not asked of the reviewer.
- A reviewer will call design choices faults (the cabinet swap). Keep them if they are the story; tell the user that
  viewers may read them the same way.
- When the user's notes are all done and the review finds only minor issues, list them and deliver. Do not start
  another round for minor issues unless the user asks; each 4K round cost about 40 minutes.
- When a brief asks for a closed-mouth smile, the reviewer counts "no smile" as a fault. Write "if she smiles, lips
  stay closed with no teeth".
