# Sumi operations

Use the connected user's account and current tools. This is a workflow, not a frozen HTTP client or a guarantee that a named model is available.

## Discovery and task contract

1. Call `doctor` to confirm connection and relevant scopes. Report a missing scope accurately; do not ask for a new login or extra permissions when existing scopes suffice.
2. Discover the desired model with `list_models`, then `get_model` for the actual task type. Verify supported references, number/total duration of videos, dimensions, fps, file size, output durations, resolution, aspect ratio and audio toggle. Model display names and request keys are not interchangeable.
3. Use `list_skills` for task types. In Sumi itself, optional official model skills can supplement prompting if available. This package does not depend on their private text.

Verified on 2026-10-26, `seedance-2.5` / `reference_to_video` exposed `imageAssetIds`, `referenceVideoAssetIds`, `referenceVoiceAssetIds`, `prompt`, `duration`, `aspectRatio`, `resolution`, `generateAudio` and `count`. It used `Image N`, `Video N`, `Audio N` prose references. That snapshot allowed output durations 4–30 seconds, resolutions through `1080p`, and reference video totals through 30.2 seconds. These are historical observations: re-read the live guide before every new production, and do not copy these limits to another model or task type.

An illustrative request shape, not a runnable paid request:

```json
{
  "taskType": "reference_to_video",
  "modelKey": "CURRENT_MODEL_KEY",
  "idempotencyKey": "PROJECT-SHOT-REVISION-UNIQUE_KEY",
  "input": {
    "prompt": "PROMPT_WITH_ACTUAL_INPUT_ORDER",
    "imageAssetIds": ["APPROVED_ANCHOR", "APPROVED_LEAD", "CLEAN_SCENE"],
    "referenceVideoAssetIds": ["ALIGNED_SILENT_CONTROL_CLIP"],
    "duration": 4,
    "aspectRatio": "4:3",
    "resolution": "1080p",
    "generateAudio": false,
    "count": 1
  }
}
```

## Credits and uncertain outcomes

Obtain a cost estimate/quote and explicit scope plus spend ceiling before paid creation. Include reference-video fees, registration deposits when quoted, separate upscale charges and a bounded repair reserve. Quotes can expire and prices can change. A balance reading is not approval to spend it; prior user authorization remains valid within its stated scope and limit.

Prefer `quote_task` immediately before `create_generation_task` with the exact quoted request and stable idempotency key. A changed request is a new revision/key. If creation times out or the outcome is unknown, use `find_task_by_request` before resubmitting. Do not mistake a queued response for finished footage. Poll boundedly with `wait_task` or `get_task` / `get_tasks`, and persist final charge/refund facts rather than estimating spend from the number of clips.

Store task/asset identifiers, model, prompt, input order, returned dimensions, cost, state and acceptance separately. Use canvas versions when writing shared nodes; on a version conflict, reread and recompute.

## Assets and registration

Follow the current upload guide: create a ticket for the exact file metadata, upload bytes with its returned headers, complete multipart uploads when required, then commit. Never place service authorization headers on a signed storage upload. Temporary URLs and upload tickets belong in private runtime records, not the public skill or release ZIP.

Classify an error before retrying:

- Documented transient transport error: retry the same operation with its documented idempotency/resume behavior, within a bounded retry count.
- Explicit format/size/fps/duration error: prepare a conforming derivative, preserve the source and mapping, and retry the corrected request.
- Registration rejection with no explanation: preserve code, message, request ID, asset ID and timestamp, and request platform diagnostics. One unmodified retry may test a transient failure if allowed; repeated unexplained rejection is not proof of a technical or copyright cause.
- Explicit content/rights restriction: stop that input path and use properly authorized, accepted material or the platform's review process. Do not recut, blur faces, remove audio or convert to Depth for the purpose of defeating that restriction.

Silent references and depth-based controls are useful production representations when accepted and appropriate; they do not clear rights or guarantee registration.

## Finish and install

Inspect the actual final file after `export_film` or an enhancement task. “Succeeded” means a service task completed, not that fps/aspect/audio/identity meet the brief. If local execution is unavailable, preserve honest “not verified” states for checks that require it.

For a private Sumi installation, create `skills/sumi-mv-recast/SKILL.md` with `create_user_skill`, add supporting files with `write_workspace_file`, and read them back. Use `expectedVersion: 0` only for new files; preserve unrelated existing skills. Remote text storage does not prove that a Python helper can execute in that environment.

Public Sumi market publication is a separate operation: `publish_user_skill` requires explicit agreement to publish under MIT. Never set `licenseAccepted: true` merely because a private skill was created. GitHub publication likewise needs the intended repository, public visibility and license authorization; preparing this package is not itself publication.
