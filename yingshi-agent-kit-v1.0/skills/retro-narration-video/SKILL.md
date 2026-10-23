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

## 配置来源

生产配置只有一份：`<skill>/config.json`，或 `YINGSHI_CONFIG` 指向的文件。
`config.template.json` 只是部署模板；仓库 `config/config.json` 只作为安装种子，
不得在运行中同时维护两套值。启动 TTS、出图或渲染前先确认脚本实际读到的是哪一份。

新项目优先用 `new_project.py` 搭建；只有需要复刻某个已验收构图时才复制旧工程。
制作前把风格、平台、目标时长和章节结构写进 BRIEF。先完成口播稿与 6 尺寸封面，
一起交用户确认；确认前不进入 TTS、出图或渲染，确认后不再先出图再改文案。

## 风格三选一（开工前在 BRIEF 定死，全片不混）

| 风格 | 适用 | 镜头基调 | 镜头语法 |
|---|---|---|---|
| 动态纸墨（默认） | 品牌历史长故事、人物传记，5–8 分钟 | 真实空镜或满幅木刻画打底，纸片、人物、标注分层，切镜承载叙事 | `visual-craft.md` §6.1 |
| Vox 拼贴 | 硬核解释、反常识冷知识，仅限 60–180 秒短片/实验片 | 固定机位桌面拼贴，2–3 秒一个事件 | `visual-craft.md` §6.2 |
| huashu 艺术动态 | 视觉冲击强、节奏快的 15–180 秒短片 | 相机平滑 + 元素步进，硬切快推 | `visual-craft.md` §6.3 |

B 站 5–8 分钟长片默认只用“动态纸墨”。Vox / huashu 不替代长片主流程；需要长解释
内容时先用动态纸墨完成长片，再单独剪一条 60–180 秒实验短片。

`MG Styles 15` 等新增来源目前只登记在 `references/future-style-references.md`，
属于候选参考，不属于以上三种已生效风格，不参与当前选型、分镜、出图或渲染。

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
- [references/cover-ip-prompt.md](references/cover-ip-prompt.md)：言同学定稿人物
  （照片原型 · 黑色钢笔线稿）的封面生图提示词、同框互动要求和动作示例。
- [references/publish.md](references/publish.md)：B 站 Browser Use 发布步骤、
  发布说明模板、抖音物料、标题标签简介规范、草稿箱限制。
- [references/future-style-references.md](references/future-style-references.md)：
  `MG Styles 15` 候选风格库。**尚未整合**；只有用户明确要求研究或扩展风格时才读取，
  不得影响当前动态纸墨主流程。

## 全局不可变硬规则（跨册，违反即返工；细则在对应分册）

1. **年份用「零」不用「〇」**：`二零二四`、`二零零六`；交 TTS 前对 chapters.json
   全局检查 `〇`。细则见 `script-rules.md` §3。
2. **口播正文禁止章节标题、Markdown 符号、括号、破折号**；章节头只用于视觉标题，
   绝不进 TTS。
3. 开场和结尾按平台分流：
   - B 站长版：第 1 章 hook 后必须出现 `欢迎回来，我是言同学。`，全片仅一次；
     结尾用 `fixed_copy.ending_line`，固定句后接本集互动问题。
   - 抖音短版：0–3 秒直接钩子，禁止出现 `欢迎回来，我是言同学。`；结尾必须用
     本集互动问题收束。
   `fixed_copy` 以 `config.json` 为唯一来源，细则见 `script-rules.md` §2、§5。
4. **文字不交给文生图**：AI 只画画面内容，所有文字由 HTML/CSS 叠在卡片上，保证字形清晰。
5. Z-Image 在 2080 Ti 上用 512×512、4 步；不得跑 768+ bf16 全精度；放大交给
   Real-ESRGAN。细则见 `image-pipeline.md`。
6. **每个画面必须有明确视觉主体**：木刻插画、满幅档案图或真实 B-roll 均可。B-roll
   只能作为镜头底层或叙事素材，不能替代主体；禁止异风格图、无意义素材拼接和纯文字页。
7. HyperFrames 生产工程采用「一个主壳 + 每场一个子合成」：`index.html` 只挂音频和
   `data-composition-src` 场景宿主，场景 HTML 放在 `compositions/`。只有不超过
   5 场的冒烟样片允许单文件。所有定时媒体保留 `class="clip"`；中文字体必须
   `@font-face src: local()` 声明。结构细则见 `composition-and-render.md`。
8. 统一使用 `npx --yes hyperframes@latest`，避免机器上的旧版解析；TEMP/TMP 指到大盘
   （`D:\workspace\tmp\...`）。长片可保留 auto workers，但禁止手工指定 `--workers 2`。
   细则见 `composition-and-render.md`。
9. **时长与镜头下限**：B 站长版横屏必须 5–8 分钟，低于 4 分钟打回重做。镜头目标
   4–7 秒，5 分钟至少 45 个镜头，8 分钟至少 70 个镜头；同一张图不得连续占用两个
   镜头。镜头可通过裁切、分层、B-roll 和版式变化复用同一批基础素材。口径唯一权威在
   `visual-craft.md` §2 与 `script-rules.md` §1。
10. **音频电平**：人声目标 `-16 ± 1 LUFS`、真峰值不高于 `-1.5 dBTP`；BGM 全程固定
    比人声低 12–15 LU、平稳不跳变，禁止侧链闪避 / ducking。成片必须用响度检测验证，
    不能只看播放器音量。细则见 `audio-pipeline.md`「混音电平硬标准」。
11. **封面统一语言**：回归已验收旧风——米黄旧纸底 + 撕边毛边纸卡 + 黑白半调/木刻排线车图，
    人物为黑色钢笔线稿「言同学」（保留照片原型辨识特征：上唇小髭 + 下巴山羊胡、细框矩形眼镜、
    黑色乱发、中等略壮），顶部超大磨损品牌名，白底朱红印章。禁止深墨绿充墨扁平插画、黄肤扁平
    色块人物和硬黑矩形画框。标准定义唯一权威在 `image-pipeline.md`，完整生图提示词在
    `cover-ip-prompt.md`，封面落位与模板在 `cover-and-layout.md`。

## 工作流闸门

1. **封面与稿先行确认**：新项目完成口播稿后，先出 6 个尺寸封面（1:1 / 16:9 /
   9:16 / 4:3 / 3:4 / 4:5），连同稿子交用户确认 IP 形象与标题排版；用户确认前
   禁止进入配音、出图、渲染，不白烧算力。
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
