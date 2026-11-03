# Render

Three.js r170 on a page that headless Chrome loads, driven frame by frame by `scripts/capture.mjs`. The example is `example/suzhou/render/`.

## The page contract

```js
// main.js
await buildWorld(scene, renderer);       // load every layer once
await document.fonts.load('300px Callig', '苏州');  // fonts used only late must be loaded before frame 1
await document.fonts.ready;
window.renderFrame = (f) => {           // everything from f, nothing else
  const s = stateAt(f);                 // timeline.js
  world.apply(s); placeCamera(s.cam); post.render(scene, camera, s, look); hud.update(s, camera);
  renderer.getContext().finish();       // the GPU is done before the screenshot
};
window.ready = true;
```

Open `render/index.html?f=1200` in a normal browser to look at one frame while authoring (`node scripts/server.mjs <project>`).

## Scene (`world.js`)

- **Board:** a dark slab the size of the extent, with roads as thin ribbons and water as recessed glossy channels (Suzhou: deep blue-grey `#3E5560`, highlight `#8FD3E0`). Water is the hero in a canal city, so give it more contrast than the reference did.
- **Buildings:** one mesh, extruded in the shader by the per-vertex height. Each building rises once at its own story frame (`aReveal`, computed from the timeline's `revealFrame()`). Old-city blocks rise from the centre outward with noise; modern blocks rise by their CMAB year as the ticker passes it. Toggling whole zones on reads as batches popping, and the user will notice.
- **Landmarks:** pagodas as procedural tiered geometry (with the Tiger Hill lean), supertall towers from OSM heights, special shapes (the Gate of the Orient arch) built by hand.
- **Thematic layers:** ribbons with a draw-on head and travelling dashes for canals, routes and the wall; glowing pads for gates; paired red rails for bridges; and the stele photo on a grid that morphs from upright stele layout to georeferenced positions, so the photo stays under its own canals.
- `apply(state)` sets uniforms and visibility from the state object. It does nothing else.

## Post (`post.js`)

HDR scene with MSAA and depth, then a depth-of-field gather (tilt-shift look; shallower at grazing pitch, where the near ground is close to the lens), bloom, and grade/grain/vignette to the canvas. Exposure, bloom and a fade-to-black come from the timeline.

## Timeline (`timeline.js`)

Everything on screen is a pure function of the frame:

- `toStory(f)` maps a film frame to a story frame through `WARP` from `vo.js`.
- `track(keys, ease)`: keyed values with smootherstep easing, held outside the keys. Two keys one frame apart make a hard step.
- `CAM_KEYS`: `[storyFrame, {tx, ty, dist, az, pitch, fov}]`. Two keys one frame apart make a cut, which should only happen at chapter starts.
- `CHAPTERS`: id, story range, index, CN/EN names, year keys, and "big" cards switching inside the chapter.
- `SUB_TEXT` holds the text only. Timing comes from `vo.js`: 3 frames before the voice, 14 after.
- `CALLOUTS`: leader-line labels pinned to world positions, with heights, so they track the camera. `NOTES` carry hedges like 示意.
- The year ticker follows chapter year keys. Where narration says "four years later", ramp the ticker inside that line (`yearRamp`) so the number moves while the words are spoken.

Keep the story frames fixed once the picture is approved. Re-timing then only touches `vo.js`.

## HUD (`hud.js`)

A DOM overlay laid out at 1920×1080 CSS pixels and captured at any device scale factor: chapter index and names, big number card, year ticker, scale bar, callouts, subtitles, watermark and the end card. Fonts are local files: Noto Sans/Serif CJK, Inter, and Ma Shan Zheng for the end-card calligraphy (all OFL). The end card's vertical calligraphy 「苏州」 reveals character by character with a moving CSS mask.

## Capture numbers (Apple silicon, 4 workers)

| Scale | Output | Speed | 4-minute film |
|---|---|---|---|
| 0.5 | 960×540 preview | ~10 frames/s | ~11 min |
| 2 | 3840×2160 | ~0.52 frames/s (7.6 s per frame per worker) | ~3 h 20 min for 6,190 frames, ~10 MB per PNG, ~59 GB |

`capture.mjs` skips existing PNGs, so a stopped render resumes where it was. Workers load the page once. **If you edit the timeline while a render runs, stop it, edit, and restart**, otherwise the workers keep the old code. Frames that a change touches must be deleted before re-rendering, because existing files are skipped.

## Things that bit

- **End camera too far:** at 36 km distance the edge of the board showed in the corners during the final fade. Keep the final camera inside the board, or extend the board.
- **Fonts used only on the end card** appeared as fallback glyphs until they were explicitly loaded before the first frame.
- **Callouts and the camera:** when narration names a place, the camera has to show it, with a callout. The user noticed when the line about gardens played over a frame without 拙政园 in it.
