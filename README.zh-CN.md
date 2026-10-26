# Sumi Creative Skills

这是 Nicky Li 持续积累的创作技能库：把实际制作中有效的方法提炼成可复用 skill，并让使用者直接看到案例。

[打开 Gallery](https://nickyli37.github.io/sumi-creative-skills/) · [English](README.md) · [新增技能指南](CONTRIBUTING.md)

首个技能是 [sumi-mv-recast](skills/sumi-mv-recast/SKILL.md)：按选定段落复刻 MV，分开使用 Depth 动作参考、净场景、正式角色设定和首帧构图，再逐镜验收、局部修复、回配声音与等比例超分。

Gallery 已提供《Thriller》AI娘复刻的完整132.54秒无声网页预览，保留4:3和Sumi Studio水印。原声和4K母版未进入公开仓库。案例展示的是经过多轮制作与验收的结果，并不保证一次生成即可精准复刻。

## 分类方法

- **品类 Category**：作品用途，例如 Music video、Advertising、Short film、Product demo。
- **风格 Styles**：视觉呈现，例如 Anime、Cinematic、Photorealistic、Stop motion。
- 一个技能可以有多个风格和多个案例。Depth属于方法，不作为风格标签。

目录清单是 `site/catalog.json`，新增条目后，搜索、筛选和案例展示自动更新。当前只有一个已公开技能；不会把规划中的内容标成已完成。

## 使用

1. 在 [Sumi Skill Market](https://sumistudio.ai/en/skills/cmvowuj2x0pe6r50k12143t1a) 安装，然后输入 `/sumi-mv-recast`。
2. 提供选中段落、正式角色、已有Depth及预算/保真优先级。已有工程和授权可继续沿用。
3. 本地宿主可复制完整 `skills/sumi-mv-recast/` 目录。Python辅助脚本需要本地FFmpeg；在Sumi中保存脚本不代表运行环境一定能执行它。

扩展步骤和本地检查见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [英文README](README.md)。

原创技能文档与代码采用MIT许可；案例视频、海报及第三方音乐/MV/人物/商标不在MIT授权范围内。见 [媒体说明](site/media/README.md)。
