---
name: retro-narration-video
description: >-
  End-to-end 言同学-style Chinese retro narrated knowledge videos: web research →
  script with hard formatting rules → local IndexTTS2 voice → per-scene retro
  illustrations (Z-Image-Turbo + Real-ESRGAN) → HyperFrames composition with an
  optional real B-roll background layer, Bilibili 1920×1080 long version and
  Douyin 1080×1920 short version → check/render → vertical stills. Use when a
  topic or script needs the approved 老报纸/纸墨 illustration style. In-line real
  B-roll loops are allowed as a motion background; this skill does NOT cover
  editing external finished footage, AI video-model motion graphics, or
  slide-only content without voiceover.
---

# Retro Narration Video（复古口播讲解视频）

把「选题或口播稿」做成一条复古纸墨风中文口播视频，同时产出 B 站长版横屏
1920×1080 与抖音短版竖屏 1080×1920。流程为「研究 → 文案 → 本地配音 → 本地出图
→ HyperFrames 合成」，不依赖 NotebookLM 出 PPT 或在线图片模型。

## 适用与不适用

- **适用**：言同学账号的知识 / 人物 / 社会话题口播；已有口播稿需要出片；把旧题材重做成
  「每个画面都有一张复古配图」的版本。允许在本产线内用真实 B-roll 空镜循环打底（见
  `references/visual-craft.md`）。
- **不适用**：外部成片剪辑；AI 视频模型生成的镜头动画；纯 PPT 幻灯片且无口播。

## 产线总览

```text
① 选题研究(web/笔记) → ② 口播稿(硬规则校验) → ③ IndexTTS2 分章配音
→ ④ 词级转写 → ⑤ Z-Image 批量出图 + Real-ESRGAN 放大
→ ⑥ HyperFrames 复古合成(横/竖, 可叠加 B-roll 空镜层)
→ ⑦ check + 渲染 → ⑧ 竖屏套图 / 发布物料
```

每个项目建议复制一个已验收工程再改（首例参照日产 / 凯迪拉克工程）。制作前把目标
时长与章节结构写进 BRIEF，先出封面确认，再写稿配音，不要先出图再改文案。

## 风格三选一（开工前在 BRIEF 定死，全片不混）

| 风格 | 适用 | 镜头基调 | 镜头语法 |
|---|---|---|---|
| 普通复古（默认） | 品牌历史长故事、人物传记，5–8 分钟 | 静态木刻画 + 极缓位移，舒缓 | `visual-craft.md` §6.1 |
| Vox 拼贴 | 硬核解释、反常识冷知识，3–5 分钟 | 固定机位桌面拼贴，2–3 秒一个事件 | `visual-craft.md` §6.2 |
| huashu 艺术动态 | 视觉冲击强、节奏快的实验内容 | 相机平滑 + 元素步进，硬切快推 | `visual-craft.md` §6.3 |

## 开工前必读（跑哪步读哪份，细节以下册为准）

- [references/script-rules.md](references/script-rules.md)：口播稿结构、开场结尾、
  数字标点、去 AI 味、钩子与涨粉、平台脚本差异、字数口径。
- [references/audio-pipeline.md](references/audio-pipeline.md)：IndexTTS2、拼接、
  转写、BGM 选曲、混音电平硬标准。
- [references/image-pipeline.md](references/image-pipeline.md)：Z-Image +
  Real-ESRGAN 本地出图、风格锁定、言同学 IP 唯一标准。
- [references/composition-and-render.md](references/composition-and-render.md)：
  HyperFrames 横/竖结构、校验、渲染、抽帧套图。
- [references/visual-craft.md](references/visual-craft.md)：镜头节奏口径、真实
  B-roll 空镜层、揭示动作、转场、三风格镜头语法（反 PPT 感唯一权威）。
- [references/cover-and-layout.md](references/cover-and-layout.md)：封面 4 模板、
  配色 token、IP 落位、静态卡片排版、反 AI 模板套路。
- [references/publish.md](references/publish.md)：B 站 Browser Use 发布步骤、
  发布说明模板、抖音物料、标题标签简介规范、草稿箱限制。

## 全局不可变硬规则（跨册，违反即返工；细则在对应分册）

1. **年份用「零」不用「〇」**：`二零二四`、`二零零六`；交 TTS 前对 chapters.json
   全局检查 `〇`。细则见 `script-rules.md` §3。
2. **口播正文禁止章节标题、Markdown 符号、括号、破折号**；章节头只用于视觉标题，
   绝不进 TTS。
3. 第 1 章 hook 后一字不差出现 `欢迎回来，我是言同学。`（全片仅一次）；结尾用固定句
   收尾。台词与固定句见 `script-rules.md` §2。
4. **文字不交给文生图**：AI 只画画面内容，所有文字由 HTML/CSS 叠在卡片上，保证字形清晰。
5. Z-Image 在 2080 Ti 上用 512×512、4 步；不得跑 768+ bf16 全精度；放大交给
   Real-ESRGAN。细则见 `image-pipeline.md`。
6. **每个画面必须有一张配图**，统一风格前缀与调色，禁止混入实拍、异风格图或纯文字页。
7. HyperFrames：文字元素 `class="clip"` 直挂 root；视频层不包进带 `data-start` 的
   section；中文字体必须 `@font-face src: local()` 声明。结构细则见
   `composition-and-render.md`。
8. 渲染用 `--quality draft --low-memory-mode --gpu`；TEMP/TMP 指到大盘
   （`D:\workspace\tmp\...`）；禁用 `--workers 2`。细则见 `composition-and-render.md`。
9. **时长下限**：B 站长版横屏必须 5–8 分钟，低于 4 分钟打回重做；5 分钟至少 18–22 个
   场景。口径唯一权威在 `visual-craft.md` §2 与 `script-rules.md` §1。
10. **音频电平**：人声是绝对主角（-6dB ~ -12dB），BGM 全程固定比人声低 12–15dB、
    平稳不跳变，禁止侧链闪避 / ducking。细则见 `audio-pipeline.md`「混音电平硬标准」。
11. **言同学 IP 全片一致**：标准定义唯一权威在 `image-pipeline.md`，封面落位与模板在
    `cover-and-layout.md`，其他位置不另写第二份描述。

## 工作流闸门

1. **封面先行确认**：新项目先出 6 个尺寸封面（1:1 / 16:9 / 9:16 / 4:3 / 3:4 / 4:5）
   连同口播稿交用户确认 IP 形象与标题排版；用户确认前禁止进入配音、出图、渲染，不白烧算力。
2. 确认后一口气走完：配音 → 选 BGM → 出图 → 合成 → 渲染草稿给用户看 → 确认后再出
   正式片头片尾与发布物料。
3. 发布走 `publish.md`：禁止 Playwright 脚本自动发 B 站（风控），用 Browser Use 操作
   用户自己的 Chrome，只存草稿，由用户最后发布。

## 交付产物结构

```text
<项目>/
├─ BRIEF.md / notes/研究笔记.md
├─ scripts/视频脚本_版本A.md + audio/chapters.json
├─ audio/Part1..N.wav + 口播拼接.wav + transcript.json
├─ assets/illustrations/*_2048.png
├─ index.html                        # 横屏合成
├─ vertical_douyin/index.html         # 竖屏工程（独立子目录）
├─ renders/*.mp4                     # 横屏 / 竖屏 / 60 秒引流片
├─ 抖音竖屏图集_9x16/*.png
└─ 发布说明.md
```
