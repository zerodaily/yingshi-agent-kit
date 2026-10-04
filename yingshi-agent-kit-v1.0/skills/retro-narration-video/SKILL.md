---
name: retro-narration-video
description: >-
  Make 言同学-style Chinese retro narrated videos (口播讲解视频) end to end:
  web research → 口播稿 with hard formatting rules → local IndexTTS2 voice →
  per-scene retro illustrations generated locally by Z-Image-Turbo and upscaled
  with Real-ESRGAN → HyperFrames composition (1920x1080 and/or 1080x1920
  抖音竖屏) → check/render → 竖屏套图. Replaces the old NotebookLM+PPT
  workflow; use when a topic/口播稿 is provided for a narrated knowledge or
  story video and the visuals should be the approved 老报纸/纸墨 illustration
  style. Not for live-action footage edits or AI video-model motion graphics.
---

# Retro Narration Video（复古口播讲解视频）

把「选题或口播稿」做成一条复古纸墨风的中文口播视频，可同时产出横屏 1920×1080
与抖音竖屏 1080×1920 两个版本。本流程不再依赖 NotebookLM 出 PPT 或在线图片
模型：画面统一用「研究 → 文案 → 本地配音 → 本地出图 → HyperFrames 合成」。

## 适用与不适用

- 适用：言同学等账号的知识/人物/社会话题口播；已有口播稿需要出片；把旧流程
  的题材重做成“每一画面都有一张复古配图”的版本。
- 不适用：需要真实拍摄/既有录像素材剪辑；需要 AI 视频模型做镜头动画；纯 PPT
  幻灯片且无口播。

## 产线总览

```text
① 选题研究(web/笔记) → ② 口播稿(硬规则校验) → ③ IndexTTS2 分章配音
→ ④ 词级转写 → ⑤ Z-Image 批量出图 + Real-ESRGAN 放大
→ ⑥ HyperFrames 复古合成(横/竖) → ⑦ check+渲染 → ⑧ 竖屏套图/交付
```

## 开工前必读

- 每个项目建议复制一个已验收工程再改（首例参照
  `Y:\Projects\自媒体\在外互助父母协议_试片`）。
- 环境硬性依赖见对应参考，跑哪步前读哪份：
  - [references/script-rules.md](references/script-rules.md)：口播稿格式、年份、
    去 AI 味与硬校验。
  - [references/audio-pipeline.md](references/audio-pipeline.md)：IndexTTS2、
    拼接、转写。
  - [references/image-pipeline.md](references/image-pipeline.md)：Z-Image +
    Real-ESRGAN 本地出图。
  - [references/composition-and-render.md](references/composition-and-render.md)：
    HyperFrames 横/竖排版、校验、渲染、抽帧。
- 制作前把目标时长与章节结构写进 BRIEF，再写口播稿；不要先出图再改文案。

## 关键规则（踩过坑，勿跳）

1. 年份一律用「零」不用「〇」：`二〇二四` 会让 TTS 读错，写成 `二零二四`、
   `二零零六`。生成后必须对 chapters.json 全局检查 `〇`。
2. 口播稿正文禁止出现章节标题、Markdown 符号、括号与破折号；正文里的章节头
   只用于视觉标题，绝不能进 TTS。
3. 第 1 章 hook 后必须一字不差出现：
   `欢迎回来，我是言同学。`
   结尾必须一字不差以固定句收尾（见 script-rules）。
4. 文字/排版页不得交文生图模型渲染：AI 只画“画面内容”，文字全部由 HTML/CSS
   叠在卡片上，保证字形清晰。
5. 本地 Z-Image 在 2080 Ti 上用 512×512、4 步；单张约 20–50 秒。不得直接跑
   768+ bf16 全精度（实测单张 >20 分钟）。放大交给 Real-ESRGAN。
6. 每个画面必须有一张配图；配图统一套用同一风格前缀与同一调色，禁止混入
   实拍、异风格图片或纯文字页。
7. HyperFrames：文字元素用 `class="clip"` 直挂 root；不要给视频包一层带
   `data-start` 的容器；中文字体必须用 `@font-face src: local()` 声明。
8. 渲染用 `--quality draft --low-memory-mode --gpu`，TEMP/TMP 指到大盘
   （如 `D:\workspace\tmp\...`），避免 C 盘爆盘。

## 每个画面的版式约定

- 米黄旧纸底（`#f2e8d3` 系）+ 颗粒纹理 + 双线/朱红点缀；大标题楷体（KaiTi）、
  正文宋体（SimSun）。
- 内容结构：上方一张 `artplate` 配图（朱红木框画卡），下方 HTML 文字。
- 一段 5 分钟口播约 20 个画面；若时长更长，按 2–3 秒/画面节奏扩张，不要复用
  同一张图做相邻两个画面。

## 交付产物

项目目录建议：

```text
<项目>/
├─ BRIEF.md / notes/研究笔记.md
├─ scripts/视频脚本_版本A.md + audio/chapters.json
├─ audio/Part1..5.wav + 口播拼接.wav + transcript.json
├─ assets/illustrations/*_2048.png
├─ index.html               # 横屏合成
├─ vertical_douyin/index.html  # 竖屏工程（独立子目录，见 composition 参考）
├─ renders/*.mp4
└─ 抖音竖屏图集_9x16/*.png
```

最终先渲染一版草稿给用户看，确认后再生效片头/片尾与发布物料。
