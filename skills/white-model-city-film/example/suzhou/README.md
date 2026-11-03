# Example: 《人家尽枕河》 (Suzhou)

The complete code of the Suzhou film as delivered in round 5 (257.9 s, 6,190 frames, 4K). Not included: data, audio, fonts and brand assets (licensing and size). To run it you need to rebuild them.

| Path | What it is |
|---|---|
| `制作总结.md` | production summary: numbers, sources, models, workflow, the five revision rounds, lessons (Chinese) |
| `方案.md` | the living plan: chapter table, HUD spec, fact sheet with source links, per-round status log (Chinese) |
| `提示词_优化版.md` | how the user's original prompt was rewritten into a buildable brief (Chinese) |
| `prep/` | data prep: `common.py` (extent, local frame), `fetch_osm.py`, `osm_layers.py`, `cmab_buildings.py`, `film_layers.py`, `satellite.py`, `pj_*.py` (Pingjiang stele tracing and georeferencing) |
| `render/` | the film: `src/timeline.js` (everything time-based), `src/world.js` (scene), `src/hud.js`, `src/post.js`, `src/main.js`, `src/vo.js` (generated), `capture.mjs`, `make_srt.mjs` |
| `vo/` | `plan_v2.py` (the warp; `scripts/plan_warp.py` is its general form), `build_vo.mjs`, `mix_v2.py`, `split.py` (cut a full TTS take into lines), `align.json` (score file, start, pauses), `v4/script.txt` (TTS text), `v4/lines.json` (line lengths) |
| `out/` | `encode.sh` and the bilingual SRT |

## Rebuilding the inputs

1. `data/raw/cmab/`: download the CMAB tiles that cover the extent in `prep/common.py`, then run `python prep/cmab_buildings.py data/raw/cmab data/layers`.
2. `python prep/fetch_osm.py data/raw/osm`, then `python prep/osm_layers.py data/raw/osm data/layers`, then `python prep/film_layers.py data/layers data/raw/osm`.
3. `python prep/satellite.py data/layers`.
4. Pingjiang map: the `pj_*` scripts expect a stele photo and traced lines; see the docstrings. Licensed sources are listed in `方案.md`.
5. Fonts into `render/fonts/` (Noto Sans CJK SC Regular/Medium/Bold, Noto Serif SC VF, Inter VF, Ma Shan Zheng), an optional watermark at `brand/sumi-studio-logo.png` (missing watermarks are hidden), and `npm i` in `render/`.
6. Narration lines into `vo/v4/lines/NN.wav` and the score at the path in `vo/align.json`.

Then: `node render/capture.mjs --out out/preview --from 0 --to 6190 --scale 0.5 --workers 4`.
