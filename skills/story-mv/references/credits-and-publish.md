# Credits, cover and release

## Credit cards

- Check every credit in several public sources before it goes on a card: song title as officially written, artist,
  release date, writers, producers, and the sampled song's singer, composers, lyricist, arranger, album and label.
  HONG KONG checked Apple Music, Spotify, KKBOX, Album of the Year and music press. Write nothing from memory; leave
  out what no source states (the single's label could not be confirmed and was left off).
- Write the official title exactly: `HONG KONG (feat. 王菲季候風)`, with no space between the names, as the stores
  list it.
- Cards of three to six lines. Size each card's full-light time from its word count at 4 words a second before the
  first render (`scripts/card_timing.py`). HONG KONG lost two build-and-review rounds, about 40 minutes each, to cards
  that were too short to read. Leave about 1 s of black after the last card.
- One opening card on a dark part of an early shot; the closing cards on black after the song.
- A fan-made film says so on a card: all music rights belong to their owners, not affiliated with the artists or
  their labels. Credit the animals' home and the tools.

## Cover

The user wanted the title alone, big, on one line, with no artist names and no tagline (`scripts/title_cover.py`):

1. Render a clean still through the film pipeline with no text and no logo.
2. Cut the subject out with macOS Vision (`scripts/subject_mask.swift`). Check the mask at full size: on HONG KONG a
   tail tip showed above the orange cat's head and read as a hair bun against the red letters, and the mask edge
   carried a thin dark fringe (pulled in 2 px and softened).
3. If the user shows a type reference, match it by measuring. No system font is condensed enough; squeezing a heavy
   face per glyph gets there without installing fonts. HONG KONG: Impact with H at 0.285 of the cap height, letter gap
   0.033, word space 0.19, pure red letters (253, 1, 1 measured inside the reference's letters) and the dark red glow
   only outside them; a glow screened over the letters turned them orange-pink.
4. Feather the picture into the dark only where its edge shows; never feather the subject's mask, or heads go
   half-transparent.
5. Offer a 16:9 cover whose title, subject and logo all sit inside the centred 4:3 area, for platforms that crop to
   4:3 (the user picked this one as the final cover).
6. Save JPEG at 4:4:4 so the red edges stay clean. YouTube's thumbnail limit is 2 MB: the 4K cover at quality 90 was
   1.17 MB.

## Release copy

- Find each artist's official account on each platform before tagging (verified badge, account number), and link
  official listening pages, not a third-party upload.
- Declare AI-generated content where the platform asks.
- YouTube: Content ID will most likely claim the song; the ad money then goes to the rights holders and some regions
  may block the video.
- X: a free account takes videos up to 2 min 20 s and 512 MB. A 4-minute film needs Premium, a short cut, or a cover
  image with a link.
- Run every line of copy past the user's style rules, for example a ban on AI parallel phrasing such as
  「A没了，B还在」 and 「不是X而是Y」.

## A package to send

Films (4K and 1080p), the final cover, a set of strong shots (storyboard frames and clean graded shot clips without
lyrics), an overview sheet and a short readme, in one folder and one ZIP (`scripts/share_pack.py`). Shot clips rendered
from the clean master must avoid frame ranges that were patched later, or they will not match the film. Ask before
including close-ups of a person's face.
