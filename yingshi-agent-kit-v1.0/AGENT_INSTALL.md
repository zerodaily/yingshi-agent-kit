# AGENT_INSTALL.md — 硬视产线 · Agent 本地部署执行手册

> **本文件写给 AI Agent 阅读。** 用户把本套件交给你，你的任务是：在这台电脑上完成「硬视」AI 视频工厂的全套本地部署，并通过末尾的冒烟测试。
>
> 你是执行者，不是提问者——除了 `config/onboarding.md` 里列出的必填项需要问用户，其余一切自行判断、自行安装、自行排错。排错资料见 `skills/retro-narration-video/references/` 下的四份文档（含已踩过的坑）。

---

## 阶段 0 · 用户访谈（先做这个）

逐项询问 `config/onboarding.md` 中的问题，把答案写入 `config/config.json`（模板见 `config/config.template.json`）。**必填项没有收集完之前，不要进入阶段 1。**

用户自备素材（音色样本、风格参考图）应放入 `assets-customer/` 目录。如果用户暂时拿不出，标记为待补，冒烟测试改用临时公开素材（见阶段 7）。

---

## 阶段 1 · 硬件与系统预检

逐项检查，任何一项不满足则停止并向用户说明，不要带病安装：

| 检查项 | 要求 | 检查命令 |
|---|---|---|
| 操作系统 | Windows 10/11 x64 | `systeminfo` |
| 显卡 | NVIDIA，显存 ≥ 8GB（12GB+ 更稳） | `nvidia-smi` |
| 显卡驱动 | CUDA 12.x 可用 | `nvidia-smi` 右上角 CUDA Version |
| 磁盘空间 | C 盘 ≥ 15GB；模型与工作目录所在盘 ≥ 60GB | `wmic logicaldisk get size,freespace,caption` |
| 内存 | ≥ 32GB 推荐 | `systeminfo` |
| WSL2 | 已启用或可启用 | `wsl --status` |
| 网络 | 可访问 GitHub 与 ModelScope（国内镜像） | `curl -I https://github.com` |

**注意**：
- WSL 未安装时执行 `wsl --install -d Ubuntu`，需要重启则告知用户重启后继续。
- 显存不足 8GB 时告知用户：TTS 与出图可跑但更慢，或改用 CPU 模式（仅研究+写稿可用）。

## 阶段 2 · 基础环境

按顺序安装并验证（已有则跳过）：

1. **Git** → `git --version`
2. **Python 3.10**（必须 3.10.x，3.11+ 会缺 ML 依赖）→ `python --version`；没有则 `winget install Python.Python.3.10`
3. **Node.js ≥ 20** → `node --version`；没有则 `winget install OpenJS.NodeJS.LTS`
4. **ffmpeg / ffprobe**（加入 PATH）→ `ffprobe -version`；没有则 `winget install Gyan.FFmpeg`
5. **WSL Ubuntu 内**：`uv`（IndexTTS2 用）与 **miniconda**（Z-Image 用）：

```bash
wsl -d Ubuntu -e bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh'
wsl -d Ubuntu -e bash -lc 'test -d ~/miniconda3 && echo has || wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/mc.sh && bash /tmp/mc.sh -b && ~/miniconda3/bin/conda init bash'
```

> 坑：C 盘空间不足时，把 npm 缓存与 TEMP 指到大盘：
> `npm config set cache "D:\workspace\tmp\npm-cache"`，渲染时 `TEMP/TMP` 指到大盘目录。

## 阶段 3 · IndexTTS2 语音合成服务（WSL）

```bash
wsl -d Ubuntu -e bash -lc 'cd ~ && git clone https://github.com/index-tts/index-tts.git j-indextts2 && cd j-indextts2 && uv sync'
```

- 启动：`wsl -d Ubuntu -e bash -lc 'cd ~/projects/j-indextts2 && exec uv run webui.py --fp16 --port 7860'`（用 Agent 的后台任务方式保持前台，**WSL 里 nohup 后台进程会随会话被杀**）
- 健康检查：`http://127.0.0.1:7860/` 返回 200；首次加载约 2-3 分钟，轮询等待
- 首次合成会自动下载模型权重（数 GB），耐心等待

## 阶段 4 · Z-Image-Turbo 出图（WSL + GPU）

```bash
wsl -d Ubuntu -e bash -lc 'cd ~ && git clone https://github.com/Tongyi-MAI/Z-Image.git Z-Image'
# 模型权重（国内走 ModelScope）：
wsl -d Ubuntu -e bash -lc 'pip install modelscope -y 2>/dev/null; modelscope download --model Tongyi-MAI/Z-Image-Turbo --local_dir ~/models/Z-Image-Turbo'
```

- conda 环境：`wsl -d Ubuntu -e bash -lc 'source ~/miniconda3/etc/profile.d/conda.sh && conda create -n zimage python=3.10 -y && conda activate zimage && pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124 && pip install -r ~/Z-Image/requirements.txt'`
- 验证：按 `skills/retro-narration-video/scripts/zimage_gen.py` 头部注释的要求放置模型路径（该脚本默认读 `~/models/Z-Image-Turbo`，与 clone 目录不符时以脚本注释为准调整）
- 单张 512px 出图约 20-50 秒（2080Ti 级别）

## 阶段 5 · Real-ESRGAN 放大（Windows）

1. 下载：https://github.com/xinntao/Real-ESRGAN/releases → `realesrgan-ncnn-vulkan-xxx.zip`
2. 解压到固定工具目录（如 `C:\yingshi\tools\`），记录 exe 路径写入 `config.json` 的 `esrgan_exe`
3. 验证：`realesrgan-ncnn-vulkan.exe -i 测试图 -o 输出.png -n realesrgan-x4plus -s 4`

## 阶段 6 · HyperFrames 渲染（Node）

```bash
mkdir 渲染测试目录 && cd 渲染测试目录 && npx hyperframes --version
```

- 渲染统一参数（不要改）：`npx hyperframes render --quality draft --low-memory-mode`
- **禁用 `--workers 2`**：多 worker 会导致长视频帧存储爆盘（10 分钟视频约 205GB）
- 渲染临时目录默认写系统 TEMP，C 盘紧张时先 `set TEMP/TMP` 到大盘

## 阶段 7 · 客户素材就位 + 冒烟测试

素材（用户自备，放入 `assets-customer/`）：
- `voice-sample.wav`：≥ 10 秒、干净无背景音乐的中文人声（客户自己的声音或已授权声音）
- `style-ref.png`：视觉风格参考图（客户 IP 形象/海报），决定出图风格

**冒烟测试全流程**（目标：产出一条 ≥ 30 秒、画面非黑、有配音的测试片）：

1. 写一个 3 章共 500 字的测试口播稿（规则见 skill `references/script-rules.md`：无章节标题进正文、开场白、结尾句、年份用汉字）
2. `parse_script.py` 切分校验 → `audio/chapters.json`
3. 启动 IndexTTS2 → `indextts2_speak.py` 合成 → filter 直拼 → `ffprobe` 验证时长
4. 写 2 个测试 prompt → `zimage_gen.py` 出图 → ESRGAN ×4 放大
5. 用 skill 的 `assets/starter_index_16x9.html` 模板合成 index.html → `npx hyperframes check`
6. `npx hyperframes render --quality draft --low-memory-mode` → 成片
7. **质检（不可跳过）**：`ffprobe` 验证时长；每 15 秒抽帧 `scale=160:90`，文件体积 < 1KB 的帧即黑屏 → 必须为 0；渲染前校验 index.html 引用的所有图片在磁盘上真实存在（缺图会静默渲染成黑屏，这是最高频事故）

## 阶段 8 · 交付与验收

向用户报告并逐项打勾：

- [ ] IndexTTS2 服务可启动、合成出声
- [ ] Z-Image 出图成功、风格与参考图一致
- [ ] ESRGAN 放大正常
- [ ] HyperFrames 渲染出片、无黑屏帧
- [ ] `config/config.json` 已保存全部配置（含各服务路径）
- [ ] 用户已知悉：日常使用只需对 agent 说「用硬视产线做一期XX的视频」

## 排错索引

所有已知坑与解法都在 skill 文档里，按报错关键词查：

- TTS 连接拒绝/启动失败 → `references/audio-pipeline.md`
- 出图风格漂移/显存不足 → `references/image-pipeline.md`
- 渲染黑屏/浮点重叠/sweep_static/爆盘 → `references/composition-and-render.md`
- 脚本校验不过/标题混入 → `references/script-rules.md`
- 旧流程（NotebookLM）的历史坑 → `references/faq-旧流程踩坑.md`（仅备用参考）

## 法务与合规提示（需转告用户）

- MediaCrawler 自动发布为 GPL 开源项目，**本套件不打包它**；如需启用，由 agent 现场 `git clone`，用户需自行承担平台条款与商用授权风险
- 音色样本与形象参考图必须是**用户本人或已获授权**的素材
- 生成内容发布到平台时需遵守各平台 AI 内容标识规定
