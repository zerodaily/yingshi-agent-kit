"""WSL faster-whisper transcribe. Run on Windows."""
import os, shutil, subprocess, sys

try:
    from yingshi_config import load_config, cfg_get, expand
    _CFG = load_config()
except Exception:
    _CFG = {}


def _cf(key, default):
    return cfg_get(_CFG, key, default) if _CFG else default


project = sys.argv[1] if len(sys.argv) > 1 else r"Y:\Projects\自媒体\20260905-丰田-审核"
audio_wav = os.path.join(project, "audio", "口播拼接.wav")
transcript = os.path.join(project, "audio", "transcript.json")

if os.path.exists(transcript) and os.path.getsize(transcript) > 1000:
    print(f"transcript exists, skipping ({os.path.getsize(transcript)} bytes)")
    sys.exit(0)

# Copy audio to WSL-accessible Windows temp
win_tmp = expand(_cf("wsl_temp", r"C:\Users\jonny\AppData\Local\Temp"))
os.makedirs(win_tmp, exist_ok=True)
win_path = os.path.join(win_tmp, "audio.wav")
shutil.copyfile(audio_wav, win_path)

# Write whisper script
w_model = _cf("whisper.model", "medium")
w_compute = _cf("whisper.compute_type", "float16")
script_text = (
    "import json\n"
    "from faster_whisper import WhisperModel\n"
    f"m = WhisperModel('{w_model}', device='cuda', compute_type='{w_compute}')\n"
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

wsl_user = _cf("wsl_user", "zerodaily")
wsl_tmp_win = win_tmp.replace("\\", "/")
wsl_mnt = "/mnt/" + wsl_tmp_win[0].lower() + wsl_tmp_win[2:]
# Copy to WSL
subprocess.run(["wsl", "-e", "bash", "-c", f"cp {wsl_mnt}/audio.wav /tmp/audio.wav"], check=False)
subprocess.run(["wsl", "-e", "bash", "-c", f"cp {wsl_mnt}/_whisper_run.py /tmp/_whisper_run.py"], check=False)

# Run whisper
w_env = _cf("whisper.conda_env", "whisper")
py_bin = f"~/miniconda3/envs/{w_env}/bin/python"
nvidia_base = f"/home/{wsl_user}/miniconda3/envs/{w_env}/lib/python3.10/site-packages/nvidia"
ld = nvidia_base + "/cublas/lib:"
ld += nvidia_base + "/cuda_runtime/lib:"
ld += nvidia_base + "/cuda_nvrtc/lib"
cmd = ["wsl", "-e", "bash", "-c",
       f"export LD_LIBRARY_PATH={ld}:$LD_LIBRARY_PATH && "
       f"cd /tmp && {py_bin} /tmp/_whisper_run.py"]
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