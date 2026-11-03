# Storyboard, script and facts

## Study the reference before writing

If the user points at a reference film, measure it before you plan anything. Extract frames with `ffmpeg -i ref.mp4 -vf fps=2 ref_%04d.jpg`, check `ffprobe` for length and fps, and look at the spectrum for narration. Note down:

- length, fps and resolution (the Chengdu reference: 148.75 s, 24 fps, 1920×1080, score only, story told by subtitles)
- where the subtitles sit, the order of the languages, and where the chapter block, year ticker and scale bar are
- the material: board colour, building colour, water colour, depth of field, bloom, grain
- the cut rhythm: how long a chapter holds, which moves are cuts and which are eased

If the user's prompt is vague or technically wrong, rewrite it into a precise brief before building, and show them the diff. `example/suzhou/提示词_优化版.md` is a real example. Common corrections:

- recommend Three.js + headless capture, not scientific plotting tools
- make the frame number the only clock
- separate fact from illustration
- add checkpoints instead of "give me all the code"
- specify the HUD layout to the pixel

## One through-line

A city has too much history for four minutes. Pick one thread and bend every chapter to it. In Suzhou it was "homes and water" (人家 + 水), taken from the title poem, and each chapter shows what happened to the canals and the houses on them. Chapters in the example:

前史 · 水与稻 → 建城 → 苏州 · 运河 → 唐 · 桥 → 平江图 → 明清 · 繁华 → 战火 → 保护 → 两翼 → 高度 → 枕河 → end card

Each chapter gets one or two "big numbers" for its HUD card: 前514年, 390 桥, 1229年, 450 m, 2500+ 年. They give the viewer an anchor and the post a headline.

## The fact sheet

Every narrated line goes into a fact sheet with a source link and a check mark. `example/suzhou/方案.md` has the full sheet.

- **Say only what you can source.** If a claim is close, use the weaker word. 44 of 169 stele canals still match today's water within 70 m, so the line says 「不少」 ("many"), not 「大多」 ("most").
- **Check superlatives against the data.** "The old city's skyline belongs to the Song pagoda" was false, because a 151 m TV tower stands inside the old city. The line became the median height of old-city buildings plus the pagoda's height.
- **Label illustration on screen.** Where today's buildings stand in for an older city, or a historical map is schematic, a small HUD note says 示意 / illustrative.
- **Data fields have ranges.** CMAB's building-age field only covers about 1985–2018. Earlier periods cannot come from building ages; use thematic layers for them (walls, canals, gates, bridges, gardens).

## Sensitive history

Choose historical scope with the user's brief and intended audience. In the Suzhou project, the user omitted the 1958–1972 demolition of the city wall and filling of canals because of their publishing concerns. That was an editorial decision for this film, not a general rule. Its chapter became "protection": national historic city (1982), the 1986 master plan's "protect the old city's appearance in full", restored streets, and repaired gates with their years. Other projects may cover those episodes with sourced, neutral narration.

## Copy

- Use bilingual subtitles: Chinese on top, English below, the English a faithful plain translation.
- Write narration for the ear. Use one idea per line, with numbers as the TTS should read them (一二二九年) in the TTS script and as digits (1229年) in the subtitles.
- No slogan rhythm. Avoid symmetric pairs like 「A没了，B还在」, 「不是X而是Y」, 「从…到…，从…到…」. Users hear them as machine-written. State the fact plainly.
- Quote poems exactly, with poet and title on screen.
- Give subtitles 3 frames of lead before the voice and hold them 14 frames after it, never overlapping the next line.

## Budget the timeline in story frames

Author the picture on a fixed story timeline before the narration exists. Suzhou used 3,960 frames = 165 s at 24 fps. For each line, reserve a slot in story frames where its picture plays; `plan_warp.py` later stretches the slots to the voice. Chapter starts are story frames too. Leave each chapter turn a beat of pause: `plan_warp.py` adds 40 film frames there by default.
