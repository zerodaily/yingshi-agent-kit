# HyperFrames 合成与渲染

## 合成结构

参照已验收的 `Y:\Projects\自媒体\在外互助父母协议_试片`。每个画面是一个
`section.clip`（直接挂 root），内部结构：

```html
<section id="s03-title" class="clip" data-start="17.903" data-duration="11.307" data-track-index="1">
  <div class="bg warm"></div>
  <div class="inner sans" id="s3-inner">
    <div class="artplate small"><img src="assets/illustrations/xxx_2048.png" /></div>
    <div class="title">…</div>
  </div>
</section>
```

规则（全部踩过）：

- root 必须 `data-start="0"`；每个画面同一 track 不能重叠。
- `.clip` 必须是 root 直接子元素；不要在它外面再包带时序的容器。
- 视频若存在：`muted playsinline`、自带 `data-start/duration`、直接放 root；
  不要包进带 `data-start` 的 section（会 frozen）。
- 中文字体声明：`@font-face { font-family:"ChineseSans"; src: local("Microsoft YaHei"); }`
  KaiTi/SimSun 同理，否则 lint 报 font-family 未声明。
- 正文不要用 `<br>`；用 max-width 让文本自然换行。
- 背景纸纹用 `.bg::after` 叠加噪声，注意它会禁用 fast capture（渲染略慢，
  正常）。
- 每个有内容的场景在 GSAP 卡片数组里登记：
  `["#s3-inner", 17.903]`，并在 `window.__timelines["main"]` 注册 paused timeline。

## 横屏工程

`index.html`：root `data-width="1920" data-height="1080"`，meta
`width=1920, height=1080`。

## 竖屏工程

不要直接改横屏工程；建独立子目录 `vertical_douyin/`：

1. 复制横屏 HTML 为 `vertical_douyin/index.html`；
2. 复制 `assets/illustrations` 与根目录 `口播拼接.wav`；
3. 文本变换要点（用脚本做，不要手改 20 处）：
   - root/meta/body 改为 `1080×1920`；
   - 所有 `font-size` 乘约 0.62；
   - 横向宽度容器（timeline/comment/grid4）压到 ~940–960px；
   - `inner` 横向 padding 压到 ~54px。

在 `vertical_douyin/` 里 check 和 render，产物互不覆盖。

## 校验与渲染

```powershell
cd <横屏或竖屏项目目录>
npx hyperframes check --json --no-contrast   # 迭代期可跳过对比度
npx hyperframes check --json                  # 交付前跑含对比度
```

渲染：

```powershell
$env:TEMP='D:\workspace\tmp\hf_xxx'; $env:TMP=$env:TEMP
npx hyperframes render --output renders/main.mp4 --quality draft --low-memory-mode --gpu --quiet
```

- draft 先给用户看；确认后再考虑 standard/high。
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
