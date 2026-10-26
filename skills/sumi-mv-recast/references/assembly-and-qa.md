# Assembly and acceptance

## Owned frames

Use half-open frame ranges `[start, end)`, so their length is `end - start`. Preserve exact rational fps. Validate that the first output starts at zero, every next start equals the previous end, and the last end equals the target frame count. Every chosen generated range must exist and have the same number of owned output frames unless a deliberate retiming is explicitly accepted.

Keep source RGB, control and generated frame mappings separate. A hold added to meet a model's minimum reference length is not source motion. Render only selected frames, exclude failed/unreviewed candidates, and count any original-footage placeholders explicitly. Zero placeholders is a completeness check, not proof of perfect choreography.

## Audio

Keep a continuous soundtrack across editorial cuts. If preserving source audio, extract the exact chosen interval once and use it for the complete assembly. Encode it once if PCM must become AAC. Do not repeatedly encode or concatenate per-shot AAC: segment priming/padding can create boundary artifacts.

For a later visual-only revision, map audio from the approved master with stream copy. Compare audio stream parameters, packet count, payload hashes, timestamps, durations and skip metadata; “same bitrate” is insufficient. If the source and result intentionally use different codecs or encodes, packet equality is the wrong test: disclose this and verify decoded duration/sync/listening instead.

## Local shot replacement

Identify the defect by exact output frames, not only a rounded player time. Generate a sufficient motion window, select its owned frames, upscale the selected take to the master dimensions and verify both cut boundaries. Review every frame of a very short repair when practical.

Frame-accurate video stream-copy cuts are not generally possible at arbitrary frames. A tested boundary-aware workflow can preserve unrelated compressed frames, but mixing AVC sample descriptions is a player-compatibility risk. Prefer one consistent final encode when that gives a more reliable ordinary MP4; keep audio copied and the old master intact. Do not claim “all untouched video bytes preserved” after re-encoding. Compare image quality outside the patch when quality loss is a concern.

## Upscale and watermark

Record actual input/output dimensions, fps and frame counts. Preserve sample/display aspect ratio; do not stretch 4:3 to a 16:9 preset. Enhancement can alter linework and faces; inspect the close-up and turn samples after it finishes. Spatial normalization of an alternative model's output must not silently change speed.

Use an approved transparent logo, maintain its proportions and clear space, and check against bright/dark backgrounds. Apply a static watermark to the final accepted cut, then repeat media/audio checks because a watermark normally entails video re-encoding.

## Acceptance layers

| Layer | Required evidence | Does not prove |
|---|---|---|
| Technical | Full decode, dimensions/SAR/DAR, fps, frames/PTS, expected duration, audio checks | Identity, choreography or aesthetics |
| Visual | Compared first/last frames, poses, turns, entrances, masks and repair boundaries | Unseen frames or legal clearance |
| Playback | A real player reaches the end without media error, with playback mode recorded | Every detail was visually reviewed or audio was listened to if muted |
| Editorial | Complete ledger, chosen versions, no gaps/overlaps/unapproved placeholders | Pixel-exact reference reconstruction |
| Distribution | Appropriate rights and platform scope, assessed separately | A video remaining online is authorized |

Use statuses such as `pending`, `rejected`, `accepted_with_limits`, `accepted`. Keep known limits attached to their shot even if it is accepted. A “major issue frames = 0” total must not erase ordinary accepted deviations.

Inspect leading foreground identities more strictly than distant extras only when the brief permits. Record repeated/missed background characters, expression differences and phase offsets explicitly. After technical checks pass, repeat them only when edits or unresolved defects justify it.

## Delivery

Provide the final master and obvious navigation, an EDL/ledger, provenance for selected media, an acceptance summary and checksums. Keep original masters and provider files. If editing records contain relative links across rounds, retain the necessary sibling directories or rewrite and verify the links as part of a deliberate package export.

For public release of this skill, include only original documentation/code and synthetic fixtures. Exclude music, MV frames, character sheets, logos, private IDs, account balances, temporary URLs, upload tickets and personal filesystem paths. The license for the skill does not license any user's project media.
