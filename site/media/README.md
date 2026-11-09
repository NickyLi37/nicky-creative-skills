# Gallery media

These files are published as visual case-study previews. **They are excluded from the repository's MIT license.** Viewing a demo does not provide a license to redistribute its underlying source work, music, choreography, character designs or trademarks. No third-party rights are claimed by this repository.

## Thriller AI-character recast

- `thriller-ai-recast-preview.mp4`: the full 132.54-second AI-character dance recreation, 960×720, 24 fps, 4:3, silent, with the Sumi Studio watermark.
- `thriller-ai-recast.jpg`: a frame extracted from that generated film for its poster.
- Production: Nicky Li using Sumi Studio and the `sumi-mv-recast` workflow.
- Source inspiration/reference: Michael Jackson's *Thriller* music video. The original soundtrack and source-video file are not distributed here.
- Characters include a DeepSeek-inspired lead and other AI-character designs. Names identify the visual references; no endorsement or affiliation is implied.
- This preview was resized from the completed production master for browser delivery. It retains the complete selected sequence; it is not a new generation or the 4K master.

The preview and poster have no additional open-source media license. All applicable rights remain with their respective holders. To report a concern about a Gallery asset, contact the maintainer through this repository's GitHub profile or issue tracker.

## 人家尽枕河 / Homes Pillowed on the River

- `suzhou-preview.mp4`: the complete 257.916667-second film, 1920×1080, 24 fps, 16:9, H.264/AAC, with Mandarin narration, music, bilingual on-screen subtitles and the Sumi Studio watermark. This is the existing phone delivery, not a new render. The 4K master is not distributed here.
- `suzhou-poster.jpg`, `suzhou-history.jpg`, `suzhou-growth.jpg`: resized stills from final production frames 6100, 2300 and 5200. They retain the image and on-screen credits from those frames.
- `suzhou-subtitles.srt` and `suzhou-subtitles.vtt`: bilingual film transcripts; VTT is converted from the delivery SRT. The video's burned-in subtitles remain visible when the optional text track is off.
- Production: Nicky Li in collaboration with Claude. The city visuals are code-rendered in Three.js; narration (MiniMax TTS 2.8 HD) and music (Suno v6) were generated through Sumi Studio MCP.
- Form and pacing reference: [@EianLu's Chengdu city film](https://x.com/EianLu/status/2111662397278847478). Its source video is not included.

The following credits describe third-party inputs to the rendered work, not files bundled with the skill:

| Input | Source and terms | Changes in this film |
| --- | --- | --- |
| Building footprints, heights and ages | [CMAB](https://figshare.com/articles/dataset/CMAB-The_World_s_First_National-Scale_Multi-Attribute_Building_Dataset/27992417), Yecheng Zhang, Huimin Zhao and Ying Long, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Clipped, projected and extruded; some landmark heights overridden |
| Roads, water and landmark heights | [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL | Selected, simplified and rendered as map layers |
| Satellite imagery | Sentinel-2 cloudless 2016 by EOX IT Services GmbH, containing modified Copernicus Sentinel data 2016; [EOX source and licensing](https://cloudless.eox.at/documentation/faq), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Cropped and composited into the city board |
| Pingjiang stele reference photograph | [Siyuwj, 四大宋碑——平江图，2016-05-15](https://commons.wikimedia.org/wiki/File:%E5%9B%9B%E5%A4%A7%E5%AE%8B%E7%A2%91%E2%80%94%E2%80%94%E5%B9%B3%E6%B1%9F%E5%9B%BE%EF%BC%8C2016-05-15.jpg), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Used as a reference for tracing, georeferencing and illustrative historical layers; applicable attribution and ShareAlike terms remain in force |
| Historical rubbing photograph | [《亜細亜大観》第14册第036图〈平江之圖（蘇州）〉](https://commons.wikimedia.org/wiki/File:%E4%BA%9C%E7%B4%B0%E4%BA%9C%E5%A4%A7%E8%A6%B3_14_036_%22%E5%B9%B3%E6%B1%9F%E4%B9%8B%E5%9C%96_%EF%BC%88%E8%98%87%E5%B7%9E%EF%BC%89%22.jpg), Wikimedia Commons, public domain | Cropped and used in the historical-map transition |
| Fonts | Noto Sans/Serif CJK, Inter, Ma Shan Zheng, SIL OFL | Rendered text; font files are not bundled |

This release grants no additional blanket license to the combined film, generated audio or branding. Existing third-party permissions and obligations are unaffected. In particular, the code's MIT license does not replace CC BY, CC BY-SA or ODbL terms; any adaptation covered by ShareAlike retains those terms. See the [case study](../../docs/suzhou-case-study.md) for reconstruction and data limits.

## HONG KONG

- `hong-kong-preview.mp4`: the complete 248.166667-second film, 1280×720, 24 fps, 16:9, H.264, silent, with the Sumi Studio watermark. It was rendered for this Gallery by the same 4K finishing pipeline as the final version 15, with the lyric layer switched off, then encoded for the web. The opening and closing credit cards are kept. The song and the on-screen lyrics are left out because their rights belong to the song's owners. The 4K master with sound is not distributed here.
- `hong-kong-poster.jpg`: the approved 1920×1080 cover, unchanged: the title and the two cats from the Nathan Road shot.
- `hong-kong-tram.jpg`, `hong-kong-cabinet.jpg`: 1920×1080 stills from frames 720 and 1320 of that lyric-free render.
- Production: Nicky Li in collaboration with Claude. First and last frames were drawn with GPT Image 2.6; the clips were generated with Seedance 2.5 and upscaled to 4K through Sumi Studio MCP; the finish was made with Python, OpenCV and FFmpeg.
- Music: The Weeknd, *HONG KONG (feat. 王菲季候風)*, released 31 October 2026, which samples Faye Wong's *季候風 (Monsoon)*, 1993. This is a fan work, not affiliated with the artists or their labels. No recording, composition or lyric is distributed here.
- The cats 豆包 and 茶茶 are from 墙边茶馆 in Suzhou. The look is an homage to Wong Kar-wai's Hong Kong films. Its colour targets were measured from a [fan edit uploaded to YouTube by Schumann](https://www.youtube.com/watch?v=YxAZU4saD84); none of that video is included.

The preview, poster and stills have no additional open-source media license. All applicable rights remain with their respective holders. See the [case study](../../docs/hong-kong-case-study.md) for how the film was made and what was checked.
