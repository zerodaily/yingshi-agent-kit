# 配音与转写

## IndexTTS2 服务

部署目录（WSL）：`~/projects/j-indextts2`。服务没起就启动，不问用户：

```bash
wsl -d Ubuntu -e bash -lc 'cd ~/projects/j-indextts2 && nohup ./run_optimized.sh > webui_run.log 2>&1 &'
```

健康检查：`http://127.0.0.1:7860/` 返回 200。加载约 2–3 分钟。
如果日志混入上一次推理内容，先 `mv webui_run.log webui_run_old.log` 再启动。

> 启动方式坑（实测）：`wsl -d Ubuntu -e bash -lc 'nohup ... &'` 的后台进程会随会话退出被杀
> （日志为空、进程消失）。改用 **exec 前台方式挂宿主后台任务**：
> `wsl -d Ubuntu -e bash -lc 'cd ~/projects/j-indextts2 && exec ./run_optimized.sh'`（run_in_background）。
> 另外 TTS 刚才还 200 不代表现在活着——`indextts2_speak.py` 开头已内置健康检查与
> 自动拉起（`--no-auto-start` 可关闭），无需每次手动 curl。

## 分章生成

```powershell
python <skill>\scripts\indextts2_speak.py `
  --chapters <项目>\audio\chapters.json `
  --ref <项目>\assets\口播样本_小强.wav `
  --base <项目>
```

- 音色样本：`Y:\Projects\自媒体\小强的声音文件sample.wav`（复制进项目
  `assets/口播样本_小强.wav`）。
- 输出 `audio/Part1..5.wav` + `audio/timeline.json`；已有文件会跳过。
- 改口播后重录：把旧 `PartN.wav` 移到 `audio/old_*`，只重跑受影响章节。
- 生成约 2–3 倍于音频时长；5 分钟片约 15–25 分钟。

## 拼接并校验（必须）

中文路径用 filter 直拼，不要用 `-f concat` 列表文件：

```powershell
python -c "import subprocess,os; base=r'<项目>'; cwd=os.path.join(base,'audio'); parts=[f'Part{i}.wav' for i in range(1,6)]; args=['ffmpeg','-y']+[x for p in parts for x in ('-i',p)]+['-filter_complex','[0:a][1:a][2:a][3:a][4:a]concat=n=5:v=0:a=1[a]','-map','[a]','-c:a','pcm_s16le','口播拼接.wav']; subprocess.run(args,cwd=cwd,check=True)"
```

校验：`ffprobe` 时长 ≈ Part1..5 之和。然后把 `口播拼接.wav` 复制到**项目根目录**
（HyperFrames 相对引用用根目录音频）。

## 词级转写

```powershell
python <skill>\scripts\transcribe_wsl.py <项目目录>
```

脚本会用 WSL faster-whisper（`~/miniconda3/envs/whisper`，medium/cuda）写
`audio/transcript.json`。GPU 与 IndexTTS2 共用时内存会高，必要时先停 TTS：
`wsl -d Ubuntu -e bash -lc 'pkill -f webui.py'`。

## 时间轴注意

- 每次重新配音后时长会变，必须按新章节时长等比重排画面（先读
  `audio/timeline.json` 的新章节边界，再按章节内画面比例重算，连续填充、无重叠）。
- 场景结束到下一场景开始不允许重叠（HyperFrames 同 track 重叠会 lint 报错）。
