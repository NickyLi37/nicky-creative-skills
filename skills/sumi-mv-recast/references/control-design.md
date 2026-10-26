# Control design

## Align before generating

Probe RGB and Depth independently. Record dimensions, rational fps, first PTS, frame count and selected source interval. The Depth file may cover the entire MV while the output covers only a dance segment. Match several poses and cuts at the beginning, middle and end; compute a measured frame offset. If frame rates differ, retain both originals and create an explicitly documented common timeline. A fixed offset cannot fix time drift.

For short references below the model minimum, prefer real neighboring frames when their context is useful. A terminal hold is an alternative only if explicitly mapped and visually checked. Keep repeated control frames out of the owned output interval. Never assume a generated clip's first frame is the reference's first event: inspect it.

## Clean plates and anchors

Remove people and their attached shadows from a representative scene frame while retaining the set, road markings, reflections, lamps, vanishing points and blue/warm illumination. Inspect at full size for residual heads, limbs and altered perspective. One plate rarely covers a moving camera or a reverse angle: use distinct views where needed.

Then compose an opening anchor from the clean plate, approved identity and actual first-frame blocking. A clean plate by itself can cause an empty-scene introduction. The anchor must preserve facial design rather than import a realistic nose/eyes from the original performer. Treat face shape, eye geometry, hairline, head ornament, costume neckline and proportions as a coherent identity.

Review the anchor before animating it. A correct accessory does not compensate for a changed face. Keep approved and rejected anchors in different folders and store their status in the ledger.

## Character assignment

Create a cast table with `character_id`, approved appearance version, distinct silhouette, body-slot role and forbidden substitutions. Assign the lead unambiguously. Use closer framing references for close-ups and full-body images for dance shots. Avoid references with props that would introduce new hand actions.

Track identity through body motion and occlusion, not through current horizontal position. For example, slot `front-right-at-start` stays with that body after a turn, even when it crosses screen center. Promote a named supporting character only when requested and consistent with source blocking; do not move performers merely to make every reference visible.

Crowd sheets reduce reference count but weaken single-character specificity. Maintain distinguishable hair/ears/colors/clothes and enough separate extras for visible foreground slots. A large sheet is not automatically better than a focused cast subset. If crowd count exceeds unique assets, report the exact exception or obtain additional designs; don't silently clone the lead.

## Depth variants

A linear depth map keeps depth values more direct. An enhanced relief representation may show face/clothing volume more clearly but can add texture-like cues. Test the supplied variants on a representative shot; neither is a universal winner. Record polarity (near white or near black), alignment and source generation method if known. Do not claim a particular depth-estimation algorithm when the user supplied the file and its provenance is unavailable.

Use colored proxy tracks only for a diagnosed ambiguity, such as two crossing bodies. Explain that the color identifies a motion slot and must not appear in the output. Inspect for unpainted gray/blue figures and duplicated leads. A proxy is guidance, not a segmentation or identity guarantee.

## Registration is a separate gate

These controls separate visual responsibilities; they are not a method to bypass supplier restrictions. A registration error can happen before generation. Preserve the raw error code, message, request identifier and asset identifier in private logs. Unknown is not proof of copyright rejection. Do not publish those identifiers or temporary signed links with this skill.
