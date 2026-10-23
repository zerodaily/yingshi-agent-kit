# 本地出图（Z-Image + Real-ESRGAN）

## 环境

- 模型（Diffusers 目录）：`/mnt/e/ai-models/ltxdesktop/Z-Image-Turbo`
- 运行环境：WSL `~/miniconda3/envs/wan2gp`（Python 3.11，含 diffusers 的
  `ZImagePipeline`；base env 的 flash_attn 与 torch 不兼容，不要用 base）。
- 依赖工具目录：WSL 任意工作目录内放入本 skill 的 `scripts/zimage_gen.py`，
  在 `~/projects/Z-Image` 下运行即可（那里已有 `outputs/` 习惯）。

## 单批出图

先在项目写 `prompts.json`（Win 或 WSL 均可），**先跑 `reuse_illustrations.py <项目> --apply`
查共享配图库**：通用场景直接复用，只把 `still_needed.json` 里的场景拿来出图。
然后：

```bash
wsl -d Ubuntu -e bash -lc 'cd ~/projects/Z-Image && ~/miniconda3/envs/wan2gp/bin/python <skill>/scripts/zimage_gen.py <prompts.json> --project <项目名>'
```

`--project` 让输出隔离到 `outputs/<项目>/batch_01/`（自动递增），不再和旧工程
文件混在一起。

规格固定：

- 512×512，`num_inference_steps=4`，`guidance_scale=0.0`，bf16；
- 2080 Ti 上每张约 18–100 秒，模型只加载一次；与渲染或 TTS 抢卡时会更慢。
  一次不要超过 15 张，防止长时间失败难续跑；
- 输出 `outputs/zimg_<NN>_<key>_512.png`。

不要跑 768/1024 全精度（2080 Ti 实测 >20 分钟/张）。

## 风格锁定

`zimage_gen.py` 默认给每条 prompt 前缀：

```text
复古中国风插图，老报纸与宣纸质感，米黄色旧纸底，墨色线条，朱红点缀，
拙朴木刻版画与淡彩水墨结合，画面留白，无任何文字。内容：…
```

主体提示词只写“画面内容”和氛围，不写进画面文字。若想统一“更斑驳/更水墨”，
只改这一处前缀再整体重出，保证一批风格一致。

## 放大与归位

```powershell
python <skill>/scripts/esrgan_batch.py <项目目录>
```

批量把 `assets/illustrations/*_512.png` 放大为 `*_2048.png`（已存在且未变更的
自动跳过，中断可续跑）。底层调用 config 里 `esrgan_exe` 指定的
realesrgan-ncnn-vulkan.exe。若工具不存在，从
`github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip`
解压即可。

## 无参考图（重要）

Z-Image-Turbo 是文生图，不接受参考图/垫图。要复刻既有画风只能：

1. 统一风格前缀 + 固定调色滤镜（推荐，本项目采用）；
2. 未来接支持多图参考的在线 API（火山 Seedream / 阿里 wan2.7-image）时再升级，
   不要在本流程假装已支持参考图。

## Y 盘项目与 WSL 的文件交换（重要）

WSL **没有挂载 Y 盘**（Windows 网络映射盘），`/mnt/y` 不存在。
**不要手拷**，用 `scripts/sync_assets.py`：

```powershell
python <skill>/scripts/sync_assets.py push <项目目录>     # prompts.json -> WSL
python <skill>/scripts/sync_assets.py pull <项目目录> --project <项目名> --batch batch_01
python <skill>/scripts/sync_assets.py verify <项目目录>   # 回填后必跑：校验 index.html 引用的图全在
```

pull 会按场景 key 自动重编号归位（`zimg_NN_<key>_512.png` → `<key>_512.png`）；
verify 逐张检查引用，缺图直接失败——**缺图会静默渲染成黑屏，这是最高频事故**，
回填后必须跑 verify 通过了再 render。回填时按场景 key 精确匹配，别用宽泛 glob；
多批次出图每批编号都从 01 重新开始，回填前先重编号，避免串到旧参考工程的同编号文件。

## 基础配图与镜头变体

不要按 5 分钟 20 张的旧口径排图。新的镜头目标是 4–7 秒一个，5 分钟至少 45 个镜头。
为了控制出图成本，基础配图按叙事信息量准备：

- 5 分钟建议 24–32 张基础图，每 10–14 秒至少一张新的信息图；
- 8 分钟建议 36–48 张基础图；
- 同一张基础图可在不相邻的镜头中复用，但必须改变景别、裁切、前后景层次或标注重点；
- B-roll 空镜算独立镜头素材，不替代关键证据图；
- 写 `prompts.json` 时每个基础图给一个 scene key，再在分镜中建立“基础图 → 镜头变体”
  映射，禁止一图一标题复制满全片。

## 封面人物 IP 标准（小黑风「他」）

封面人物 IP 的唯一来源是 `jonny-illustrations`，视觉 DNA 继承
`ian-xiaohei-illustrations`。旧版「方眼镜、小胡子、山羊胡、写实卡通人」已废弃。

- **整体**：偏瘦、中等身高的黑色实心几何人形剪影，轮廓略带手绘抖动。
- **头部**：鹅蛋脸，短黑发用整块实心形状表现；不画发丝、鼻子、耳朵和胡须。
- **眼镜与眼睛**：细黑框方形或圆方形眼镜，白色镜片内各有一个小白点眼。
- **嘴**：下半脸留白，只用一条冷静的平线。
- **穿着**：黑色短袖 T 恤、左胸一个极小识别图标、右肩至左胯一条细斜挎带、黑色裤子和块状鞋。
- **手**：黑色实心小块，不画五指。
- **风格**：纯白底、黑色手绘线稿、大量留白，少量红橙蓝批注；不要旧纸纹理、写实人脸、Q 版或商业插画质感。
- **动作**：必须与车或核心物件发生物理互动，例如拉安全带、蹲在车轮边量尺寸、靠车门、指发动机、站在碰撞装置旁。不能僵硬站在旁边当装饰。
- **比例**：占画面约 1/4–1/3，醒目但不抢车的主角地位。
- **生成方式**：先生成人物与车同框的一张完整场景底图，不把车和人物拆成两张再拼贴。
- **文字**：生图不写字；标题、品牌、年份、数字、标签和「言同学」印章全部由 HTML/CSS 叠加。

完整可复制提示词与沃尔沃动作示例见
`references/cover-ip-prompt.md`。Z-Image 不接受参考图，IP 一致性靠固定提示词、
统一手绘线条和固定几何识别点锁定。
