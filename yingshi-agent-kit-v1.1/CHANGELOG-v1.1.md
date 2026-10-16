# v1.1 更新说明（2026-10-07）

## 新增：多画风包

产线从「单一复古纸墨」升级为「一套产线 + N 个画风包」。产线八步只有
第 ⑤（出图）、⑤.5（元素处理）、⑥（合成）读画风包，其余步骤与画风无关。

```
styles/
├── 00-retro-paper/     包 0 复古纸墨（现行，未动）
├── 10-collage-archive/ 包 A 档案调查拼贴（样板已验收）
└── 20-collage-design/  包 B 设计拼贴（样板已出）
```

每个包固定提供：`STYLE.md`（令牌）、`prompts/still-prefix.txt` + `still-suffix.txt`
（出图前缀）、`motion.yaml`（动效词汇）、`elements/manifest.json`（元素库与授权）、
`library/`（元素 PNG）、`qc.md`（验收清单）。

## 新增：本地元素引擎

`scripts/photo_to_cutout.py` —— 真实照片 → 抠图 → 半调网点（带印刷网角）→
双色调上纸 → 撕边/裁切 → 纸纤维颗粒 → 透明 PNG。

跑在 WSL `wan2gp` 环境（rembg + numpy + Pillow 齐全），纯 CPU，7 个元素约 12 秒，
不占显存。抠图失败会自动降级成矩形照片碎片，流程不中断。

配套：`make_scraps.py`（从底图裁衬片）、`qa_elements.py`（元素墨量与覆盖率）、
`qa_frames.py`（成片抽帧抓黑帧）。

## 新增：分层舞台模板（四个）

- `assets/starter_stage_archive_16x9.html` —— 包 A（1920×1080 / 14s）
- `assets/starter_stage_archive_9x16.html` —— 包 A 竖屏（1080×1920 / 14s）
- `assets/starter_stage_design_9x16.html` —— 包 B（1080×1920 / 12s）
- `assets/starter_stage_design_16x9.html` —— 包 B 横屏（1920×1080 / 12s）

四个模板都本地引用 `assets/vendor/gsap.min.js`（随包 71KB），不走 CDN，保证离线与可复现。
合成规范见 `references/styled-scene.md`。

## 样板实测

| 项 | 包 A 档案调查 | 包 B 设计拼贴 |
|---|---|---|
| 画布 / 时长 | 1920×1080 / 14s | 1080×1920 / 12s |
| 渲染耗时（draft） | 34.8s（2.5× 实时） | 27.7s（2.3× 实时） |
| 元素处理 | 7 个 / 约 12s | 4 个 / 约 5s |
| check | 0 error / 0 warning | 0 error / 0 warning |
| 首帧 | 空纸面（mean 167 / std 11） | 纯色场（mean 103） |
| 末帧 | 拼贴成型（std 50 / 墨量 13.5%） | 设计成型（std 71） |

两个样板的素材全部是真实档案照片（Wikimedia Commons），来源与授权记录在各自
`elements/manifest.json`。

## 对硬件的影响

两个新画风不依赖任何视频生成模型，没有新增模型下载，抠图与半调是 CPU + ONNX，
8GB 显存的机器也能跑；渲染成本与现有产线一致。

## 待办

- 横竖屏“自动重排”脚本（当前四种组合的手工模板已齐，自动重排是纯省事）
- 元素库跨车系积累（现在每集仍要新拉一批照片）

## 首次实战：捷豹一集（2026-10-07）

拿现有成片 `20260929-捷豹Jaguar`（51.5 秒）完整跑了一遍包 A：

- **音频直接复用原 `口播混音.wav`**，不重跑 TTS，时间轴天然对得上
- 12 个场景、14 个拼贴元素（11 张 Wikimedia 真实档案照片 + 3 张 1900 年英格兰地质图碎片）
- 横屏 1920×1080 与竖屏 1080×1920 各 51.5 秒，draft 各约 2 分钟
- 全流程机器时间约 8 分钟（含素材下载限流等待）

由此新增：

- `scripts/build_film.py` —— 分镜构建器：一份 `film.json` 生成横竖两个 HyperFrames 工程，
  自动排节拍、自动补长场景第二波、左出右进、红绳自动连线
- `references/film-json.md` —— `film.json` 字段与槽位说明
- `references/example-film.json` —— 捷豹一集的真实分镜，可直接改文案复用

**最有价值的结论**：样板那套 10 秒组装节奏在成片里用不了。旁白 beat 只有 2.4–5.6 秒，
组装必须压到 1.2–2.0 秒（元素间隔 0.22 秒、单件 0.32 秒），5 秒以上场景要在 50% 处补第二波元素。
写在 `references/styled-scene.md` 的「实战校准」一节。

## 长片与多领域（2026-10-07 晚）

### 篇幅：3000–5000 字硬闸

- 实测语速 **5.43 字/秒**（14 集样本）→ 3000 字 ≈ 9.2 分钟，5000 字 ≈ 15.3 分钟，
  按 4 秒/画面就是 138–230 个画面
- `scripts/validate_script.py` 新增篇幅硬校验：全文不在 3000–5000 字（或短片档
  1200–2500 字）直接报错；长片模式下每章少于 400 字也报错；并打印预计时长与画面数
- 新增 `scripts/measure_pace.py`：随时用现有项目重算语速

### 长片能力

- `scripts/build_film.py` 新增**场景变体轮换**（assembly / reveal / wide / left /
  board / document），保证相邻两场不同构图，并输出质检摘要（变体分布、相邻同构图数、
  元素库用量）
- 新增**章节卡**：场景加 `"chapter"` 字段即可渲染大编号 + 标题 + 红线
- 新增 `scripts/scale_test.py`：把短分镜扩写成任意时长做压力测试
- **投影烘进元素 PNG**（`element_shadow: "baked"`）：单文件"重叠加层"数量从 116 降到 0，
  消除长片黑帧风险；图钉等装饰件也改成实色，不再用径向渐变

### 通用性：画风 × 领域 两个正交维度

新增 `domains/` 领域包，与 `styles/` 画风包正交：

| 维度 | 管什么 |
|---|---|
| `styles/` | 看起来怎样：配色、字体、材质、动效、版式槽位 |
| `domains/` | 讲的是什么：素材来源、元素类型、标注词汇、领域坑 |

已建四份：`automotive/`（已实战）、`ai/`（AI 题材没有历史照片，走官方图/自截屏/自绘线框）、
`history/`、`_template/`。新增领域只需写一份 `DOMAIN.md` + 攒一批元素，不动画风和代码。

### 长片实战工具补全（2026-10-08）

为 12 分钟级长片补齐自动化：

- `scripts/plan_scenes.py` —— **分镜自动排布**：读转写 + 元素库 + 章节表，按目标秒数切场景、
  按关键词挑元素（旁白提到九三零就上九三零的图）、角色轮换、自动插章节卡，产出 `film.json`
- `scripts/make_element_job.py` —— 把一整个素材目录变成元素引擎的 job.json，
  按文件名自动分角色（实物 / 人物 / 地图 / 碎片）
- `references/plan-scenes.md` —— 用法与"人工必补的三件事"

首个长片实战项目：`Y:\Projects\自媒体\20261007-保时捷911六十年-vox拼贴`（3976 字 / 9 章 /
预估 12.2 分钟 / 约 180 个画面），走的就是「长片档校验 → IndexTTS2 → 元素库 →
plan_scenes → build_film → check → 渲染」这条链路。

### 镜头语言与子合成（2026-10-08 第二轮）

长片第一版跑出来后暴露两个问题，都已修：

**问题一：镜头太单一。** 只换元素落点，156 场看起来还是一个模子。新增**镜头类型**层
（在六种变体之上）：常规分层、满幅出血特写、左右双联、巨号年份块、照片墙、年表轴、人物圈注，
按固定顺序轮换；再加**三种纸色轮换**（暖黄 / 浅米 / 灰），整片不再是一张纸。

**问题二：单文件到极限。** 加密画面后单文件 410KB / 4000 个补间，
`check` 报 `Navigation timeout of 10000ms`（浏览器建不完时间轴）。
新增 `scripts/build_film_split.py`：按章拆成子合成（每 20 场一个），宿主只留底板与音轨。
拆完 `check` 回到 0 error / 0 layout / 0 runtime。

同时新增：`film.json` 支持 `bgm` 字段（宿主页第二音轨，`loop` + `volume`），
与现有 `Select-BGM.ps1` 选曲流程对接。

### BGM 响度治理（2026-10-08 第三轮）

把 BGM 挂成第二条音轨、靠播放器 `volume` 压制是错的：实测旁白 -27.2 LUFS、
BGM 素材 -15.9 LUFS，**音乐比人声响 11 LU**，压不住；mono→stereo 上混还会再丢 3 dB。

新增 `scripts/mix_bgm.py`：按响度算增益 + 人声频段让位 + 侧链闪避 + 限幅，
输出单轨 `口播混音.wav`。

**默认值经过一轮返工**：`--keep-below 18` 试出来音乐几乎听不见（「音乐没有了」），
最终定为 **10 LU + 4:1 闪避**——听得见、但说话时不抢口播。每集可在 11–15 之间微调。

这条片子的最终结果：

- BGM 增益 **-21.3 dB**（-15.9 → -37.2 LUFS）
- 成片 -27.3 LUFS，与旁白 **只差 0.10 LU**；旁白电平零损失（-28.401 → -28.333 dB）
- 停顿处 BGM -42.6 dB（比人声低 14 dB）；说话时闪避后低约 21 dB
- 真峰值 -4.5 dBFS

流程上改为：`audio` 指向烘好的 `口播混音.wav`，不再挂第二条音轨；
已渲好的片子可以只换音轨不重渲（`-c:v copy`）。

### 镜头语言（2026-10-08 第四轮）

用户反馈「镜头语言还是太单一」。查了电影语法资料（field size / camera angle /
movement / composition / 剪辑节奏 / transition），发现自己之前只做了"构图"一个维度，
于是新增 `scripts/shotgram.py`：

| 维度 | 取值 | 这条片的分布 |
|---|---|---|
| 景别 | ELS/LS/MS/CU/ECU/INSERT | 1% / 24% / 24% / 25% / 11% / 14% |
| 机位 | eye/topdown/low | 77% / 12% / 11% |
| 运动 | static/push/pull/drift/pan | 26% / 37% / 23% / 12% / 2% |
| 构图 | center/left/right/negative/diag | 36% / 9% / 22% / 20% / 13% |
| 转场 | cut/dissolve/match | 59% / 24% / 17% |
| 时长 | 2.4–7.5 秒（按文本密度） | 中位 4.1 秒 |

第一版规则让"转折/数字"这类词主导，结果 91% 平视、48% 推镜、0 叠化；改成
**轮换为主、内容覆盖为辅**后才散开。文档见 `references/shotgram.md`。

另外两个经验：

- **渲染读的是目录下的 `index.html`**，只改文件名（如 `proof_index.html`）不会被渲染——
  我在样片流程上白跑了两次，样片必须放独立子目录。
- 整层做镜头运动会明显变慢（~13fps → ~10fps，12 分钟片 22 分钟 → 35 分钟），
  `.shot` 容器加了 `will-change: transform`。

## 四个分层模板（已完工）

| 模板 | 画风 | 画布 | check | 渲染 | 首帧 → 末帧 |
|---|---|---|---|---|---|
| `starter_stage_archive_16x9.html` | 包 A | 1920×1080 / 14s | 0 error | 33.2s | std 11 → 50 |
| `starter_stage_archive_9x16.html` | 包 A 竖屏 | 1080×1920 / 14s | 0 error | 33.5s | std 10 → 50 |
| `starter_stage_design_9x16.html` | 包 B | 1080×1920 / 12s | 0 error | 26.9s | std 7 → 71 |
| `starter_stage_design_16x9.html` | 包 B 横屏 | 1920×1080 / 12s | 0 error | 27.5s | std 7 → 65 |

四种组合的抽帧质检都满足硬指标：首帧是空底纸/纯色场，无黑帧，信息量逐秒递增。

