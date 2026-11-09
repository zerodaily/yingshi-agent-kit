# 风格 B 模板 · 人文纪录片（纸面 2D · 锚词法 · 音乐驱动）

规则原文见 `references/style-library.md` §B。本目录是可运行骨架，**不是成品片**。

## 三步出片

```powershell
# 1. 改 film.html 顶部 CONFIG：锚词 / 术语 / 字幕表 / 高潮秒 / 片长
# 2. 逐帧渲染（约 1 秒/帧，20 秒片约 10 分钟）
python render.py

# 3. 合成（BGM + 17 秒冲击音）
powershell -ExecutionPolicy Bypass -File build.ps1 -Bgm "D:\music\千年之后.wav" -Beat 17.0
```

## 硬规矩（踩过的）

1. **锚词先定，再写文案**。2–4 个字，是普通人的处境，不是术语。
2. **高潮秒必须实测**。`Beat` 在 `film.html` 与 `build.ps1` 两处要一致；换曲先用 ffmpeg 测「换气 + 重拍」，误差 ≤2 帧。
3. **纯帧号驱动**。`setState(t)` 里不许有累加变量，否则局部重渲（`--from/--to`）接缝会闪。
4. **地面线之类贯穿元素，要在高潮前收掉**，否则会横切术语大字。
5. **字幕 ≤18 字**，中英双行，暗背景反白；每句 3–5 秒。
6. **高潮那一帧锚词直接满不透明**，不要淡入——淡入会把「砸」变成「浮」。

## 局部返修

只改高潮段就不用整片重出：

```powershell
python render.py --from 480 --to 600
powershell -ExecutionPolicy Bypass -File build.ps1 -Bgm "..."
```

## 环境

- `playwright` 装在 Python 3.10（`C:\Users\jonny\AppData\Local\Programs\Python\Python310\python.exe`），PATH 上的 python 3.13 没有。
- playwright 自带 chromium 可能没下载，`render.py` 会自动找系统 Chrome / Edge；也可 `--chrome` 或 `set YINGSHI_CHROME`。
- ffmpeg 需在 PATH。

## 换主题要改的地方

| 位置 | 改什么 |
|---|---|
| `film.html` CONFIG | 锚词、术语中英、字幕表、`beat`、`total` |
| `film.html` setState | 三幕画面元素（跑者 / 追逐 / 人群 → 换成新主题的意象） |
| `build.ps1 -Bgm -Beat` | 音乐文件与重拍秒数 |
