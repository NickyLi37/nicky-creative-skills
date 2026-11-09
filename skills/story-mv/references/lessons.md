# Lessons from HONG KONG

What the user asked for, what was done, and the rule it left behind. The film went from story to a 4K master in
about two days, through 15 film versions; v15 is final.

## The user's notes

| Note | Fix | Rule |
| --- | --- | --- |
| Aged cats are too sad | the cats never age; time passes through clothes and the city | An animal lead stays the same age; carry time some other way. |
| Make it Hong Kong, in the Wong Kar-wai vein | measured look from the reference, two colours, foreground cover, wet ground, step print | Describe a director's look by measurable features, never by name, in every prompt. |
| More looks for the cats, try glasses and headwear | 13 outfits (seven for one cat, six for the other) through the boom years, with the cabinet camera returning between them | One fixed set-up that returns makes a costume change read as time passing. |
| Lyrics on screen, made to look good | neon English per word, vertical Chinese signboard columns, timed from the user's file | The agent never reads or writes the lyrics; tools read the file, reviews use placeholders. |
| Lyrics are off the singing | DTW starts were early; English re-timed with the cut test, Chinese from chorus repeats | Never trust aligned word starts; the user hears what numbers miss. |
| Don't throw a line's last word into the next shot | whole line as one block across the cut, last word lit in place | Keep a line in one place, even across a cut. |
| More step print through the middle | four more shots on 12 fps | The user likes the step-print texture; offer it. |
| Make it feel less AI | grain × 1.2, 10 % soft filter, softer corners, 0.4 % gate flicker, handheld drift | Take the enhancer's crispness off in post, not in the prompt. |
| A shot starts too slowly | skip the still opening with a step plan and an eased ramp | Seedance clips often stand still for the first second. |
| Her hand on the cat looks wrong | hands redrawn on both frames, prompt rewritten, three takes, the one whose hand stays down used | Fix the frames and the prompt before buying takes. |
| Credits for the singer, writers, sample and source | four checked cards after the song, one on the second shot | Size cards by words before rendering. |
| Fireworks behind the 2000 glasses are frozen | re-shot from the first frame with a burst; outline added to the text over it | New bright motion behind text: re-check readability. |
| The door is already open and the foot already out | first frames redrawn with the door shut, re-shot from first and last frames | A first frame that shows the end of an action freezes it. |
| The shutter stops with fingers on it, awkward | picture fades to black while the shutter is still falling | Fade the picture, not the text, and land the black on the stop. |
| Eyes closed, then opening at the end | re-shot from first and last frames, push-in written into the prompt | Say every camera move the frames imply. |
| The key in the palm looks like a dead hand | a dark window lights up and the cats jump onto the sill | Replace an image that fails rather than polish it. |
| The minor issues can stay; it has taken long enough | delivered v15 | After the user's notes are done and only minor issues remain, deliver. |
| Cover: title bigger, one line, no artist names | giant squeezed red title behind the cats, a 16:9 kept inside 4:3 | A cover is the title, alone and huge. |

## Process

- Story, look, spend and rough cut are the user's stops; inside an approved cap the director carries on and logs.
- The hardest shots go first: plane over the roof, the 63.5 s crowd, cats on Nathan Road, the slip off the new
  cabinet, the sea of umbrellas, cats between legs, head into palm, the sign lighting up.
- A sign that lights block by block was made from two approved stills, fully off and fully on, revealed block by
  block in post.
- Every repair round: new files, independent review, numeric check that unchanged frames are unchanged.
- Re-render only what changed: ProRes pieces per range, one final encode.
- Keep a written summary as you go (`example/hong-kong/制作总结.md`); delivery notes, credits and the case study come
  from it.
- Calibrate measuring tools on synthetic input with a known answer before acting on their numbers. The beat-phase
  detector was 36 ms early and nobody noticed until its test (see `look-and-finish.md`).
- The director cannot hear the film or see true motion. Say what was measured and what was not.
