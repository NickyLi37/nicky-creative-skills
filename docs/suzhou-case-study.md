# 《人家尽枕河》 / Homes Pillowed on the River

[观看作品](https://nickyli37.github.io/nicky-creative-skills/projects/suzhou.html) · [white-model-city-film Skill](../skills/white-model-city-film/README.md) · [完整制作总结](../skills/white-model-city-film/example/suzhou/制作总结.md)

Nicky Li 与 Claude 于 2026 年 11 月 2–3 日完成的苏州城市纪录短片。影片以人家与水为线索，从约六千年前的稻田讲到 2025 年。画面由真实地理数据和 Three.js 代码逐帧渲染；旁白和配乐由 Claude 通过 Sumi Studio MCP 生成。片名取自杜荀鹤《送人游吴》：“君到姑苏见，人家尽枕河。”

The film combines a code-rendered city model with AI narration and music. Its reusable workflow is published as `white-model-city-film`, with production references, general-purpose helpers and the Suzhou example source.

## 作品规格

| 项目 | 已交付作品 |
| --- | --- |
| 时长 | 257.916667 秒，约 4 分 18 秒 |
| 母版 | 3840 × 2160，24 fps，6,190 帧，16:9 |
| 网页预览 | 1920 × 1080，完整旁白与配乐，约 30 MB |
| 地图范围 | 32 × 21 公里 |
| 建筑 | 92,681 栋，其中古城内 7,031 栋 |
| 旁白 | 38 句，中英双语字幕 |
| 旁白 / 配乐 | MiniMax TTS 2.8 HD / Suno v6，通过 Sumi Studio MCP |

原项目记录五轮修改合计约 147 Sumi 积分，包含未采用的旁白与配乐。该数字是本片的历史制作记录，不是其他城市、当前模型或账户的报价。

## 可复用的制作方法

1. **用事实约束叙事。** 先确定故事线与逐句事实表，再整理建筑、道路、水系和历史图像。无法由数据支持的历史表现标注为示意。
2. **用帧号控制画面。** `window.renderFrame(f)` 根据帧号决定相机、图层和字幕状态。渲染可以并行、断点续跑，也可以局部返修。
3. **分开故事时间与成片时间。** 相机和图层编排在固定故事帧上，旁白以原速排布，再通过平滑映射连接两条时间轴。
4. **用停顿对齐音乐。** 本片采用一首连续配乐，从第 0 帧开始；调整句间停顿，让战火、保护和现代天际线分别落在合适的音乐段落。
5. **逐项验收。** 原项目使用逐句 ASR、年份对照、帧间跳变扫描、音高与响度检查、联系表，以及最后一秒的画面复查。

五轮修改中，1.2 倍速旁白改为原速；建筑从整批显现改为逐栋生长；混音从整体压低音乐改为按需压低人声频段；结尾诗句回到与整片一致的旁白参数；片尾淡出露出的地图边缘被修正。

## 开源范围与重建条件

开源包包括 Skill 指令、分步参考、通用辅助脚本，以及苏州案例的 Python / JavaScript 源码、方案、字幕与制作总结。原创代码和文档采用 MIT 许可。

重建时仍需自行准备 CMAB / OpenStreetMap 数据、历史图像、字体、旁白音频、配乐和所需品牌素材。仓库提供网页预览，未包含 4K 母版及其生产数据。安装与输入重建步骤见 [Skill README](../skills/white-model-city-film/README.md) 和 [苏州示例 README](../skills/white-model-city-film/example/suzhou/README.md)。

Node.js、Python、Chrome 和 FFmpeg 支持渲染及编码；Sumi MCP 生成使用操作者自己的积分。原项目的 mlx-whisper 语音识别检查依赖 Apple silicon，其他平台需选择可用的识别方式。

## 数据表达的边界

- CMAB 建筑年代来自遥感推断，并不提供精确到吴、唐、宋、明清的逐栋建造史。1985 年以前的建筑生长是叙事示意，历史信息通过城墙、河道、桥和园林等专题图层表达。
- 原项目发现 CMAB 超高层高度不足，因而使用 OpenStreetMap 的地标高度修正。这是苏州案例的处理方式，不应假定每个数据集都有相同问题。
- 制作记录中的“44 / 169 段平江图河道距当代水道不足 70 米”来自本片的描线与配准方法，不是历史地图精度的普遍结论。
- 网页预览是压缩展示版本。原项目记录的技术检查不等同于其他城市、平台或重新生成音频的验收结果。

## 署名与素材许可

- 形式与节奏参考 [@EianLu 的成都城市短片](https://x.com/EianLu/status/2111662397278847478)。
- 建筑：[CMAB — Zhang, Zhao & Long](https://figshare.com/articles/dataset/CMAB-The_World_s_First_National-Scale_Multi-Attribute_Building_Dataset/27992417)，CC BY 4.0。
- 道路、水系、城墙遗存与部分地标高度：[© OpenStreetMap contributors](https://www.openstreetmap.org/copyright)，ODbL。
- 卫星底图：[Sentinel-2 cloudless 2016 by EOX](https://cloudless.eox.at/documentation/faq)，CC BY 4.0，含修改过的 Copernicus Sentinel 数据。
- 平江图示意重绘：描线参考 Siyuwj 的平江图照片 / Wikimedia Commons，CC BY-SA 4.0。拓片照片来自《亜細亜大観》第 14 辑，公有领域。
- 字体：Noto Sans/Serif CJK、Inter、Ma Shan Zheng，SIL OFL。

影片、剧照、音乐、旁白、品牌标识及第三方素材不受代码的 MIT 许可覆盖。参阅 [媒体使用说明](../site/media/README.md)；复用第三方素材时，其许可与署名要求继续适用。
