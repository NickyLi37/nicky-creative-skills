# Validation record

Checked on 2026-10-26. The original record below covers the self-contained skill package, not a new paid production. Its later public release and Gallery are additional delivery layers.

## Local helper

Seven synthetic-media tests passed with Python 3.15.1 and FFmpeg 8.1.2. The scripts use only the Python standard library; the declared minimum is Python 3.10, which was not separately exercised.

- Exact zero-based, end-exclusive frame selection at rational frame rate, with audio removed.
- Native geometry and color-reference preservation within lossy H.264 tolerance.
- Wrong frame count, fps and aspect-ratio contracts rejected.
- Existing outputs, invalid intervals and output/report aliases protected against overwrite.
- Exact copied AAC accepted; re-encoded or shifted audio rejected.
- Variable timing rejected, including a missed frame with a coarse timebase.
- All temporary synthetic fixtures removed after the run.

Test names group several assertions; run `python3 skills/sumi-mv-recast/tests/test_media.py` to reproduce. No production media, credentials or online service are required.

## Independent decision review

A separate reviewer exercised the actual skill against a scenario with mismatched source/Depth frame rates, an unexplained asset-registration rejection, and a next quote exceeding the remaining authorization. The resulting plan stopped paid batch submission, continued free preparation, required event-based time mapping, and did not infer the rejection's cause.

The review found and corrected two real omissions: prompts now preserve an absent/offscreen lead and intentional empty openings; the ledger now records both frame rates, timestamp origins and offset direction. A second review found those items resolved and all nine skill-relative links present.

The skill frontmatter passed the skill-creator validator. Package inspection found no bundled production media, personal paths, signed URLs or runtime caches.

## Boundaries

No fresh paid model generation or runtime execution of the Python helper inside Sumi Studio was performed for this package validation. The original private installation was verified by reading back its text files. It was subsequently published to the Sumi skill market with the owner's explicit MIT agreement; the public listing is linked from README. Media tests do not evaluate character identity, choreography, scene fidelity or distribution rights.

## Public collection and Gallery

The collection adds a data-driven Gallery, separate category/style filters, and tests for multi-skill catalog entries, local-path containment, invalid links, duplicate identifiers, filtering and media URL handling. GitHub Actions validates these files before deploying `site/` to Pages. Check the repository's Actions tab for the actual result of each revision.

The Gallery includes a separately licensed, complete silent preview and an extracted poster. These media are outside the self-contained skill folder and outside MIT. Browser playback and preview-media checks are separate from synthetic helper tests. No new paid film generation is needed for this publication.

## Suzhou skill and project page — 2026-11-03

The new `white-model-city-film` package passes the Skill Creator validator. Its 70-file `.skill` archive was CRC-checked and compared byte-for-byte with the published source folder. It contains no datasets, production audio, original map imagery, fonts, caches, credentials or personal absolute paths.

The 6 catalog tests, 4 Gallery tests, 7 existing media-helper tests and 2 new server tests pass. The server tests make real HTTP requests against both included servers and cover normal files, traversal, symlink escapes, malformed paths and continued service after errors. The new helper files passed Python/JavaScript/shell syntax checks. The example's SRT was regenerated identically, and a synthetic timing plan passed finite-value and monotonicity checks.

The full web preview was verified with ffprobe: 1920×1080, H.264/AAC, 24 fps, 6,190 video frames and 257.916667 seconds. The webpage reuses the existing delivery file without encoding changes. Its three JPEGs come from final 4K frames. All static page/media links resolve locally. Browser checks cover Gallery search, navigation to the project, video playback starting and advancing, desktop layout and a 390-pixel mobile viewport with no horizontal overflow.

Publication did not rerender the full city, regenerate audio, spend Sumi credits, test installation in Claude.ai, or replay the complete data acquisition and 4K pipeline. Responsive browser emulation is not a physical-phone test. No continuous human listening or new historical-fact review was performed. The original production QA remains a separate historical record.

## Story MV skill and HONG KONG project page — 2026-11-09

The new `story-mv` package passes the Skill Creator validator. Its 43-file `.skill` archive was CRC-checked and compared byte-for-byte with the published source folder. It contains no film, clips, frames, character boards, song, lyrics, fonts, logo, caches, credentials, task or asset IDs, or personal absolute paths. A script read the lyric files at run time and counted lyric word sequences in every text file of the repository without printing them. The only overlaps were the song title and four single four-word or four-character phrases inside ordinary sentences: a caption on the project page, a step in `story-and-board.md`, and two lines from the Suzhou release. An independent reviewer and a Sepia review then read the release; their findings on wording, numbers and one passage about uploaded images were fixed before publication.

11 of the 12 script tests pass with NumPy 2.5, OpenCV 5.0, Pillow 13 and FFmpeg 8.1.2 on an Apple M1 Max. The twelfth, the Whisper onset test, runs only with `STORY_MV_ASR=1` on Apple silicon; it passed when enabled. Without NumPy, OpenCV and Pillow, 8 tests skip. A separate CI job installs those packages on Ubuntu and runs the tests; it does not gate the Gallery deployment. Writing the beat-phase test showed that the production onset detector labelled hits about 36 ms early. The published script is calibrated, and the case study records what this means for the film's audio offset.

The 6 catalog tests, 4 Gallery tests, 7 media-helper tests and 2 server tests pass.

The Gallery copy was rendered by the film's own finishing pipeline from the same 4K master with the lyric layer off: 5,232 song frames in 34.5 minutes with 9 processes, followed by the existing closing cards. All 5,956 frames were compared with the delivered version 15 at 640×360. Frames without lyrics differ by a median of 0.94 levels (encoding). Every other difference is local brightening covering at most 24 of 144 grid cells, and the 724 closing-card frames match within 0.16 levels. Coarse difference maps of the most-changed frame in each of five lyric-bearing patch ranges show only text-shaped areas where version 15 is brighter. ffprobe of the web file: 1280×720 H.264 High, 24 fps, BT.709, 5,956 frames, 248.166667 s, no audio stream, 46,515,060 bytes. The poster is the approved cover file, byte-identical; the two stills are frames 720 and 1320 of the lyric-free render.

Browser checks used a local server with byte-range support: Gallery order, card links, category, style and search filters, the project page's local links and images, playback starting and advancing, a seek to 2:00, a seek near the end with natural completion, and a 390-pixel viewport with no horizontal overflow on both pages. Python's built-in `http.server` does not serve byte ranges, so seeking fails there; GitHub Pages serves them.

Publication generated nothing new and spent no Sumi credits. Nobody listened to the master again, and the lyric text was not checked; the user proofreads lyrics. The browser pane was hidden for most of the check, so layout was judged from layout measurements and desktop screenshots, not by eye at every width. No install test in Claude.ai and no physical-phone test were done.
