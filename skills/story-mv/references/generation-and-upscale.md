# Generation and 4K upscale with Sumi Studio MCP

Every call spends the user's credits. Read the model's live parameters (`get_model`), quote (`quote_task`), tell the
user the shots, seconds and credits, and wait for approval. When the user has given a cap and handed over the run,
stay inside the cap and log every task. Account balance is not authorization.

## Clips

- Seedance 2.5 (`seedance-2.5`), `generateAudio: false`, `outputFormat: "mov"`: the files come back tagged BT.709.
  Untagged Seedance files were BT.601 on earlier projects; convert before any compositing.
- HONG KONG generated at 1080p: 88 clips of 4 s or more settled at 43,692 credits in November 2026 (a 4 s clip
  settled near 460 credits against a quote of about 480). Prices change; quote each batch.
- First frame: `task: image_to_video` with `imageAssetIds`. Writing `firstFrameAssetId` returned
  MISSING_INPUT_ASSET and a full refund.
- Submit with a stable `idempotencyKey`, wait with `wait_task`, download the original with
  `get_asset_download_url` into the project, and log shot, take, task, model, resolution, seconds, credits and time
  in a ledger (one JSON line per task). Never publish the ledger: it holds task and asset ids.
- Generate the hardest shots first and look at them before the batch.
- Download every take. Old takes stay; the pick happens at the end.
- If an uploaded image disappears from the platform with no reason (`inputAssetsUnavailable`, not in the trash), do
  not upload it again and do not route around it. Reuse assets the platform already holds, repair locally, tell the user, and
  let the user ask the platform why.

## 4K

- Upscale the accepted cut, not every take. HONG KONG used Sumi `mediakit-video-enhance` at tier `4k`. On a test
  shot the `professional` tool version kept more detail than `standard`, and its flicker matched the source clip,
  so professional was used.
- Split the 1080p cut into chunks that end on shot boundaries (`scripts/upscale_chunks.py`). HONG KONG: 13 chunks
  of about 17 s, run side by side. Each job holds its whole quote and refunds the difference: all 30 upscale jobs
  (chunks, the test and single-shot redos) settled at 19,113 credits against 80,101 quoted.
- The enhancer accepts Sumi's own output assets directly, so a re-shot clip can be upscaled without uploading it.
- Look at faces, wet fur and fine lines after upscaling. The enhancer drew lines into skin on her close-ups and
  cracks into a cat's wet head fur. Mix the plain 1080p picture back under the upscale there (HONG KONG used
  85 % 1080p on the cat's head, and a per-shot share on her close-ups).
- Keep a map from film frames to chunk frames (`chunks.json`), so a repaired shot replaces exactly its frames.

## Totals for HONG KONG

| Item | Count | Credits |
| --- | --- | --- |
| Seedance 2.5, 1080p | 88 clips | 43,692 |
| 4K upscale, professional | 30 jobs | 19,113 |
| Total | | 62,805 |

GPT Image ran on the user's own OpenAI key and is not in the table.
