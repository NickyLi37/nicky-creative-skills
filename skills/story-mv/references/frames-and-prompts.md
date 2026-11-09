# First and last frames, and video prompts

## Frames

- Draw every shot's opening frame, and its last frame when the action has to land somewhere (`task: first_last`).
  HONG KONG: 69 shots, 82 frames in the first pass, GPT Image 2.6 `sunburst` at `quality: max`, `complexity: high`.
- Frames are clean: no grain, no halation, no text. The film look is added in post. A video model asked to keep
  grain renders it as flicker.
- Put the look into every image prompt as one fixed paragraph (`example/hong-kong/look.md` has HONG KONG's) and
  describe each character with fixed sentences. Never write a real person's or a director's name; describe what
  the picture shows.
- Check every frame at full resolution before it goes to video: crop each animal and each hand and count two front
  legs, two hind legs, two ears, one tail, five fingers. A raised paw is the pose that grows a third paw. A contact
  sheet hides these.
- A first frame and a last frame that differ in tone or framing turn into drift inside the clip. If the camera moves
  between them (V17 pushes in about 6 %), the prompt must say so.

## Prompt format

Six blocks, in English, one file per shot, plus a Sound block only when the model generates audio. Real examples are in `example/hong-kong/prompts/`.

```
[Style]  one line of look, then "Style, colour and character design match the input image exactly."
[Camera] "<N> s, <shot size>, <camera position>." and either the move with its reason, or the locked-off line:
         "Locked-off camera, framed and lit exactly as in the input image. The camera remains completely still for
          the entire shot: no push-in, no pull-back, no pan, no tilt, no zoom, no shake, no drift. One continuous
          shot with no cuts."
[Layout] where everything sits, by picture left and right; for first/last-frame shots, the first state and the
         last state, matching the frames exactly
[Cast]   each character's fixed look, the same words in every prompt
[Beats]  0.0-0.2 s: the picture is identical to the input image.
         timed beats, each written 0.5 s earlier than wanted, at most two main actions
         Last 0.3 s: everything is completely still and matches the last frame.   (first/last-frame shots)
[Limits] Only the people and objects in the input image appear. Faces and bodies stay the same throughout.
         Real speed, no floaty or slow movement. The picture stays clean, with no text, subtitles or watermark.
         Each cat keeps exactly four legs, two ears and one tail, moves like an ordinary real cat and keeps the
         same costume. Their mouths stay closed. No human face appears at any moment.
```

- Write real speed. Never write "slow motion": it makes the action stiff and draggy. Step print, holds and speed
  ramps are done in the edit.
- For the heroine: "Her skin stays smooth and young, her lips stay closed with no teeth showing, and she does not
  speak. Her hand keeps five fingers."
- Name an off-screen or empty part of the frame when it must stay empty ("At the start of this shot the bottom left
  of the frame is bare").
- If something new must appear (fireworks in B15), the limit "only the objects in the input image appear" conflicts
  with it; change the limit, or the model keeps the sky empty.

## What Seedance 2.5 did with timing (HONG KONG, first/last frames, 4 s)

- A door that opens before a foot steps out: the door was open after about 1 s, the foot out at about 1.7 s, on the
  ground at about 2.9 s. A shot shorter than about 2.6 s cannot hold the whole action; move the cut first (V16 was
  started 0.9 s earlier and V15 shortened).
- A first frame that already shows the end of an action freezes it: the first frames of C8 and V16 had the door open
  and a leg outside, so nothing happened. Redraw the first frame with the door shut and no leg.
- Clips often stand nearly still for their first frames (V3: 24 frames). Plan the in-point, or skip the slow start
  with a step plan (`scripts/flow_ramp.py`).
- Eyes closed to open (V17): "his eyes stay closed until …", then "he opens his eyes over about a second". Of two
  takes, one opened half a second early; pick by frame numbers, not by the first look.

## Gate C before every paid submission

A fresh agent reads the prompts, the frames and the board and writes "通过" (pass) or the blocking problems, with the
SHA-1 of every file it read so you can prove the submitted files are the reviewed ones. See `review-gates.md`.
HONG KONG's gate C caught, among others: a cat told to stand in a last frame where it sits, a door's end state that
contradicted the last frame (the model then swings the door at the camera and back), a locked-off camera line on a
shot whose frames differ by a 6 % push-in, an afterimage on a cat's far ear, and "no new objects" against new
fireworks.
