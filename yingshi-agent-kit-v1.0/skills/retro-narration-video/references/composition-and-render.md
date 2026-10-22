# HyperFrames 合成与渲染

## 新建项目脚手架

优先用脚手架一键搭目录，替代手动复制已验收工程。脚手架默认复制动态纸墨 v2
项目壳与场景子合成；小样片可用兼容的单文件模板。

```powershell
python <skill>\scripts\new_project.py "20261005-丰田-第一集" [--brief "目标时长8分钟，5章"]
```

目录落在 config 的 projects_root 下，自动建好 `BRIEF.md`、`notes/`、`scripts/`、`audio/`、
`assets/illustrations/`、`compositions/`、`renders/`、`vertical_douyin/`、图集目录，并从
starter 模板复制 `index.html` 与场景子合成。要沿用某个已验收工程的具体排版时，再复制
该工程再改（结构范本参照
`Y:\Projects\自媒体\在外互助父母协议_试片`，风格范本参照日产 / 凯迪拉克工程）。

## 合成结构

生产长片使用「主壳 + 场景子合成」。`index.html` 只保留底板、音频和场景宿主：

```html
<div id="s03" data-composition-id="s03"
     data-composition-src="compositions/s03_evidence.html"
     data-start="12" data-duration="6" data-track-index="1"
     data-width="1920" data-height="1080"
     data-track-kind="graphics"></div>
```

场景文件的一切内容放在 `<template>` 内，根元素用 `#root` 选择器，宿主 id、场景根
`data-composition-id` 与 `window.__timelines["s03"]` 必须完全一致。单镜头 4–7 秒，
超过 8 秒必须拆分。镜头优先采用满幅图、分栏、局部特写、巨号数字和证据叠放；
`artplate` 居中画卡只能偶尔用于结论句。

规则（全部踩过）：

- 主壳 root 必须 `data-start="0"`；每个场景宿主同一 track 不能重叠。
- 场景文件必须包在 `<template>` 内；样式、脚本和标记都放模板内。根元素以 `#root`
  选择，不能使用类选择器。
- 定时视频保留 `class="clip"`、`muted playsinline`、`data-start/data-duration`。
  视频可以位于场景内部；不要同时给视频和它的时序父容器都设置时间窗。
- B-roll 空镜打底的层级、scrim 浓度、预循环烘焙、选片与节奏口径，见
  `visual-craft.md` 第 2、3 节，本文件只规定合成结构。
- 中文字体声明：`@font-face { font-family:"ChineseSans"; src: local("Microsoft YaHei"); }`
  KaiTi/SimSun 同理，否则 lint 报 font-family 未声明。
- 正文不要用 `<br>`；用 max-width 让文本自然换行。
- 背景纸纹用 `.bg::after` 叠加噪声，注意它会禁用 fast capture（渲染略慢，
  正常）。
- 每个场景注册自己的单一 paused timeline；主壳的 timeline 只保留空时间轴。不要将
  场景 timeline `add()` 到主时间轴。clip 生命周期由 HyperFrames 管理。
- 统一横向 current：出场向左 partial travel，入境从右侧接续；不要每场 fade-and-slide-up。

## 横屏工程

`index.html`：root `data-width="1920" data-height="1080"`，meta
`width=1920, height=1080`。

## 竖屏工程

简单单文件旧工程可用脚本生成兼容竖屏；动态纸墨 v2 必须使用原生 9:16 场景重排，
不得把 16:9 场景整体缩放后直接交付。原生竖屏场景从
`assets/starter_retro_v2_vertical/` 起步；`new_project.py` 会把它复制到
`vertical_douyin/`。

旧工程兼容转换：

```powershell
python <skill>/scripts/vertical_transform.py <项目目录>
```

脚本仅用于旧的一图一文静态模板：root/meta/body 改 1080×1920、字号缩放、宽容器
压到 950px、复制素材与音频。检测到 `.scene-shell` / B-roll 等多层镜头时默认拒绝，
避免把横屏构图机械裁成竖屏。浏览器打开竖屏页加 `?guide=1` 可显示抖音安全区参考线。
（顶部10% / 底部25% / 右侧10% 遮挡区），排版时把核心内容放进安全区。

在 `vertical_douyin/` 里 check 和 render，产物互不覆盖。

## 校验与渲染

本项目当前按 HyperFrames `0.8.185` 验证。不要依赖机器上可能残留的旧版
`npx hyperframes`（实测有环境会解析到 `0.7.94`）；统一显式使用：

```powershell
cd <横屏或竖屏项目目录>
npx --yes hyperframes@latest check --json --no-contrast   # 迭代期可跳过对比度
npx --yes hyperframes@latest check --json                  # 交付前跑含对比度
```

渲染：

```powershell
$env:TEMP='D:\workspace\tmp\hf_xxx'; $env:TMP=$env:TEMP
npx --yes hyperframes@latest render --output renders/main.mp4 --quality looks --gpu
```

- draft 先给用户看；`looks` 用于第一版真实出片，`delivery` 用于最终交付。
- check 报 `sweep_static` 时先确认 GSAP 数组里每个 scene 都登记了；不是只看
  `tl.from` 是否存在。
- 用 `--quiet` 时若秒退，先不加 quiet 重跑一次拿错误。

## 竖屏套图

成片后按每个 scene 的 `data-start + ~1.0s` 用 ffmpeg 抽 1080×1920 PNG：

```powershell
ffmpeg -y -ss <start+1.0> -i renders/main_9x16.mp4 -frames:v 1 -q:v 2 "<场景名>.png"
```

输出放 `<项目>/抖音竖屏图集_9x16/`。若还要抖音封面，单独做一张 9:16 标题封面，
不要拿普通场景帧冒充封面。

## 每次改口播后的连锁

改口播 → 重录受影响 Part → 重新拼接 → 重新转写 → **按新章节时长重排画面** →
重渲染。画面图没变时可以跳过 ⑤。
