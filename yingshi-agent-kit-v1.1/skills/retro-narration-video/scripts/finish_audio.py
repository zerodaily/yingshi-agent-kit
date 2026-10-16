# -*- coding: utf-8 -*-
"""把 Part1..N 拼成口播拼接.wav，并按章节表算出时间轴。
用法: python finish_audio.py <项目目录>
"""
import json
import os
import subprocess
import sys


def probe(path):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True).stdout)


def main(project):
    audio = os.path.join(project, "audio")
    parts = sorted(
        (f for f in os.listdir(audio) if f.startswith("Part") and f.endswith(".wav")),
        key=lambda s: int("".join(ch for ch in s if ch.isdigit()) or 0))
    if not parts:
        raise SystemExit("no Part*.wav in " + audio)
    outs = os.path.join(audio, "口播拼接.wav")
    args = ["ffmpeg", "-y"]
    for p in parts:
        args += ["-i", p]
    n = len(parts)
    chain = "".join("[%d:a]" % i for i in range(n)) + "concat=n=%d:v=0:a=1[a]" % n
    args += ["-filter_complex", chain, "-map", "[a]", "-c:a", "pcm_s16le", outs]
    subprocess.run(args, cwd=audio, check=True)
    dur = probe(outs)
    print("concat done: %.2fs from %d parts" % (dur, n))
    root_copy = os.path.join(project, "口播拼接.wav")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Copy-Item -LiteralPath '%s' -Destination '%s' -Force" % (outs, root_copy)],
                   check=True)
    chapters = json.load(open(os.path.join(audio, "chapters.json"), encoding="utf-8"))
    t = 0.0
    tl = []
    for i, c in enumerate(chapters):
        d = probe(os.path.join(audio, "Part%d.wav" % (i + 1)))
        tl.append({"part": i + 1, "title": c.get("title", ""), "duration": round(d, 3),
                   "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    json.dump(tl, open(os.path.join(audio, "timeline.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("timeline written, total %.2fs" % t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
