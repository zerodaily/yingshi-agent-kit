# FAQ（实战踩坑记录）

## NotebookLM 登录
- `notebooklm list` 报 `Authentication expired or invalid`：cookie 快照可能仍有效但服务端会话失效。
  - 先试 `notebooklm auth refresh`；不行就 `python scripts/notebooklm_login.py`（Playwright 干净会话，需用户配合登录）。
  - **SID 一族 cookie 必须落在 `.google.com` 域**：只出现在 `.youtube.com` 上 CLI 不认。所以登录要用干净 profile，避免旧会话污染。
- `notebooklm login` 官方窗口反复 "closed during login"：`auth logout` + `--fresh`，或直接用 `notebooklm_login.py`。
- **所有命令报 `CSRF token not found in HTML. Final URL: https://notebook.google/?location=unsupported`**：
  不是 cookie 过期，是**代理出口 IP 落在 NotebookLM 不支持的地区**（实测中国香港节点必现）。
  先 `curl -sL https://notebooklm.google.com/` 看是否 302 到 `?location=unsupported`，
  再 `curl ipinfo.io` 确认出口地区；让用户把节点切到美/日/新等受支持地区即可恢复，不要走重新登录。

## 源文件上传
- 上传 `.md` 常报 source status=error：**转成 `.txt`**，用 `--type file --mime-type text/plain`。
- 源添加后 status 是 preparing/processing：稍等再 `source list` 确认 ready。

## 深度研究
- `source add-research` 后源列表为空：用 **`research wait --import-all`** 一次性导入全部研究源（不要逐个 add URL）。
- 研究源偶尔状态 error/preparing：等 processing 完成，error 的源可忽略或重加。

## 生成 PPT
- 并发多个 notebook 生成 slide-deck 会 `RATE_LIMITED`：**串行**，或间隔 30-60s。
- 语言码用 **`zh_Hans`**，`zh` 会报 Unknown language。
- 页数不要写死，让 NotebookLM 按拆分稿内容自判；拆分稿每份 750-1250 字效果最好。
- `artifact list --json` 输出前面有 `Matched:` 行、JSON 后有附加文本：解析时用
  `json.JSONDecoder().raw_decode(out[out.find("{") :])`。

## 下载
- `download slide-deck` 输出路径不能当位置参数：用 `--artifact <id>`。
- 默认下载 PDF；要 PPTX 加 `--format pptx`。

## IndexTTS2
- Gradio 版接口参数名：`do_sample` 等的实际参数名是 `param_16`、`param_21`(num_beams) 等（label 只是显示名）。
- 推荐 `num_beams=2`、`max_text_tokens_per_segment=200`，其余默认。
- 分章生成：每章 650-850 字约 8-11 分钟（GPU）；脚本有"已存在跳过"，中断可续跑。
- 服务端口以本地为准（常见 7860 / 8002）；启动后 `Invoke-WebRequest http://127.0.0.1:7860` 验证。
- 部署环境 `uv` 不在 PATH 时报 `exec: uv: not found`：直接用 venv 的 Python 启动：
  `./.venv/bin/python webui.py --fp16 --port 7860 --host 0.0.0.0 --model_dir ./checkpoints`。
- WSL 卡死（连 `wsl -e echo` 都超时）：`wsl --shutdown` 后重启即可。
- **口播稿改动后重生成单章**：`indextts2_speak.py` 检测到 `PartN.wav` 存在会跳过，
  必须先把旧文件改名/移走再跑，否则换稿不生效；随后重拼整轨、重转写、重对齐。

## 精确对齐（词级时间戳 + OCR + 内容锚点）
- NotebookLM 的 slide-deck PPTX **每页是整张图片、没有文字层**：`python-pptx` 抽不出文本，
  必须用 `ocr_pages.py`（RapidOCR / PP-OCRv4）识别导出的 PNG。
- huggingface.co 在国内被墙（解析到 127.0.0.1 / 连接被拒）：faster-whisper 模型改从
  ModelScope 下载（`Systran/faster-whisper-medium` 的 config.json / model.bin / tokenizer.json / vocabulary.txt），
  用本地目录路径传给 `--model`；hf-mirror 的 resolve 链接会 302 跳回 huggingface.co，不可用。
- Windows 版 Python 常缺 CUDA 运行库（`cublas64_12.dll` not found）：
  转写在 WSL 里跑（miniconda3 + `pip install faster-whisper`，GPU float16），音频/模型放到
  WSL 可见的挂载盘（如 E:），结果拷回项目。
- 对齐脚本默认 `--min-match 4`：>=6 字强锚点满分、4-5 字弱锚点半分；
  无匹配页按比例先验插值，页界统一吸附到 whisper 段边界（语音停顿）。
- 脚本改动后 `transcript.json` 必须重转写，否则对齐基于旧音频。

## HyperFrames 渲染
- 图片必须放在项目目录内（如 `assets/img/`），项目外的相对路径会报 `missing_local_asset` 且渲染跳过。
- 相邻 clip 浮点重叠报 `overlapping_clips_same_track`：后一个 clip 的 `duration` 减 0.001s。
- 无动画会报 `sweep_static`（Timeline did not advance）：每页加一个 0.4s 淡入 tween。
- **`check` 的 sweep_static 误报**：hyperframes 0.7.94 打包器 `bundleWithLocalizedFonts`
  对 `<audio ...></audio>` 自闭合标签处理异常，校验页里时间轴脚本失效、采样签名全同 → check 失败。
  实测：不闭合 audio 能过 check 但渲染全黑；自闭合形式 check 误报但**渲染完全正常**。
  **以渲染为准**（渲染不打包、直接服务原始 HTML），check 仅作参考门禁。
- 渲染帧缓存默认写系统 TEMP：C 盘空间不足报 `ENOSPC: no space left on device`（常见于 ~18000 帧）；
  渲染前把 `TEMP`/`TMP` 指到剩余空间大的盘（如项目盘），再 `npx hyperframes render`。
- `check` 通过后再 `render`；渲染 8-9 分钟视频约 15-16 分钟（GPU 硬件加速）；页面多/内存紧时更慢。
- 片尾分辨率/帧率不一致时：ffmpeg concat filter 统一 scale + aresample 44100。
- 中文路径下 `ffmpeg -f concat -i list.txt` 打不开列表文件：改用
  `-filter_complex "[0:a][1:a][2:a][3:a]concat=n=4:v=0:a=1[a]"` 直拼音频。

## NotebookLM 任务中断
- `generate` / `ask` 客户端断连（网络错误、命令被中断）不代表服务端停止：
  稍后用 `notebooklm artifact list -n <id> --json` 轮询到 `"status": "completed"` 再下载。
- 登录脚本默认 15 分钟超时；用户登录较慢时用 `--timeout 1800` 重开窗口，登录完成即可自动保存。
- `generate slide-deck` / `ask` 带 `--wait` 时超时要给足：**≥300 秒**（180 秒在详细模式经常不够）。

## 链式后台任务静默死亡（重要）
- 把「source add → generate → 轮询 → download」串成一条后台长命令时，`generate` 阶段经常静默死亡：
  进程还在但永远不推进、无报错。
- **改为单步手动执行**，每步验证后再下一步：create → source add（确认 ready）→ generate →
  轮询 artifact list → download。参照 `gen_ppt_manual.py` 的分步模式。
- NotebookLM 整体不稳定是常态，单步失败只重试该步，不要整段重来。
  国产替代备选（未实测）：扣子空间工作流、Kimi K2 API。

## 老项目 checkpoint 缺字段
- 早期 checkpoint 没有 `notebooklm_research_nb` 字段，直接续跑 step 2 会缺研究笔记来源（丰田踩过）。
- 续跑前检查 checkpoint 字段完整性，缺什么从对应 step 补起（缺研究字段就先补跑 step 1）。

## 口播稿校验（章节标题混入 / 开场白丢失 / 大纲式输出）
- NotebookLM 生成口播稿经常把**大纲/章节标题当正文输出**（本田事故：整片念大纲），也可能静默丢固定开场白。
- 不能靠提示词自觉，**必须在代码里做确定性校验 + 失败带原因重试（≥3 次）**：
  - 5 章 + 总字数 3000-5000 + 每章 ≥400 字。
  - 首个标题行之前的内容是元文本，截取丢弃；标题行不得进正文。
  - 正文开头 100 字内含开场白原文；正文以结尾语收尾。
  - 标题判定要排除含 `。！？；…～` 的叙述句，防误杀。
- 校验失败时把具体原因回灌进重试提示词（如「上一版每章只有 200 字，请扩写」）。实测福特项目第 2 次重试即通过。

## Python 版本（3.10 红线）
- 托管版 Python 3.13 装不上 ML 依赖（gradio_client、rapidocr_onnxruntime、pymupdf 实测失败）。
- 全流程脚本必须用 **Python 3.10**：`C:\Users\jonny\AppData\Local\Programs\Python\Python310\python.exe`（PATH 前置）。
- 症状：Step 3 报缺 gradio_client、Step 5 `import fitz` 失败、OCR 报缺 rapidocr —— 先查 Python 版本，别急着重装包。
- 缺 pymupdf 时 PDF 转 PNG 兜底：`pymupdf.open(pdf)` → `get_pixmap(dpi=150)` 逐页渲染（同样要用 3.10）。

## C 盘满 / npm 缓存 / Y 盘守卫
- C 盘长期接近满盘（~99%）：npm 缓存、渲染 TEMP、中间产物全部指大盘。
  - `npm config set cache "D:\workspace\tmp\npm-cache"`（全局 .npmrc），shell 里再
    `export npm_config_cache="D:\workspace\tmp\npm-cache"` 兜底。
  - 不做这一步，`npx hyperframes` 会被 Windows 安全删除守卫拦截，报错难排查。
- **Y 盘（网络盘）删除文件被安全守卫拦截**：清理/归档一律 `mv` 移到归档目录，不要 `rm`。

## IndexTTS2 服务启动（WSL 部署）
- 服务没启动时直接自行启动，不必问用户：进 WSL 到 `project/j-indextts2`，
  `uv run webui.py --fp16 --port 7860`；健康检查 `http://127.0.0.1:7860/` 返回 200。

## ffmpeg concat 静默失败
- `ffmpeg -f concat` 拼章节 wav 可能**静默失败**（无报错但 口播拼接.wav 缺失或时长为 0）。
- 拼完必须 `ffprobe` 验证时长 ≈ 各章之和；失败时手动补：
  `ffmpeg -y -f concat -safe 0 -i _concat.txt -c copy audio/口播拼接.wav`，再验证。
- 推荐预防：优先用 filter_complex 直拼（见上「HyperFrames 渲染」节）。

## HyperFrames 渲染爆盘 / 旧产物陷阱（重要）
- **长视频（≥10 分钟）必须 `npx hyperframes render --quality draft --low-memory-mode`**：
  多 worker（`--workers 2`）会把全部帧缓存到磁盘再编码，12 分钟视频实测需 ~205GB，必然爆盘；
  单 worker + 流式编码磁盘占用可控。
- **index.html 引用的是项目根目录的 `口播拼接.wav`，不是 audio/ 里的**：渲染前强制从
  `audio/口播拼接.wav` 覆盖复制到根目录。丰田事故：根目录残留旧 wav，成片全程念旧稿。
- **对齐脚本「index.html 存在即跳过」陷阱**：重做项目时旧 index.html / page_timeline.json
  会让 step 5 跳过重新对齐，沿用旧时间轴（本田/丰田都踩过）。重做前先归档旧产物强制重生成。
- **断点恢复「PNG 在 ppt/img ≠ 在 assets/img」陷阱（雪佛兰案例）**：HyperFrames 只认
  `assets/img/` 里的图片；分步恢复时 Part1-3 的 PNG 转好了但没拷进 assets/img，
  渲染不报错、成片对应页面**全黑**（missing_local_asset 只在日志里）。step-4 恢复后务必
  校验 `assets/img/` 页数 = 全部页面数（如 42），再进渲染。
- **黑屏快速检测法**：抽帧看体积——`ffmpeg -ss T -i final.mp4 -frames:v 1 -vf scale=160:90 f.jpg`，
  纯黑帧压缩后只有 ~800 字节，正常画面 5KB+；批量每 30s 抽一帧即可定位黑屏区间。
- 渲染后用 `ffprobe` 验证成片时长 ≈ 口播拼接.wav 时长，确认音画同源。

## WSL 内联命令
- 不要用内联 `python -c` 串 WSL 命令（引号转义必出 SyntaxError）：写成独立脚本文件（如 `lib/_ws_whisper.py`）再从 WSL 调用。

## 脚本年份规范（防 TTS 读错）
- 所有年份用中文数字，**用「零」不用「〇」**：`2021` → `二零二一`、`2001` → `二零零一`。
- 型号数字转中文读法：`LZ 110` → `LZ 一一零`、`宏光 S3` → `宏光 S 三`。
- 中英文之间一个空格；禁用破折号、连字符、下划线、括号。


## NotebookLM login browser
- New --browser firefox (default) or --browser chromium-msedge option.
- Firefox uses p.firefox.launch_persistent_context(); does not accept chromium-style args/ignore_default_args/channel.
- Requires python -m playwright install firefox first on Windows.

## NotebookLM slide-deck download
- --format pptx fails with UNEXPECTED_ERROR (empty message) on notebooklm-py 0.8.x; the artifact IS a PDF.
- Fix: download with --format pdf, pass to pptx_to_images.py --pptx, the script detects .pdf and skips LibreOffice.

## ffmpeg drawtext Chinese
- ffmpeg drawtext treats colon as option separator, so any fontfile / textfile absolute path with a colon (e.g. C:\Windows\Fonts\simhei.ttf or C:/temp/x.txt) fails: No option name near '/Windows/Fonts/simhei.ttf:textfile=...'.
- Fix: do not pass a path for fontfile / textfile. Use font=SimHei (fontconfig name) + inline text='Chinese'.
- Common Windows Chinese fontconfig names: SimHei, SimSun, Microsoft YaHei, Microsoft YaHei UI, Noto Sans SC, Noto Serif SC.
- Run c-list :lang=zh to list available Chinese fonts.

## ffmpeg output path with Chinese
- Error opening output file <chinese path>: Invalid argument.
- Fix: output to an ASCII path (e.g. C:/temp/outro.mp4), then shutil.copyfile to the project.

## HyperFrames gsap reference
- align_timeline.py emits <script src="assets/gsap.min.js"> by default; if you do not drop gsap into assets/ the page 404s in render.
- Fix: replace with the CDN before render: <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js">.


## Outro from a user-provided video
- Common case: 言同学片尾.mp4 (2560x1440 ~2K, 1-2 seconds, h264+aac) for branding.
- Make_outro.py --user-outro <path> rescales to 1920x1080@30fps and re-encodes aac 44100Hz.
- Concat_final.py handles the join with the main video. If main and outro have different
  resolutions or framerates, scale+pad+fps normalize first.
- Always output the concat to an ASCII path (e.g. C:/temp/final_<project>.mp4) then copy to
  the project; ffmpeg fails on Windows paths with non-ASCII characters.

## Concat filter_common errors
- Stream mismatch (different sample_rate or sample_fmt): the filter graph complains about
  "Input link parameters do not match". Always aresample to 44100Hz and use -ar 44100 -ac 2
  when re-encoding the source.
- Resolution mismatch: pad or scale to a common canvas before concat.
- Frame-rate mismatch: force a single -r 30 on output (or set ps=30 in the video filter).
