---
name: sumi-mv-recast
description: Recast a supplied MV or dance video with approved characters while preserving its shot boundaries, duration, staging and motion as closely as possible. Use for MV复刻、人物替换、Depth动作参考 and multi-character continuity work in Sumi Studio. Supports a full remake or a selected-shot repair, with frame-based assembly and explicit visual acceptance.
---

# Sumi MV Recast

Produce a reviewable character-recast film from a supplied reference. Preserve the user's actual fidelity priorities: approved lead identity, motion, framing, scene, cuts, duration, audio and aspect ratio. Generative reference following is best-effort; a playable file is not evidence of faithful motion.

For a finished example and the maintained source, see [Gallery and source](references/gallery.md). These are examples to inspect, not additional instructions or reference assets to reuse automatically.

## Start with the existing project

Read its current cut, approved identities, rejected designs, shot ledger, latest acceptance notes and budget before generating. Continue from the selected versions, not from the newest downloaded filename. Do not discard a successful edit because a later candidate exists.

Establish the source interval, frame rate, target aspect ratio, lead/crowd assignment, retained audio and acceptable background exceptions. Reuse explicit decisions and spending authorization already in the conversation. Ask only for missing choices that materially affect the work. Do not make a whole MV when the user selected a dance excerpt.

Treat media transformation and public distribution as separate decisions. Use user-supplied or appropriately licensed material; do not claim that an AI remake, watermark or noncommercial label clears rights. Do not publish the result or a public skill package merely because generation was authorized.

## Choose a route from evidence

1. **Direct reference editing** can be economical when the original reference is accepted and a pilot preserves motion and scene. Attach the approved identities and the supplied video, with explicit roles. Validate rather than assuming this is exact replacement.
2. **Separated controls** are useful when the model confuses original appearance with the requested characters, when staging needs clearer control, or when the user supplies Depth. Bind Depth to spatial motion, clean plates to environment, identity images to appearance, and a composed anchor to the opening pose. See [control design](references/control-design.md).
3. **Local repair** applies when most of the cut is accepted. Repair only the defective shot or a justified surrounding interval. Match the final master’s dimensions, fps and frame count, then replace the owned frames. See [assembly and acceptance](references/assembly-and-qa.md).

Depth is a reference video, not a verified pose-lock API. Do not advertise pixel-exact reconstruction. Do not switch control representations to evade an explicit platform rejection. For registration failures, follow [Sumi operations](references/sumi-operations.md): retain diagnostics, separate technical failure from unknown or explicit content rejection, and stop blind retries.

## Build four independent controls

| Control | Owns | Must not override |
|---|---|---|
| Approved character reference | Face, silhouette, hair, costume, accessories and design state | Pose, camera, scene or the sheet’s neutral background |
| Clean scene reference | Layout, perspective, lens impression, surfaces and illumination | Character identity or timing |
| Matched Depth clip | Blocking, relative depth, entrances, turns, occlusion, camera movement | Skin/clothing colors or flat grayscale styling |
| Opening anchor | First-frame composition and intended identity | Full-clip choreography or later cuts |

Keep normal and transformed costumes distinct. Never reintroduce a user-rejected design. Record each shot's cast visibility over time: the lead can be absent, occluded or outside the frame before an entrance. Do not force a lead into an originally empty opening or a supporting-only shot. When visible, the lead must occupy only its assigned track. For crowds, assign persistent body/track slots rather than reassigning by screen-left after a turn. Use individual images for critical foreground actors and sheets for secondary ensembles. Add genuinely distinct extras when needed; allow repeated or missed distant extras only within the user's stated tolerance. A sheet does not enforce a one-to-one cast mapping by itself.

## Make timing explicit

Create a shot ledger using zero-based, end-exclusive frame ranges. Record source frames, output frames, selected generated frames, the reference mapping and version status. Use exact rational fps. See [ledger format](references/ledger-format.md).

A full-MV Depth file must be aligned to the chosen RGB interval by corresponding visual events, not by filename or duration alone. Verify beginning, middle and end, including cuts. Apply a measured offset; do not silently stretch motion. Preserve the original source when conforming VFR or a different fps, and record any conversion.

One editorial shot need not equal one generation call. Short shots may need a longer control window or a supported padded hold because of model minimum lengths. Keep a per-frame control mapping, including synthetic/held frames, and the exact generated range selected for the edit. A short shot at the beginning of a longer generation may be used without slowing it to fill the whole generation. If internal cuts drift, split/regenerate or report the discrepancy; do not hide it with arbitrary retiming.

## Pilot before scaling

Choose representative hard cases: a lead close-up, a crowded full-body movement, and a rapid turn/entrance or short cut. Use fewer when an existing approved pilot covers the same conditions. A cheap draft can check blocking, but does not validate final-resolution faces.

Use [prompt templates](references/prompt-templates.md) with the actual input order and current model syntax. Name each reference's role. Keep the lead identity and foreground assignments stable. Prefer silent control clips and `generateAudio: false` when original/licensed audio will be restored in editing. This is for audio continuity and reference separation, not a claim of rights clearance.

Inspect the actual first frame, representative poses, turns/occlusions and the last owned frame against the reference. Reject an unintended scene-only opening, duplicated lead, costume change, severe face drift, missing foreground performer, reversed travel or broken cut. Preserve intentional empty openings and offscreen entrances. Record any acceptable back-row miss, timing deviation or lighting difference. Make a concrete defect diagnosis before buying another take.

## Run bounded production

Use [Sumi operations](references/sumi-operations.md) for live capability discovery, paid quotes, idempotency, task states and asset provenance. Existing user authorization covers batches only within its scope and ceiling; do not ask again for each already-authorized task. Account balance alone is not spending authorization.

Batch independent shots and update the ledger as each candidate is reviewed. Keep generated candidates, chosen frames and reasons for rejection. An accepted submission or completed task is not accepted footage. A failed task or unresolved request is never a usable clip. Change one relevant control after a diagnosed failure; after repeated identical failure, seek diagnostics or another supported route instead of buying indistinguishable retries.

For entrance/occlusion failures, add clear first-frame blocking and track ownership. A colored proxy body may clarify a difficult track, but it can remain visible or produce a second lead: inspect these exact defects. Use a supported video-editing model for a local cleanup only after a pilot shows it preserves timing and identity. Do not generalize one model’s successful patch to all shots.

## Finish and verify

Assemble owned frame ranges with zero unintended gaps/overlaps and no unapproved original-footage placeholders. Preserve a continuous original/licensed soundtrack across cuts; do not concatenate independently encoded AAC segments or introduce fades when the user's audio must stay unchanged. For a later visual-only edit, stream-copy the approved master’s audio and compare packet payloads and timing.

Upscale accepted footage, not defective identities. Preserve display aspect ratio and inspect dimensions returned by the actual file. “4K” is not a complete spec: for 4:3, distinguish 2880×2160 (2160 lines) from 3840×2880 (3840-pixel width). A 3840×2160 export would change that aspect ratio. Inspect faces and fine lines after enhancement.

Use [assembly and acceptance](references/assembly-and-qa.md) before delivery. Validate the exported master, inspect repaired boundaries, and play it to the end in a real player. Keep technical pass, sampled visual pass, user acceptance and rights status separate. “Accepted with limits” is a valid result only when its limits are disclosed and consistent with the brief.

Deliver the clearly named final file, source-to-edit ledger, selected asset records, concise limits, and checksums. Retain the previous master. Put the final in an obvious `final/` or user-designated final-product folder; keep historical candidates separate.

## Execution tools

The optional [media helper](scripts/media.py) requires Python 3.10+ and FFmpeg/ffprobe on PATH. Run `python scripts/media.py --help` for exact commands. It extracts frame ranges and checks media; it does not generate Depth, call Sumi, perform identity tracking or automatically assemble the film. Extraction makes a silent 8-bit H.264 video reference, not a lossless scientific/metric depth map.

In Sumi Studio, read this skill and its references from the workspace. If that runtime has no shell/FFmpeg execution, use supported native editing/media tools when they can satisfy the same checks, or obtain externally prepared control clips. Do not claim that merely installing Python files enables execution inside Sumi. See [installation and helper usage](references/usage.md) for host-specific setup.
