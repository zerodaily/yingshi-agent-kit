# 配音与转写

## IndexTTS2 服务

部署目录（WSL）：`~/projects/j-indextts2`。服务没起就启动，不问用户。**只用前台
exec 交给宿主后台任务**，不要用已经验证会随会话退出的 `nohup`：

```bash
wsl -d Ubuntu -e bash -lc 'cd ~/projects/j-indextts2 && exec ./run_optimized.sh'
```

健康检查：`http://127.0.0.1:7860/` 返回 200。加载约 2–3 分钟。
> 另外 TTS 刚才还 200 不代表现在活着——`indextts2_speak.py` 开头已内置健康检查与
> 自动拉起（`--no-auto-start` 可关闭），无需每次手动 curl。

需要手动停止时，使用不会匹配当前 shell 本身的安全形式：

```bash
wsl -d Ubuntu -e bash -lc "pkill -f '[w]ebui.py'"
```

## 分章生成

```powershell
python <skill>\scripts\indextts2_speak.py `
  --chapters <项目>\audio\chapters.json `
  --ref <项目>\assets\口播样本_小强.wav `
  --base <项目>
```

- 音色样本：`Y:\Projects\自媒体\小强的声音文件sample.wav`（复制进项目
  `assets/口播样本_小强.wav`）。
- 输出 `audio/Part1..N.wav`（N = 章节数）+ `audio/timeline.json`；已有文件会跳过。
- 改口播后重录：把旧 `PartN.wav` 移到 `audio/old_*`，只重跑受影响章节。
- 生成约 2–3 倍于音频时长；5 分钟片约 15–25 分钟。

## 拼接并校验（必须）

中文路径用 filter 直拼，不要用 `-f concat` 列表文件。下面脚本按目录里 `Part1..N.wav`
实际章节数动态收集、按序号排序后拼接，章节数变化不用改命令：

```powershell
python -c "import subprocess,os,glob,re; base=r'<项目>'; cwd=os.path.join(base,'audio'); parts=sorted(glob.glob(os.path.join(cwd,'Part*.wav')),key=lambda p:int(re.search(r'Part(\d+)',p).group(1))); n=len(parts); args=['ffmpeg','-y']+[x for p in parts for x in ('-i',p)]+['-filter_complex',''.join('[%d:a]'%i for i in range(n))+'concat=n=%d:v=0:a=1[a]'%n,'-map','[a]','-c:a','pcm_s16le',os.path.join(cwd,'口播拼接.wav')]; subprocess.run(args,check=True)"
```

校验：`ffprobe` 时长 ≈ Part1..N 之和。然后把 `口播拼接.wav` 复制到**项目根目录**
（HyperFrames 相对引用用根目录音频）。

## 词级转写

```powershell
python <skill>\scripts\transcribe_wsl.py <项目目录>
```

脚本会用 WSL faster-whisper（`~/miniconda3/envs/whisper`，medium/cuda）写
`audio/transcript.json`。GPU 与 IndexTTS2 共用时内存会高，必要时先停 TTS：
`wsl -d Ubuntu -e bash -lc "pkill -f '[w]ebui.py'"`。

## 时间轴注意

- 每次重新配音后时长会变，必须按新章节时长等比重排画面（先读
  `audio/timeline.json` 的新章节边界，再按章节内画面比例重算，连续填充、无重叠）。
- 场景结束到下一场景开始不允许重叠（HyperFrames 同 track 重叠会 lint 报错）。

## BGM 选曲（配音完成后、混音前执行）

不再固定使用同一首 bgm.wav。配音完成后执行：

```powershell
Y:\Projects\自媒体\_BGM库\Select-BGM.ps1 -ProjectDir "<项目目录>"
```

- 自动按口播关键词匹配 7 个分类（怀旧 / 史诗感 / 紧张 / 悲伤 / 轻松 / 激昂热血 / 悬疑揭秘），随机选曲，默认避免最近 5 个项目用过的曲目。
- 自动转 44100Hz 立体声 WAV，输出到 `assets/bgm.wav` 并同步竖屏工程。
- 视频比 BGM 长时加 `-TargetDuration <秒>` 自动循环。

## 混音电平硬标准（最高优先级，违反即返工）

- **人声**：成片综合响度 `-16 ± 1 LUFS`，真峰值不高于 `-1.5 dBTP`，人声是绝对主角。
- **BGM 全程固定平稳音量：比人声低 12–15 LU**，稳定铺在背景里当情绪底色。
- **禁止动态侧链闪避 / ducking**：不要一说话就压 BGM、人停就升 BGM；BGM 全程音量平稳不跳变。
- 禁止 BGM 和人声一样大、禁止 BGM 盖过人声、禁止用太炸的鼓点盖过旁白。
- 「关键数字加重」只允许做成**一次性重音**（该处 BGM 短暂停顿或加重一下后立刻回平稳），不允许做成持续的音量起伏或闪避。
- 混音完成必须检测 `integrated LUFS / true peak / clipping`；检测命令可用
  `npx --yes hyperframes@latest audio <成片.mp4> --json` 或 `ffmpeg loudnorm print_format=json`。
