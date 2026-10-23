# 未整合风格参考

> 本文件只登记候选风格来源，**不接入现有硬视产线**。当前默认风格、选图、合成和
> 渲染规则仍以 `SKILL.md`、`visual-craft.md` 和 `cover-and-layout.md` 为准。

## MG Styles 15

- 地址：https://vincentwei1021.github.io/mg-styles-15/?lang=zh
- 页面数据：`site/data.js`，包含 15 支样片的名称、slug、说明、提示词和源码清单。
- 状态：参考库，待筛选；尚未进入硬视工作流。
- 收录日期：2026-10-23

项目收录 15 支约 10 秒的动态设计样片。每支样片都附成片、风格说明、完整提示词和源码。
页面说明显示，画面、动画、配乐和音效均由 AI 根据提示词写代码生成；技术路线包括 HTML、
Canvas、SVG、Three.js 和 Blender，渲染流程通常是无头 Chrome 逐帧截图后再用 ffmpeg
合成音视频。

## 已收录风格

| 编号 | 中文名 | 英文名 | 页面 slug |
|---:|---|---|---|
| 1 | 逐帧手绘 | Frame-by-Frame | `05-cel-boil` |
| 2 | 等轴 2.5D | Isometric 2.5D | `03-isometric` |
| 3 | 扁平矢量 | Flat Vector | `01-flat-vector` |
| 4 | 线条动画 | Line Art | `02-line-art` |
| 5 | 3D 渲染 | 3D Render | `04-3d-render` |
| 6 | 形变动画 | Shape Morph | `08-morph` |
| 7 | 贴纸风科普 | Sticker Explainer | `19-paperclip` |
| 8 | 赛博朋克 HUD | Cyberpunk HUD | `22-hud` |
| 9 | 拼贴剪贴 | Collage | `06-collage` |
| 10 | 弥散渐变玻璃拟态 | Aurora & Glassmorphism | `12-aurora-glass` |
| 11 | 几何构成包豪斯 | Geometric Bauhaus | `09-bauhaus` |
| 12 | 复古 Synthwave | 80s Synthwave | `10-synthwave` |
| 13 | 像素风 | Pixel Art | `20-pixel` |
| 14 | 液态流动 | Liquid Motion | `07-liquid` |
| 15 | 综艺花字 | Variety Captions | `18-hanazi` |

## 为什么先登记但不整合

- 现有硬视主片已有明确的镜头节奏、封面和发布规范。直接混入 15 种动态风格会破坏系列
  的视觉连续性。
- 这些项目的核心是“代码生成画面、动画和声音”，与当前以 Z-Image、真实 B-roll 和
  HyperFrames 为主的制作方式不同，需要单独设计适配边界。
- 后续若要扩展，应一次选定一种风格，先做独立样片验证，再把该风格写成正式候选，
  不应把所有风格塞进同一个主片。

## 后续筛选时的最低检查项

1. 是否能稳定用于 16:9 长片，而不只是 10 秒横屏短片。
2. 是否能输出原生 9:16，不需要把横屏机械裁切。
3. 是否兼容中文标题和言同学固定 IP，并且不依赖照片或品牌素材。
4. 是否有确定性的逐帧渲染路径，能接入 HyperFrames 或独立渲染器。
5. 是否有清晰的商用许可、字体许可、音频许可和可追溯源码。

本文件不是执行指令。除非用户明确要求研究或接入某种新风格，否则制作硬视视频时不要读取
或引用这里的具体风格。
