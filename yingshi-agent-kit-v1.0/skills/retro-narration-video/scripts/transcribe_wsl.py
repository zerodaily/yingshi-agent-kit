"""WSL faster-whisper transcribe. Run on Windows."""
import os, shutil, subprocess, sys

project = sys.argv[1] if len(sys.argv) > 1 else r"Y:\Projects\自媒体\20260905-丰田-审核"
audio_wav = os.path.join(project, "audio", "口播拼接.wav")
transcript = os.path.join(project, "audio", "transcript.json")

if os.path.exists(transcript) and os.path.getsize(transcript) > 1000:
    print(f"transcript exists, skipping ({os.path.getsize(transcript)} bytes)")
    sys.exit(0)

# Copy audio to WSL-accessible Windows temp
win_tmp = r"C:\Users\jonny\AppData\Local\Temp"
os.makedirs(win_tmp, exist_ok=True)
win_path = os.path.join(win_tmp, "audio.wav")
shutil.copyfile(audio_wav, win_path)

# Write whisper script
script_text = (
    "import json\n"
    "from faster_whisper import WhisperModel\n"
    "m = WhisperModel('medium', device='cuda', compute_type='float16')\n"
    "segs, info = m.transcribe('/tmp/audio.wav', language='zh', word_timestamps=True, beam_size=5)\n"
    "out = {'segments': [], 'words': []}\n"
    "for s in segs:\n"
    "    out['segments'].append({'start': round(s.start,3), 'end': round(s.end,3), 'text': s.text.strip()})\n"
    "    for w in (s.words or []):\n"
    "        out['words'].append({'start': round(w.start,3), 'end': round(w.end,3), 'text': w.word})\n"
    "open('/tmp/transcript.json', 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))\n"
    "print('DONE', len(out['segments']), 'segs,', len(out['words']), 'words')\n"
)
script_path = os.path.join(win_tmp, "_whisper_run.py")
with open(script_path, "w", encoding="utf-8") as f:
    f.write(script_text)

# Copy to WSL
subprocess.run(["wsl", "-e", "bash", "-c", "cp /mnt/c/Users/jonny/AppData/Local/Temp/audio.wav /tmp/audio.wav"], check=False)
subprocess.run(["wsl", "-e", "bash", "-c", "cp /mnt/c/Users/jonny/AppData/Local/Temp/_whisper_run.py /tmp/_whisper_run.py"], check=False)

# Run whisper
ld = "/home/zerodaily/miniconda3/envs/whisper/lib/python3.10/site-packages/nvidia/cublas/lib:"
ld += "/home/zerodaily/miniconda3/envs/whisper/lib/python3.10/site-packages/nvidia/cuda_runtime/lib:"
ld += "/home/zerodaily/miniconda3/envs/whisper/lib/python3.10/site-packages/nvidia/cuda_nvrtc/lib"
cmd = ["wsl", "-e", "bash", "-c",
       f"export LD_LIBRARY_PATH={ld}:$LD_LIBRARY_PATH && "
       f"cd /tmp && ~/miniconda3/envs/whisper/bin/python /tmp/_whisper_run.py"]
print("running:", " ".join(cmd[:5]) + " ...")
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
print("rc:", r.returncode)
print("stdout:", r.stdout[-1000:])
if r.returncode != 0:
    print("stderr:", r.stderr[-500:])
    sys.exit(1)

# Copy result back
r = subprocess.run(["wsl", "-e", "bash", "-c", "cat /tmp/transcript.json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode == 0 and len(r.stdout) > 100:
    with open(transcript, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    print(f"wrote {os.path.getsize(transcript)} bytes to {transcript}")