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
