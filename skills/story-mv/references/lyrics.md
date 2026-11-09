# Lyrics on screen, without reading them

Song lyrics are someone else's text. The director never writes, transcribes, prints or repeats them, and does not
open the lyric file. The user supplies the file; tools read it at run time and print only numbers (times, counts,
boxes). No lyric text goes into a tool call, a prompt, a log, a commit or a report.

- Do not transcribe lyrics with speech recognition to put them on screen. The user's file is the source.
- Reviews use a placeholder render: every Latin letter drawn as H and every Chinese character as 永, the character that holds
  all eight basic strokes (`LYRIC_MASK=1` in HONG KONG), same font, size, timing and position. Reviewers judge placement, timing, readability and cuts on that
  version. The real-text version is checked by numbers only: text boxes, frame counts, the logo region, identity of
  every frame outside the lyric areas.
- The user proofreads the real text and listens to the timing; say so at delivery.
- A public or gallery copy of the film leaves the lyrics out along with the song.

## Timing

1. **Rough positions.** Forced alignment of the user's lines (Whisper, several windows, with the line before as
   context) gives each word a rough time.
2. **Do not trust aligned starts.** Whisper's DTW lets the first word after a pause absorb the pause. In HONG KONG
   first words of English lines lit 0.93 s early on average, 3.1 s at worst; mid-line words about 0.2 s early. It
   looked right on a layout sheet; the user caught it watching with the song.
3. **English: the cut test** (`scripts/lyric_cut_test.py`). Feed the audio from a moving start point with the line's
   words forced and watch where the word's probability collapses for good; the strongest audio onset just before it
   is the start. Tested on synthetic speech with known onsets: 1 ms off.
4. **Chinese hooks Whisper cannot hear** (every character at the probability floor): use the onsets that the repeats of
   the same hook share. Find the true repeat offset by cross-correlating the audio (HONG KONG: the two choruses were
   97.391 s apart, correlation 0.644), then the bar grid. Tell the user this part rests on that method.
5. Light each word on the first frame at or before its onset, on the audio as it plays in the film (after any delay).
6. No clean vocal stem was available on the platform (its vocal separation returned only the left-minus-right side
   signal), so HONG KONG timed against the centre channel. A real stem is better if you can get one.

## Layout

HONG KONG's lyric style, built for the film's neon-sign city:

- English: Futura capitals with wide letter spacing, each word lighting up like neon as it is sung, with a faint
  reflection on the wet ground. Each line sits in the empty part of its shot and goes out at the cut.
- Chinese: vertical Weibei columns, one column per clause, like old Hong Kong shop signs.

Rules the user and the reviews set:

- **Never leave a line's last word alone in the next shot.** If timing pushes the last word past a cut, make the whole
  line one block in a place that is empty in both shots, let the block stay through the cut, and light the last word
  in place on time. (User note on the eighth version: a single word thrown into the next shot "切得难受".)
- In a block that ends on a hard cut, the last word stays lit at least 15 frames; earlier words move earlier.
- The first character of the next column should not light alone before the cut. Six places in HONG KONG still do it for
  16 to 20 frames; the user let them be.
- Keep text off the cats, hands and faces: move it, shrink it, or end it at the cut.
- On light backgrounds every glyph gets a solid dark outline. A soft dark glow raised contrast only from 1.9 to 2.1.
- When a re-shot clip brings big bright motion behind the text (fireworks, signs lighting), check readability again.
- Safe area 5 % of the frame. HONG KONG has one column at 3.8 % from the right edge on purpose: inside the safe area
  it would touch the grey cat. Record such exceptions for the user.

The layout code reads per-block specs (position, size, glow, outline, hard end) from JSON, and manual moves are kept in
an overrides file applied after automatic placement, so a re-run of the placement does not lose them.

The HONG KONG layout and rendering code was written for that film and is not in `scripts/`. Build the layer for each
film from the rules above, with the same split: placement from numbers, review on placeholders.
