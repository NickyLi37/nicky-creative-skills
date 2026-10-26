# Prompt templates

Replace all braces and verify the model's actual reference syntax. The examples use Sumi Seedance `Image N` / `Video N`, counted separately from 1 by modality. The attachment list, not the asset's title, determines N. Do not put asset IDs into prose and expect them to bind. Strong words describe the target; they do not make model output deterministic. Derive lead presence and visible counts from the shot, including offscreen intervals, entrances and occlusion; never invent a lead in a supporting-only shot. Remove unused reference clauses and renumber the remaining attachments.

## Clean scene image

> Image 1 is the scene geometry reference. Remove every performer and person-attached shadow. Preserve the camera viewpoint, lens impression, framing, architecture, ground texture, lamps, fog, reflections, vanishing points and illumination. Fill only the removed-person regions coherently. Do not invent new set pieces, rotate the camera or redesign the location. Output a clean environment plate with no people, text, labels or contact-sheet borders.

## Opening anchor

> Image 1 is the approved identity for {LEAD}. Image 2 defines scene geometry and lighting. Image 3 defines opening-frame blocking and pose only. The lead's opening visibility is {LEAD_OPENING_VISIBILITY}; only if visible, place it at {FRAME_LOCATION}, with {POSE_AND_FACING}, matching the subject scale and occlusion in Image 3. Preserve the approved face geometry, hair, {DISTINCTIVE_ACCESSORIES}, costume and proportions. Use the environment's light on the character. Do not import the reference performer's face, clothes or realistic anatomy into the approved design. Preserve an intentional empty opening when specified. No invented or extra lead, collage, labels or new props.

If Image 3 contains another person's identity, only use it through an accepted, appropriate reference workflow. A depth/pose representation can supply composition without being an identity reference.

## Depth driven recast

> Recreate the supplied {ASPECT_RATIO} shot with the approved cast.
>
> Video 1 controls motion, spatial relations, timing, occlusion and camera path. It is a depth representation, not the target surface appearance. Image 1 defines the opening composition. Image 2 defines {LEAD}'s identity. Image 3 defines the scene. Images 4–{LAST} define {CAST_MAPPING}.
>
> At the first output frame, show {OPENING_STATE}. Follow {LEAD_VISIBILITY_AND_ENTRANCE_TIMES}; when visible, keep the lead attached only to {LEAD_BODY_SLOT}, with no duplicate. Do not add it before its entrance or into a shot where it is absent. Preserve its {IDENTITY_INVARIANTS}. Each supporting identity follows its assigned body through turns and occlusion. Do not exchange identities when bodies cross.
>
> Follow these events at the original speed: {TIMED_EVENTS}. Preserve the original camera distance, viewpoint and cut boundaries: {CUT_TIMES}. Do not create a close-up, extra cut, slow-motion section, loop or freeze inside the owned interval.
>
> Image references supply appearance, not standing poses or sheet backgrounds. Render all visible intended performers as {TARGET_STYLE}, integrated into {SCENE_LIGHTING}. No proxy-body colors, residual source performers or duplicated foreground characters. Crowd exceptions: {USER_APPROVED_EXCEPTIONS_OR_NONE}.
>
> The final edit uses {OWNED_INTERVAL}; {TAIL_POLICY}. No text, logos or generated audio. Requested output duration: {MODEL_SUPPORTED_DURATION}.

If a fixed keyframe input is available, use it instead of relying solely on the phrase “Image 1 defines the opening.” If not, state that first-frame adherence remains uncertain and inspect it.

## Direct RGB reference edit

> Video 1 is the source for this shot's scene, camera, timing and motion. Replace only the assigned performers: {CAST_SLOT_MAPPING}. Image 1 defines {LEAD}; Images 2–{LAST} define the supporting identities. Keep the same environment, viewpoint, count, spatial relationships, entrances, turns and cut timing. Do not use the still images' poses or neutral backgrounds. Follow {LEAD_VISIBILITY_AND_ENTRANCE_TIMES}; preserve identity through occlusion without duplicating the lead or adding it when absent. No new props, subtitles, effects or audio. Preserve {OWNED_DURATION} at its original speed; extra generation duration is {TAIL_POLICY}.

## Local identity repair

> Video 1 is the accepted motion and environment base. Replace only {DEFECTIVE_BODY_OR_REGION} with {APPROVED_CHARACTER}, defined by Image 1. Preserve the existing body trajectory, pose timing, camera, background, nearby cast and occlusion. Follow {VISIBLE_CAST_COUNTS_OVER_TIME} and {LEAD_VISIBILITY_AND_ENTRANCE_TIMES}. Remove the defective/proxy version rather than add another person. Preserve {FACE_HAIR_COSTUME_INVARIANTS}, including at profile, back view and motion blur. Do not introduce realistic facial details absent from the approved illustration. No new cut, text, audio or timing change.

## Review questions after each take

Does frame zero match the intended cast visibility, including an intentionally empty frame? Is the same identity present during the hardest turn and after re-entry? Does the shot finish its final action? Are body ownership, foreground count, scene geometry and source cut timing preserved? If not, change the relevant reference or route rather than merely making the prompt longer.
