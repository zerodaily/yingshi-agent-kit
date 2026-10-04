# 本地出图（Z-Image + Real-ESRGAN）

## 环境

- 模型（Diffusers 目录）：`/mnt/e/ai-models/ltxdesktop/Z-Image-Turbo`
- 运行环境：WSL `~/miniconda3/envs/wan2gp`（Python 3.11，含 diffusers 的
  `ZImagePipeline`；base env 的 flash_attn 与 torch 不兼容，不要用 base）。
- 依赖工具目录：WSL 任意工作目录内放入本 skill 的 `scripts/zimage_gen.py`，
  在 `~/projects/Z-Image` 下运行即可（那里已有 `outputs/` 习惯）。

## 单批出图

先在项目写 `prompts.json`（Win 或 WSL 均可），然后：

```bash
wsl -d Ubuntu -e bash -lc 'cd ~/projects/Z-Image && ~/miniconda3/envs/wan2gp/bin/python <skill>/scripts/zimage_gen.py <prompts.json>'
```

规格固定：

- 512×512，`num_inference_steps=4`，`guidance_scale=0.0`，bf16；
- 每张 20–50 秒，模型只加载一次；一次不要超过 15 张，防止长时间失败难续跑；
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
& "Y:\Projects\自媒体\_本地出图实验\tools\realesrgan-ncnn-vulkan.exe" `
  -i <512.png> -o <2048.png> -n realesrgan-x4plus -s 4
```

每张约 10–20 秒。若工具不存在，从
`github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip`
解压即可。放大后的 2048 图复制到 `<项目>/assets/illustrations/`。

## 无参考图（重要）

Z-Image-Turbo 是文生图，不接受参考图/垫图。要复刻既有画风只能：

1. 统一风格前缀 + 固定调色滤镜（推荐，本项目采用）；
2. 未来接支持多图参考的在线 API（火山 Seedream / 阿里 wan2.7-image）时再升级，
   不要在本流程假装已支持参考图。

## Y 盘项目与 WSL 的文件交换（重要）

WSL **没有挂载 Y 盘**（Windows 网络映射盘），`/mnt/y` 不存在。prompts.json 要先复制到
`C:/Users/jonny/AppData/Local/Temp/` 再 `cp` 进 WSL；出图产出在
`~/projects/Z-Image/outputs/`，同样经 Temp 拷回 Windows。
注意 `~/projects/Z-Image/outputs/` 里混着**旧参考工程的同编号文件**，
拷贝时按场景 key 精确匹配（如 `_s13_ingredients_`），别用宽泛 glob。
多批次出图时每批编号都从 01 重新开始，回填 index.html 引用前要**重编号**
（如第二批 01→12），并逐张校验 index.html 引用的图在磁盘上都存在（防黑屏）。

## 每画面一张

画面数与口播场景数一致（5 分钟约 20 张）。写 `prompts.json` 时每个 scene 给一个
key 对应场景 id（如 `s03_contract`），方便回填 HTML 时一一对应。
