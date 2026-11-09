# 《HONG KONG》画风规范 v1

走九十年代港片的路子，主要参考王家卫和杜可风那一路的影像。学它的颜色、构图和动感，不搬具体镜头。色彩基准是用户指定的那支 YouTube 粉丝剪辑（Schumann 上传，视频 ID YxAZU4saD84），片中音频也取自这一版。

## 实测基准

从这支粉丝剪辑里取 12 帧测得：

| 项目 | 数值 |
|---|---|
| 平均亮度 | 0.26，画面大部分压在中灰以下 |
| 平均饱和度 | 0.48 |
| 暗部 RGB | 26, 28, 20，偏绿 |
| 中间调 RGB | 100, 107, 97，偏绿 |
| 高光 RGB | 199, 207, 184，偏黄绿 |
| 色相占比 | 红橙 28%，青绿 42%，其余很少 |

## 画面规则

1. **暗。** 大面积压黑，只留几块有颜色的光。
2. **两种颜色。** 荧光灯的青绿和霓虹的血红。黄色只给钠灯、烟花、金铺和她的丝巾。
3. **前景挡一块。** 隔着栏杆、湿玻璃、塑料门帘、水袋、雨伞边拍，前景虚掉，挡住画面的一部分。
4. **主体偏到边上。** 落在 38% 或 62% 线外侧，另一边留大块暗部。
5. **广角贴近。** 特写用广角贴近，脸和猫都不放在画面正中。
6. **浅景深。** 背景化成色块和光斑，招牌的字因此读不出来。
7. **湿。** 地面永远是湿的，颜色从地上反回来。

## 动感

- 提示词里仍写真实速度。Seedance 不写慢动作。
- 抽帧拖影全部后期做：人潮、奔跑、弥敦道这类镜头按 12 帧抽帧，相邻帧叠化，主体保持清楚。
  - 后来的修正（第八版盲审）：走动和奔跑的主体抽帧时不叠化，一帧停两帧，否则猫走近时读成双眼。叠化只留给主体几乎不动的镜头。
- 手持感后期加，幅度很小。

## 分段颜色

| 段落 | 颜色 |
|---|---|
| 序 | 雨夜青绿，招牌的红打在窗台上 |
| 繁华 | 红、琥珀、玉绿，全片最饱和 |
| 副歌一的回忆 | 屋里的窗光，偏暖偏白，颗粒更粗 |
| 副歌一的现在 | 青绿 |
| 间奏 | 蓝调时分的灰青 |
| 主歌二 | 白色 LED 打在青绿的夜里，饱和度压低 |
| 重逢 | 青绿的雨夜，红风衣是画面里最亮的颜色 |
| 尾声 | 青绿转清晨灰蓝，屋里的灯偏暖 |

## 后期流程

片段先转 BT.709，再走 `scripts/film_look.py`：暗部压绿，高光偏黄绿，红色加光晕，加胶片颗粒和轻微暗角。

## 出图和视频用的描述

提示词不写真人和导演的名字，只写画面特征。出首尾帧时每条提示词都带这一段：

> THE LOOK: a still from a mid-1990s Hong Kong art-house film, shot on fast 35 mm colour negative with a wide lens held close to the subject. Low-key and very dark: most of the frame sits well below mid-grey, with a few pools of coloured light. The shadows are inky with a green cast. Two colours own the frame: acid teal-green from fluorescent tubes and blood-red from neon. Highlights bloom and smear softly. The wet ground throws the colours back up. The subject is pushed towards one side of the frame, with dark empty space on the other side. A dark out-of-focus foreground object covers part of the frame. Very shallow focus, so the background melts into colour shapes and soft discs of light and no writing can be read. Real location, real rain, real fur. A photograph, not CG, not an illustration. Clean image with no film grain, no text overlay, no watermark.

两只猫的固定描述：

> 豆包：cream British Shorthair, round heavy face, stern amber eyes, thin red neck loop with a silver charm
>
> 茶茶：long-haired blue-grey cat, yellow eyes, white bib and four white paws, narrow cream cloth collar
>
> They are ordinary real cats at real cat size. Each cat has exactly four legs and two ears. Copy their faces, fur and costumes exactly from the boards.

首尾帧是干净的，不带颗粒。颗粒、光晕和抽帧都在后期加（`scripts/film_look.py`，参数在 `finish_spec.json`），否则视频模型会把颗粒拍成闪烁。
