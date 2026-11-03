# white-model-city-film · 城市白模纪录短片

一个适用于 Claude Code 和 Codex 的 skill：用代码做城市白模纪录短片。真实建筑数据拉成白模，Three.js 在无头 Chrome 里逐帧渲染，叠上古地图、城墙、河道等历史图层和中英双语字幕。旁白和配乐通过 Sumi Studio MCP 生成，对齐、混音后编码成 4K。

示例作品是苏州短片《人家尽枕河》：4K，4 分 18 秒，92,681 栋建筑，从约 6000 年前的稻田讲到 2025 年，38 句旁白。完整代码在 `example/suzhou/`，制作过程见 `example/suzhou/制作总结.md`。形式参考了 @EianLu 的成都城市短片，在此致谢。

A skill for Claude Code and Codex for making data-driven "white model" city documentaries entirely in code: real building footprints and heights extruded in Three.js, rendered frame by frame in headless Chrome, with historical map layers, bilingual subtitles, AI narration and score (Sumi Studio MCP), audio alignment, mixing and 4K encoding. The worked example is a 4-minute film about Suzhou.

## 目录 / Layout

```
SKILL.md          入口：流程、约定、经验 / entry point for Claude
references/       分步说明：选题与事实、数据、渲染、旁白配乐混音、质检交付、五轮修改的经验
scripts/          通用脚本（排时、旁白轨、混音、字幕和截图五个脚本在苏州项目上跑过，输出与原项目一致）
example/suzhou/   《人家尽枕河》的全部代码、方案文档和字幕（不含数据、音频、字体、品牌素材）
LICENSE           MIT
```

## 安装 / Install

将整个 `white-model-city-film/` 文件夹复制到 `~/.claude/skills/`（Claude Code）或 `~/.codex/skills/`（Codex），保留 `scripts/`、`references/` 和 `example/`。也可将 `.skill` 包上传到支持该格式的 Claude 界面。然后提出「给某某城市做一条白模城市短片」，Codex 中也可明确使用 `$white-model-city-film`。

Copy the complete folder into `~/.claude/skills/` (Claude Code) or `~/.codex/skills/` (Codex). A `.skill` archive is also provided for Claude interfaces that support skill upload.

## 依赖 / Requirements

- Node 18+，Google Chrome，`cd scripts && npm i`（playwright-core）
- Python 3.11+，`pip install -r scripts/requirements.txt`
- ffmpeg（带 libx264；使用 x265 导出还需 libx265）、ffprobe、zsh、bc；编码脚本固定为 24 fps
- 旁白和配乐：Sumi Studio MCP（花费用户自己的积分）。也可以换成任何能出 wav 的 TTS 和音乐模型。
- 质检里的逐句语音识别用 mlx-whisper（macOS / Apple silicon，依赖文件仅在该平台安装）。其他平台需替换 ASR 检查，其余流程不依赖 MLX。

示例不包含地理数据、音频、字体和品牌素材，不能直接一键渲染；请先按 [苏州示例说明](example/suzhou/README.md) 重建输入。服务仅监听本机，启动根目录应设为作品目录。

本地服务器回归检查：`node --test scripts/server.test.mjs`。测试覆盖正常文件、编码目录穿越、符号链接越界和无效 URL，不会调用生成服务。

## 脚本速查 / Scripts

| 脚本 | 作用 |
|---|---|
| `plan_warp.py` | 按旁白原速排句，生成成片帧到故事帧的平滑映射 |
| `align_extras.py` | 算出句间要加多长停顿，才能把指定句子对到配乐的指定秒数 |
| `capture.mjs` | 逐帧截图，可断点续渲，多进程并行，任意倍率（0.5 = 540p，2 = 4K） |
| `build_vo.mjs` / `mix_duck.py` | 拼旁白轨 / 只在人声频段按需压低配乐的混音 |
| `make_srt.mjs` | 中英双语 SRT |
| `encode.sh` / `encode_phone.sh` | 4K 母版 / 限定体积的手机版 |
| `music_profile.py` | 配乐的响度和明暗曲线，用来选曲和对段落 |
| `qa_*.py`, `qa_years.mjs`, `contact_sheet.py` | 质检 |

## 数据与版权 / Data and credits

本仓库不含任何数据。用这个流程做片时，请在片尾和发布文案里写明数据来源：

- 建筑：CMAB（Zhang, Zhao & Long），CC BY 4.0
- 道路水系：© OpenStreetMap contributors，ODbL
- 卫星底图：Sentinel-2 cloudless 2016 by EOX，CC BY 4.0
- 历史图像按各自的许可署名（苏州示例：描线参考 [Siyuwj 拍摄的平江图照片](https://commons.wikimedia.org/wiki/File:%E5%9B%9B%E5%A4%A7%E5%AE%8B%E7%A2%91%E2%80%94%E2%80%94%E5%B9%B3%E6%B1%9F%E5%9B%BE%EF%BC%8C2016-05-15.jpg)，Wikimedia Commons，CC BY-SA 4.0；拓片照片《亜細亜大観》公有领域）
- 字体：Noto Sans/Serif CJK、Inter、Ma Shan Zheng，均为 SIL OFL，请自行下载放到 `render/fonts/`

## License

本仓库的代码和文档以 MIT 许可证发布，全文见 [LICENSE](LICENSE)。MIT 只覆盖本仓库里的文件。用这个流程做片时用到的数据、历史图像和字体，仍按上面「数据与版权」里各自的许可证使用和署名。

Code and docs in this repository are released under the MIT License (see [LICENSE](LICENSE)). It covers only the files in this repository; the data, historical images and fonts a film uses keep their own licenses listed above.
