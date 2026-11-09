# story-mv · 剧情 MV

一个适用于 Claude Code 和 Codex 的 skill：给一首歌写一个原创故事，再用大量 AI 短片段把它拍出来。故事和分镜卡在歌的节拍网格上，首尾帧用 GPT Image 画，视频和 4K 超分通过 Sumi Studio MCP 调 Seedance 2.5 和超分模型，后期用 Python 和 ffmpeg 加胶片质感、抽帧、手持感和 Logo。歌词排版全程不让 agent 读歌词：工具运行时读用户的文件，只输出数字，审核看占位符版。最后出署名卡、封面、各平台文案和打包文件。

示例作品是猫猫 MV《HONG KONG》：两只茶馆的猫每晚守在九龙一个路口，等坐的士离开的她回来。4K，4 分 08 秒，69 个镜头，88 条 Seedance 片段，前后 15 版。故事、分镜、画风、提示词样例、调色参数和公开版制作总结都在 `example/hong-kong/`。

A Claude Code and Codex skill for music videos with an original story, built from many short AI clips: a story and storyboard on the song's beat grid, first and last frames with GPT Image, Seedance 2.5 clips and a 4K upscale through Sumi Studio MCP, a film-look finish with step print in Python and ffmpeg, lyric typography timed without the agent ever reading the lyrics, credit cards, a cover and a release package. The worked example is HONG KONG, a 4-minute cat music video.

## 目录 / Layout

```
SKILL.md          入口：五条约定、流程、脚本、Sumi 调用、经验 / entry point
references/       分步说明：故事和分镜、首尾帧和提示词、生成和超分、画风和后期、修复、歌词、署名和发布、审核、经验表
scripts/          通用脚本，每个都有合成素材测试（tests/test_scripts.py）
example/hong-kong/ 《HONG KONG》的故事、画风、色表、69 镜分镜、8 条提示词、调色参数、署名卡和制作总结
agents/openai.yaml Codex 的显示信息
LICENSE           MIT
```

## 安装 / Install

把整个 `story-mv/` 文件夹复制到 `~/.claude/skills/`（Claude Code）或 `~/.codex/skills/`（Codex），保留 `scripts/`、`references/` 和 `example/`。也可以把 `.skill` 包上传到支持该格式的 Claude 界面。然后说「用 story-mv 给这首歌拍一支 MV」，Codex 里也可以用 `$story-mv`。

Copy the complete folder into `~/.claude/skills/` (Claude Code) or `~/.codex/skills/` (Codex). A `.skill` archive is provided for Claude interfaces that accept skill uploads.

## 依赖 / Requirements

- Python 3.10+，`pip install -r scripts/requirements.txt`（numpy、opencv-python、Pillow）
- ffmpeg 和 ffprobe（带 libx264 和 prores_ks）
- `card_timing.py`、`share_pack.py`、`upscale_chunks.py` 和 `beat_grid.py snap` 只用标准库
- 封面抠图 `subject_mask.swift`：macOS 14 以上，`swiftc -O subject_mask.swift -o subject_mask`
- 歌词起音测试 `lyric_cut_test.py`：Apple silicon 加 `pip install mlx-whisper`，首次运行会下载模型
- 生成视频和超分：Sumi Studio MCP，花的是用户自己的积分。出图用 gpt-image 或任何能出图的模型

测试：`python3 tests/test_scripts.py`。测试只用运行时生成的合成画面和声音，缺 numpy、OpenCV 或 ffmpeg 的项目会跳过。设 `STORY_MV_ASR=1` 再跑一次，会加测 Whisper 起音（需要上面那套 Apple silicon 环境和 macOS 的 `say`）。

## 脚本速查 / Scripts

| 脚本 | 作用 |
|---|---|
| `beat_grid.py` | 测速度和第一拍；测重音落在网格前后多少（已校准）；把分镜的切点吸到拍子上并换算成帧 |
| `film_look.py` | 后期质感：调色、泛光、红色光晕、颗粒、柔光、曝光起伏、手持、12 帧抽帧（叠化或停帧）、Logo；可按镜头设参数，可分段并行 |
| `flow_ramp.py` | 单镜头变速抽帧，中间位置用光流补帧，速度渐变不顿 |
| `plate_repair.py` | 固定机位取中值净底板；把重画的底板合回每一帧，只保留原片的雨线 |
| `upscale_chunks.py` | 按镜头边界把粗剪切成超分分段，算预计积分和冻结积分，留帧号对照表 |
| `card_timing.py` | 按每秒 4 个词检查署名卡全亮时间够不够读 |
| `subject_mask.swift` | macOS Vision 抠主体，给封面用 |
| `title_cover.py` | 巨大压窄标题放在主体后面；报告标题、主体和 Logo 是否都在居中 4:3 范围内 |
| `share_pack.py` | 打包交付文件夹：文件名 NFC 加 UTF-8 标记，视频图片不压缩，支持超过 4 GB，写完校验 CRC |
| `lyric_cut_test.py` | 用 Whisper 从不同起点强制解码，找一个唱出来的词真正的起音 |

## 版权 / Rights

本 skill 的代码和文档以 MIT 许可证发布，全文见 [LICENSE](LICENSE)。MIT 只覆盖本文件夹里的文件。示例里提到的歌曲、歌词、采样录音和商标不在授权范围内，权利归各自的权利人所有。示例文件夹不含任何成片、片段、首尾帧、角色设定图、音乐、歌词、字体或 Logo。

Code and docs here are MIT licensed (see [LICENSE](LICENSE)); the license covers only the files in this folder. The song, lyrics, sampled recordings and trademarks named in the example belong to their owners and are not licensed by it. The example folder contains no film, clips, frames, character boards, music, lyrics, fonts or logos.
