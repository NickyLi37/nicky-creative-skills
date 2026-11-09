# Repairs

Work down this ladder and stop at the first step that fixes the problem. Re-rolling the same prompt does not help.
Every fix goes into a new file; the old clip and the old film stay.

1. **Move the in-point or out-point.** Most problems sit at a clip's ends. HONG KONG: B5 had fake lettering on a sign
   (in-point later), B7's neon died at the out-point (in-point later, so the lights go out mid-shot), B15's glasses
   blew out at the end and B16 got sudden fireworks (in-points earlier), V3's cats sank out of the bottom of the frame
   (in-point earlier, so both faces end whole).
2. **Retime part of the shot.** R7's cat floated through the air: the run was played 2.1 times faster and the
   braking back at real speed. In the locked-off V5 a pink cloud slid across half the sky in three seconds and read
   as pasted on: the sky region played at a quarter speed while the cats kept real speed. C6's grey cat turned its
   head and its ears became hollow outlines: the shot was slowed and ended before the turn.
3. **Cover a small area.** A paw that reached under the other cat's chin read as a fifth paw for 14 frames (V6): the
   ground from before the paw came in was laid over it. B4's grey cat seemed to have three front paws: the paw further
   back was darkened into shadow. A sign that lit with a hard square edge got a soft mask (R11).
4. **Repaint a still subject on a clean plate.** When the subject does not move, the median of the shot's frames is a
   clean still with the rain gone (`scripts/plate_repair.py plate`). Repaint the problem on a crop of the plate with
   GPT Image and a mask, then lay it back into every frame and add back only the frame's own long thin rain streaks
   (`plate_repair.py apply`). HONG KONG R7: her wet hair hung to her forearms and read as long hair, and close up it
   looked like a horror film; the head was repainted with short wet hair against the scalp. Her hands looked older
   than her face, with a scar-like streak: repainted in the same pose, rain kept with `--min-channel`, because rain
   lights all three channels while the old skin edge lights only red.
5. **Edit time locally.** O2: fingers dropped too fast and the button jumped, warped and went half-transparent. Only
   the hand area was retimed: the fingers rise to frame 4810, return along the same path, and an optical-flow
   transition reaches the pose of frame 4831; frames 4811 to 4830 are not used, everything else keeps its frames.
   Later in O2, as a button fell back into place, flow smeared its holes; for those six frames the button moved as a rigid
   body with a cross-fade, fingers kept in front.
6. **Fix brightness without touching texture.** I3: the window went almost black and the cat and the room went dark
   with it. Gain was set per frame from the cat's brightness, and the street outside got back exactly what it had
   lost from a bright plate: the drop shrank from 80 % to under 10 %. V4: a warm patch came and went on a man's hip;
   a low-frequency ratio from the frames before it pulled it back to the grey-teal, texture untouched. V2: tube lights
   slid down the ceiling in a locked shot: the roof was replaced by a plate from the frames where the tubes were
   still, the cats keyed by fur colour, the plate moved frame by frame with the tram's measured shake (the first
   version did not move, and the review saw two layers).
7. **Re-shoot with new frames or a new prompt.** Only after the steps above. HONG KONG round 13 re-shot five shots
   from first and last frames: the taxi door opening before the shoe steps out (C8, V16), fireworks bursting behind
   the 2000 glasses (B15), eyes closed then opening (V17), and a lit window with the two cats jumping onto the sill in
   place of a key handed over in a palm that looked like a dead hand (O1). Two takes each, picked by frame numbers.
   A face that looked ten years older than in the next shots (R3) was re-shot from the R8 first frame, flipped and
   cropped, and only the frames after she lifts her head were used.

## Check the neighbours

- After replacing a shot, compare props and set state with the shots before and after it. O1's new window still
  showed the empty board where the neon sign had hung, right after R11 where the sign lights up again: cropped to the
  window alone.
- Faces across shots: a face that reads older in one shot reads as another person. The blind review saw it first.
- Costume patterns, prop materials and shoe styles drift between generations. List them; fix what reads at speed.

## Leave what works

Review notes the director decided to keep in HONG KONG, with the reason recorded: a background cat that looks long
because the board has it stand up and sit down; ears flattening when a drop hits (reads as a reaction); the cabinet
swap that two reviews called a fault (it is the story). Also: when an alternating 3:2 frame cadence gives equal
distance per image, a strict 2:2 cadence makes the speed jump instead, so the 3:2 stayed.
