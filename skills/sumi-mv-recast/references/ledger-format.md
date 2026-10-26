# Ledger format

Use JSON/CSV that records what was actually selected; do not depend on filenames to imply approval. This is an illustrative schema, not a model API payload. Use zero-based, end-exclusive intervals throughout.

```json
{
  "fps": "24/1",
  "target_frames": 240,
  "aspect_ratio": "4:3",
  "source_interval": [1200, 1440],
  "control_alignment": {
    "source_fps": "24/1",
    "control_fps": "24/1",
    "mapping": "source_time_seconds = control_time_seconds + offset_seconds",
    "offset_seconds": "0/1",
    "verified_events": ["start", "middle", "end"]
  },
  "shots": [
    {
      "id": "S001",
      "source_frames": [1200, 1248],
      "output_frames": [0, 48],
      "generation_id": "local-take-S001-v2",
      "generated_frames": [0, 48],
      "generated_file": "generated/S001-v2.mp4",
      "control_file": "controls/S001-depth.mp4",
      "anchor_file": "anchors/S001-approved.png",
      "cast_slots": {"lead": "LEAD-v3", "front-right-at-start": "SUPPORT-A-v1"},
      "status": "accepted_with_limits",
      "limits": ["distant extra repeats, permitted in brief"],
      "reviewed_frames": [0, 12, 24, 47]
    },
    {
      "id": "S002",
      "source_frames": [1248, 1440],
      "output_frames": [48, 240],
      "generation_id": "local-take-S002-v1",
      "generated_frames": [8, 200],
      "generated_file": "generated/S002-v1.mp4",
      "status": "pending",
      "limits": []
    }
  ]
}
```

Validate total coverage (48 + 192 = 240 here), contiguous output intervals, candidate bounds and actual files. This example includes a pending shot and is not release-ready. Add real checksums and task/asset IDs to private production records after they exist; do not fabricate them.

Record timestamps relative to each full source file's first displayed frame, and state the offset direction as above. For differing fps, frame numbers are not interchangeable: map verified event timestamps first, then document any conforming/resampling and a per-frame correspondence; never relabel fps to claim alignment. An offset in frames is acceptable only with its exact rational fps and coordinate system recorded. If start/middle/end offsets disagree, investigate edits or drift before choosing a mapping.

For every normalized/padded control, use a companion mapping with columns `control_frame`, `original_frame`, `kind` (`original`, `hold`, or documented conversion). Do not imply that held frames were in the reference. Financial records should distinguish quote, reserved amount, charged amount, refunded amount, payer and scope; do not infer exact cost from a budget ceiling.
