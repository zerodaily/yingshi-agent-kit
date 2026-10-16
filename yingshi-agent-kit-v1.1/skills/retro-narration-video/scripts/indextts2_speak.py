#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分章调用本地 IndexTTS2 生成口播音频。

用法:
    python indextts2_speak.py --chapters audio/chapters.json --ref ref.wav --base .
参数（Gradio /gen_single）:
    --num-beams 2  --max-tokens 200  其余默认（实践推荐值）
产物:
    audio/PartN.wav + audio/timeline.json（含 start/end/duration，按序累计）
   已存在的 PartN.wav 自动跳过（中断可续跑）。
"""
import argparse, json, os, shutil, subprocess, sys, time
import urllib.request

try:
    from yingshi_config import load_config, cfg_get, expand
    _CFG = load_config()
except Exception:
    _CFG = {}


def _cf(key, default):
    return cfg_get(_CFG, key, default) if _CFG else default


def ensure_tts_alive(host, timeout=240):
    """TTS 服务自愈：先 curl 健康检查，死了就尝试用 wsl 拉起，最多等 timeout 秒。

    返回 True=可用，False=仍然不可用（调用方应中止并提示人工检查）。
    """
    health = host.rstrip("/") + "/"
    try:
        urllib.request.urlopen(health, timeout=5)
        return True
    except Exception as e:
        print("TTS not responding (%s), trying to start it..." % e, flush=True)
    tts_dir = expand(_cf("tts.dir", "~/projects/j-indextts2"))
    run_sh = _cf("tts.run_script", "./run_optimized.sh")
    start_cmd = (
        "wsl -d Ubuntu -e bash -lc 'cd %s && exec %s'" % (tts_dir, run_sh)
    )
    print("starting TTS (background):", start_cmd, flush=True)
    try:
        subprocess.Popen(start_cmd, shell=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("failed to launch TTS: %s" % e, file=sys.stderr)
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(10)
        try:
            urllib.request.urlopen(health, timeout=5)
            print("TTS is back.", flush=True)
            return True
        except Exception:
            pass
    print("TTS still down after %ds, abort. Check webui_run.log in %s" % (timeout, tts_dir),
          file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", required=True, help="章节 JSON: [{idx,title,text}]")
    ap.add_argument("--ref", required=True, help="参考口播音频（音色克隆）")
    ap.add_argument("--base", default=".", help="项目根目录（输出到 <base>/audio）")
    ap.add_argument("--host", default=None, help="TTS 服务地址（默认读配置 tts.health_url）")
    ap.add_argument("--num-beams", type=float, default=2)
    ap.add_argument("--max-tokens", type=float, default=200)
    ap.add_argument("--no-auto-start", action="store_true", help="服务挂了也不自动拉起")
    args = ap.parse_args()
    if not args.host:
        args.host = _cf("tts.health_url", "http://127.0.0.1:7860/").rstrip("/")

    if not args.no_auto_start:
        if not ensure_tts_alive(args.host):
            sys.exit(2)

    audio_dir = os.path.join(args.base, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    with open(args.chapters, encoding="utf-8") as f:
        chapters = json.load(f)

    try:
        from gradio_client import Client, handle_file
    except ImportError:
        print("Need gradio_client: pip install gradio_client", file=sys.stderr)
        sys.exit(1)

    client = Client(args.host, verbose=False)
    ffprobe = shutil.which("ffprobe")
    timeline, total_start = [], time.time()

    for ch in chapters:
        idx = ch["idx"]
        out_path = os.path.join(audio_dir, "Part%d.wav" % idx)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
            dur = float(subprocess.check_output([ffprobe, "-v", "error", "-show_entries", "format=duration",
                                                 "-of", "default=noprint_wrappers=1:nokey=1", out_path], text=True).strip())
            print("[CH%d] exists, skip (%.1fs)" % (idx, dur), flush=True)
            timeline.append({"part": idx, "title": ch["title"], "file": out_path, "duration": round(dur, 3), "gen_seconds": 0})
            continue
        t0 = time.time()
        print("[CH%d] generating (%d chars)..." % (idx, len(ch["text"])), flush=True)
        result = client.predict(
            emo_control_method="Same as the voice reference",
            prompt=handle_file(args.ref),
            text=ch["text"],
            emo_ref_path=None, emo_weight=0.65,
            vec1=0.0, vec2=0.0, vec3=0.0, vec4=0.0, vec5=0.0, vec6=0.0, vec7=0.0, vec8=0.0,
            emo_text="", emo_random=False,
            max_text_tokens_per_segment=args.max_tokens,
            param_16=True, param_17=0.8, param_18=30, param_19=0.8,
            param_20=0.0, param_21=args.num_beams, param_22=10.0, param_23=1500,
            api_name="/gen_single",
        )
        src = result.get("value") if isinstance(result, dict) else result
        if isinstance(src, dict):
            src = src.get("path") or src.get("value")
        shutil.copyfile(src, out_path)
        dur = float(subprocess.check_output([ffprobe, "-v", "error", "-show_entries", "format=duration",
                                             "-of", "default=noprint_wrappers=1:nokey=1", out_path], text=True).strip())
        timeline.append({"part": idx, "title": ch["title"], "file": out_path, "duration": round(dur, 3),
                         "gen_seconds": round(time.time() - t0, 1)})
        print("[CH%d] done %.1fs in %.0fs" % (idx, dur, time.time() - t0), flush=True)

    acc = 0.0
    for t in timeline:
        t["start"] = round(acc, 3)
        acc += t["duration"]
        t["end"] = round(acc, 3)
    tl_path = os.path.join(audio_dir, "timeline.json")
    with open(tl_path, "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=1)
    print("ALL DONE %.0fs total audio %.1fs -> %s" % (time.time() - total_start, acc, tl_path))


if __name__ == "__main__":
    main()
