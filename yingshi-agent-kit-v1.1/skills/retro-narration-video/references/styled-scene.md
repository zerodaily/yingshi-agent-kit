# 分层舞台（画风包合成规范）

v1.1 起，画面不再只有「一张配图 + 文字卡」一种形态。画风包包 A / 包 B 使用**分层舞台**：
一个画面由多个图层按时间轴逐件组装，替代 AI 视频模型的镜头动画。

## 什么时候用分层舞台

| 画面类型 | 用哪种 |
|---|---|
| 复古纸墨（包 0） | 沿用 `artplate` + 文字卡，不变 |
| 档案调查拼贴（包 A） | 分层舞台 |
| 设计拼贴（包 B） | 分层舞台 |
| 需要真实录像镜头的 | 本产线不做，走剪辑 |

## 分层舞台的固定结构

```html
<section class="clip" data-start="17.90" data-duration="11.31" data-track-index="1">
  <div class="stage" id="s3-stage">
    <div class="plate" id="s3-plate"></div>          <!-- 底纸 / 平色场 -->
    <img class="scrap" id="s3-scrapA" src="assets/elements/scrap_a.png" />
    <img class="cut hero" id="s3-hero" src="assets/elements/hero.png" />
    <div class="tape" id="s3-tapeA"></div>
    <div class="label" id="s3-label">1962</div>
  </div>
</section>
```

- `.clip` 必须是 root 直接子元素；`.stage` 是 clip 内部唯一的定位容器。
- 所有图层绝对定位，最终位置写在 CSS（`left/top/width`），**初始位移写在 GSAP 的 from 里**。
- 禁止给被 GSAP 补间的元素写 CSS `transform`（会触发 `gsap_css_transform_conflict`）。
- 图层 id 一律带场景前缀（`s3-`），保证全页唯一。

## 动效规则（画风包约束）

1. 入场一律 `steps(n)`，做出「裁切两帧」的定格手感；包 A 用 `steps(6–9)`，包 B 用 `steps(5–8)`。
2. 一件落位后不再移动；成型后只允许一次极缓推近（1.2%–1.4%）。
3 禁止 `repeat: -1`、循环漂浮、呼吸、发光脉冲（会被认定为"画面在等人"）。
4. 包 B 允许一次 `back.out(1.5)` 弹位；包 A 不使用任何回弹。
5. 节拍参考画风包的 `motion.yaml`，两件之间至少留 0.4 秒。

## 元素从哪来

1. 优先真实档案照片：Wikimedia Commons / Archive.org / Pexels，按 `elements/manifest.json` 记录出处与授权。
2. 用 `scripts/photo_to_cutout.py` 处理成半调剪影（参数见画风包 `STYLE.md`）。
3. 没有合适的真实照片时，才用画风包的 `prompts/still-prefix.txt` 出图，且**画面内文字仍然一律由 HTML 渲染**。

## 四个分层模板（随包交付）

| 模板 | 画风 | 画布 |
|---|---|---|
| `assets/starter_stage_archive_16x9.html` | 包 A 档案调查拼贴 | 1920×1080 / 14s |
| `assets/starter_stage_archive_9x16.html` | 包 A 竖屏派生 | 1080×1920 / 14s |
| `assets/starter_stage_design_9x16.html` | 包 B 设计拼贴 | 1080×1920 / 12s |
| `assets/starter_stage_design_16x9.html` | 包 B 横屏派生 | 1920×1080 / 12s |

模板放在项目根目录时，同目录必须有 `assets/vendor/gsap.min.js`（随包 71KB，本地引用，
不走 CDN，保证离线与可复现），以及模板里引用的元素 PNG。

**横竖屏之间不要整体缩放。** 分层舞台的坐标是绝对像素，两种画布要按坐标重排：
竖屏把主图下移、标签上移，核心内容压进抖音安全区（高度 15%–70%，底部 25% 空出）；
横屏把文字列放到色场一侧、照片群放到卡纸一侧。四个模板已经各自排好，改文案即可。

## 渲染与验收

> **分镜不要手写 HTML。** 场景写成 `film.json`，用 `scripts/build_film.py` 生成横竖两个工程，
> 结构与字段见 [film-json.md](film-json.md)。下方规则是生成器与手写模板共同遵守的底线。

### 实战校准（2026-10-07，捷豹一集 51.5 秒实拍）

样板里那套 10 秒逐件组装**不能直接用在成片上**——旁白 beat 只有 2.4–5.6 秒，
组装必须压到 1.2–2.0 秒：

- 元素间隔 0.09–0.26 秒（典型 0.22 秒），单件补间 0.32 秒，全场组装 1.2–2.0 秒；
- 5 秒以上的场景在 50% 处追加一个元素，避免后半段空转；
- 场景切换用**左出右进**（同轴同向），出场补间结束在 clip 边界时必须补
  `tl.set(sel, {visibility:"hidden"})` 硬杀，否则 lint 报 `gsap_exit_missing_hard_kill`；
- 12 个场景只用了 14 个元素，靠槽位复用——元素库是这么摊薄的。

### 长片校准（2026-10-07，162 场 / 10.6 分钟压力测试）

把捷豹分镜扩写成 162 场做了压力测试，暴露两个必须守的约束：

1. **单文件元素超过约 40 个"重叠加层"就有黑帧风险。** HyperFrames 把
   `filter: blur` / `radial-gradient` / `clip-path` 三类算作重叠加层，并且在
   `opacity:0` / `visibility:hidden` 状态下**也算数**。150 场 × 4 张图远超阈值。
   两条对策：① 元素投影烘进 PNG（`element_shadow: "baked"`），不再用 CSS
   `drop-shadow`；② 装饰件不要用径向渐变，图钉之类改用实色 + 内阴影。
2. **单文件时间轴会变密**（162 场 → `timeline_track_too_dense` 警告）。当前
   生成器仍输出单文件，可正常渲染；再往上到 200 场以上时，建议按章节拆成
   `compositions/chNN.html`，用 `data-composition-src` 挂载。

压力测试的验收口径：`lint` 0 error、无 `composition_heavy_overlay_count_high`、
相邻场景不同构图（生成器质检摘要里"相邻同构图"必须为 0）。

```powershell
npx hyperframes lint
npx hyperframes check --json --no-contrast      # 迭代期
npx hyperframes render --output renders/main.mp4 --quality draft --low-memory-mode --gpu
python scripts/qa_frames.py renders/main.mp4 renders   # 抽帧质检：抓黑帧、看信息量是否递增
```

验收看三条硬指标（见各画风包 `qc.md`）：

- 首帧是空底纸/纯色场，元素逐件进入，不是整体淡入；
- 逐秒抽帧平均亮度没有接近 0 的黑帧；
- 逐秒 std 从个位数一路升到 45+（包 A）/ 60+（包 B），说明画面在持续加信息。
