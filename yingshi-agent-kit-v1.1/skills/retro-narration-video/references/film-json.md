# film.json 与 build_film.py（拼贴画风的分镜构建器）

拼贴画风不手写 HTML。分镜写成一份 `film.json`，用 `scripts/build_film.py`
生成横屏 / 竖屏两个 HyperFrames 工程。

```bash
python scripts/build_film.py film.json --orientation land --out index.html
python scripts/build_film.py film.json --orientation port --out vertical_douyin/index.html
```

## film.json 结构

```jsonc
{
  "audio": "口播混音.wav",
  "duration": 51.5,
  "canvas": { "land": [1920, 1080], "port": [1080, 1920] },
  "type":   { "land": { "big": 92, "small": 38, "cn": 42, "stamp_cn": 34, "stamp_en": 28 },
              "port": { "big": 70, "small": 30, "cn": 34, "stamp_cn": 26, "stamp_en": 22 } },
  "plate":  { "land": { "map": "assets/plate_uk_geo.jpg", "pos": "48% 46%", "opacity": 0.30 },
              "port": { "map": "assets/plate_uk_geo.jpg", "pos": "50% 42%", "opacity": 0.28 } },
  "slots": {
    "land": { "hero": {"x":0.30,"y":0.30,"w":0.46}, "scrap": {...}, "label1": {...}, "pinA": {...} },
    "port": { "hero": {"x":0.03,"y":0.34,"w":0.94}, "...": {} }
  },
  "scenes": [
    { "id": "s01", "start": 0.0, "duration": 4.56,
      "cast":  { "scrap": "scrap_uk_a", "hero": "ss_1933", "portrait": "founder_lyons" },
      "cast_late": { "mini": "ftype_2023" },
      "tape": ["tape0","tape1"], "string": ["pinA","pinB","pinC"],
      "label1": { "big": "1922", "small": "SWALLOW" },
      "label2": "斯旺与莱昂斯 · 伦敦创立", "stamp": "档案", "underline": true }
  ]
}
```

坐标全部用画布比例（0–1），所以同一份分镜能出横竖两版。`cast` 的键是槽位名，
值是 `assets/elements/<值>.png`。

## 槽位

| 槽位 | 用途 |
|---|---|
| `scrap` / `scrap2` | 撕边档案碎片（衬底） |
| `hero` / `hero_b` | 主图和次图 |
| `portrait` / `mini` | 人物剪影 / 小图 |
| `photo1` / `photo2` | 备用照片位 |
| `tape0` / `tape1` | 胶带（需要 `w` 和 `h`） |
| `label1` / `label2` | 年份标签条 / 中文标签条 |
| `stamp` | 橡皮章 |
| `pinA` / `pinB` / `pinC` | 红绳图钉（三个点从左到右） |

## 生成器做了什么

1. **底板全片共用**：旧纸 + 档案图 + 污渍 + 颗粒 + 暗角挂在 root 下，所有 clip 之上，
   场景之间只换拼贴元素，读起来像同一张桌子上不断摆新东西。
2. **自动排节拍**：组装步长 = `min(0.26, max(0.09, min(时长-0.8, 2.6) / (元素数-1)))`。
   旁白快的段落自动压紧，长的自动放松。
3. **长场景补第二波**：`cast_late` 的元素在场景 50% 处入场。
4. **左出右进**：每场主图结束前 0.24 秒向左滑出淡出，下一场从右侧滑入（同轴同向），
   并在 clip 边界补 `tl.set(..., {visibility:"hidden"})` 硬杀，避免 `gsap_exit_missing_hard_kill`。
5. **红绳自动连线**：按三个图钉坐标生成带下垂的二次贝塞尔路径，用 `scaleX` 从左往右拉出。

## 一句话

写分镜只填三样：**哪个元素进哪个槽位、标签写什么、场景几点开始几点结束**。
其余（定位、缓动、硬杀、红绳路径、横竖屏差异）由生成器负责。

## 长片模式（3000–5000 字，10–15 分钟）

实测语速 **5.43 字/秒**（14 集样本），所以：

| 字数 | 时长 | 4 秒/画面 | 6 秒/画面 |
|---|---|---|---|
| 3000 | 9.2 分钟 | 138 | 92 |
| 4000 | 12.3 分钟 | 184 | 123 |
| 5000 | 15.3 分钟 | 230 | 153 |

一个 150+ 画面的片子，靠"每场都手工设计"是做不完的，必须靠三件事摊薄：

### 1 变体轮换（`build_film.py` 自动做）

场景不给 `variant` 时，生成器按顺序轮换，且**保证相邻两场不同构图**：

| 变体 | 落点 | 适用 |
|---|---|---|
| `assembly` | 主图居中（hero1），碎片先落 | 默认叙事 |
| `reveal` | 主图偏上（hero2），主图先落 | 强调"揭示" |
| `wide` | 主图更宽（hero3） | 大场面、整车 |
| `left` | 主图靠左（hero_l） | 讲参数、配文字列 |
| `board` | 多元素 + 红绳 | 谱系、多条线索 |
| `document` | 无主图，碎片与印章为主 | 事件、公告、无实物可拍 |

构建完会打印质检摘要：变体分布、相邻同构图数（应为 0）、元素库用量排行。

### 2 章节卡

场景加 `"chapter"` 字段就渲染成章节卡（大编号 + 标题 + 红线）：

```json
{ "id": "c01", "start": 0.0, "duration": 3.0,
  "chapter": { "no": "01", "title": "为什么开不坏" } }
```

建议每 10–14 场插一张，10 分钟片约 8–12 张。

### 3 元素库复用

150 场不需要 150 个元素。实测捷豹一集：12 场用 14 个元素；扩到 162 场，
同一批 14 个元素各复用约 30 次仍然成立——因为变体改了落点，观众感知是"新画面"。

按领域维护库（见 `domains/README.md`），一个领域积累 40–80 个元素就能撑起一个系列。

### 长片必须烘阴影

`film.json` 里加 `"element_shadow": "baked"`，元素 PNG 在生成阶段就把投影烘进去。
原因：HyperFrames 对 `filter: drop-shadow` 这类"重叠加层"有数量阈值（约 40 个），
150 场 × 4 张图会远超阈值，存在捕捉出黑帧的风险。烘进图片后每个元素只剩一个 `<img>`。

## 镜头类型（v1.1 起，解决「镜头太单一」）

只换元素落点还是会单调——长片必须换**镜头语言**。`build_film.py` 在变体之上再加一层
`_layout`，按固定顺序轮换（不连续重复）：

| 镜头类型 | 画面构成 | 占比 |
|---|---|---|
| `stage` | 常规分层拼贴（前面的六种变体都在这一档里） | 约一半 |
| `fullbleed` | 主图放大到 1.26 倍画布出血，下半压一条撕边纸带 | 1/15 |
| `duo` | 左右双图对比，中间一条红色中缝 | 1/15 |
| `bignum` | 左侧巨号年份块 + 右侧主图 | 1/15 |
| `wall` | 4 张小图贴成一面照片墙 | 1/15 |
| `timeline` | 横向年份轴 + 轴上红色区间 + 两侧小图 | 1/15 |
| `quote` | 人物大幅 + 红色圈注 | 1/15 |

另有 **三种纸色轮换**（暖黄 / 浅米 / 灰），每场换一次，整片不再是同一张纸。

要改比例就改 `LAYOUT_ROTATION` 列表；要加新镜头类型，在 `LAYOUT_SLOTS` 里给一套槽位，
再在 `scene()` 的附加件分支里加它的装饰件（纸带 / 中缝 / 年表轴 / 巨数字 / 红圈）。

## 长片必须拆子合成

单文件到约 400KB、4000 个补间时，浏览器 10 秒内建不完时间轴，`check` 会报
`Navigation timeout`（渲染本身也许能过，但已经到极限）。用 `build_film_split.py`
按章拆开：

```bash
python scripts/build_film_split.py film.json --orientation land --chunk 20 \
    --out index.html --sub-dir compositions
```

宿主页只留底板与两条音轨（旁白 + BGM），场景分别落在 `compositions/ch01.html ...`。
子合成有三条硬规矩（踩错就静默黑屏，见 `/hyperframes-core` → `references/sub-compositions.md`）：

1. `<style>` / `<script>` / 主标记必须全在 `<template>` 里，放 `<head>` 会被丢掉；
2. 宿主槽位的 `data-composition-id` 必须等于子合成内部的 id，也等于
   `window.__timelines["<id>"]` 的键；
3. 根元素只能用 `#root` 选择器，用 class 会被 CSS 作用域丢掉。

另外子合成的时间轴是**从宿主槽位的 `data-start` 起算**，所以补间时间要整体减去该段起点
（`build_film.py` 里的 `base` / `tb()` 就是干这个的）。

## BGM：必须烘进音轨，不能靠播放器音量

实测这条片子的两个数：**旁白 -27.2 LUFS，BGM 素材 -15.9 LUFS**——音乐比人声响 11 LU。
播放器里给个 `volume="0.16"` 压不住，而且 mono→stereo 的等功率上混还会把口播整体压低 3 dB。

正确做法是 `scripts/mix_bgm.py`：按**响度**算增益，再做侧链闪避，输出单轨 `口播混音.wav`。

```bash
python scripts/mix_bgm.py <项目目录> --keep-below 10 --duck-ratio 4
```

链路：BGM 压到旁白之下 10 LU → 180Hz 高通 + 2.5kHz 衰减 3dB（让出人声清晰度带）
→ 以旁白为侧链做闪避（说话时再自动下沉约 4dB）→ 限幅 -1.5 dBTP → 与旁白相加，
输出单声道 44100（保持单声道是为了不因上混丢 3 dB）。

**默认值是这样定下来的**：先试 `--keep-below 18`，成片里音乐几乎听不见（用户反馈
「音乐没有了」）；改成 **13 LU + 4:1 闪避**后听得见但不抢口播。每集按素材密度在 **9–13** 之间微调。

这条片的实测结果：

| 指标 | 数值 |
|---|---|
| BGM 增益 | **-21.3 dB**（-15.9 → -37.2 LUFS） |
| 成片整体响度 | -27.3 LUFS（旁白 -27.2，只差 **0.10 LU**） |
| 旁白电平 | -28.401 → **-28.333 dB**（零损失） |
| 停顿处 BGM | -42.6 dB，比人声低 **14 dB**（清楚） |
| 说话时 BGM | 闪避后比人声低约 **21 dB**（不抢戏） |
| 真峰值 | -4.5 dBFS |

于是 `film.json` 里**不要再挂第二条 `bgm` 音轨**——`audio` 直接指向 `口播混音.wav`。
`bgm` 字段仍保留支持（`src` + `volume` + `loop`），只在需要运行时动态调音量时才用。

已经渲好的片子要换音轨不用重渲：`ffmpeg -i 成片.mp4 -i 口播混音.wav -map 0:v -map 1:a -c:v copy -c:a aac 新成片.mp4`。

