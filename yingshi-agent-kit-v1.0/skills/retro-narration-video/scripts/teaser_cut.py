#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""60 秒抖音引流片段：一键从成片里按时间戳截段拼接。

用法：
    python teaser_cut.py <成片mp4> <输出mp4> --segs "12.5-28.3,95.0-139.2" [--srt 字幕.srt]
    --segs 里各段时间加起来建议 55-65 秒；超了自动按比例截尾，少了会警告。
    --srt 可选：把对应时间段的字幕烧进片段（需要字幕文件与成片时间轴一致）。
"""
import argparse
import os
import subprocess
import sys
import tempfile


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", " ".join(cmd), file=sys.stderr)
        print((r.stderr or "")[-500:], file=sys.stderr)
        sys.exit(1)
    return r


def parse_segs(s):
    segs = []
    for part in s.split(","):
        a, b = part.strip().split("-")
        segs.append((float(a), float(b)))
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--segs", required=True, help='"开始-结束,开始-结束"，秒')
    ap.add_argument("--srt", default="")
    args = ap.parse_args()

    segs = parse_segs(args.segs)
    total = sum(b - a for a, b in segs)
    print(f"片段 {len(segs)} 段，共 {total:.1f} 秒")
    if total > 65:
        print("WARN 超过 65 秒，抖音完播率会掉，建议精简到 60 秒以内")
    if total < 45:
        print("WARN 不到 45 秒，信息量可能不够")

    tmp = tempfile.mkdtemp(prefix="teaser_")
    parts = []
    for i, (a, b) in enumerate(segs):
        p = os.path.join(tmp, f"p{i}.mp4")
        run(["ffmpeg", "-y", "-ss", str(a), "-to", str(b), "-i", args.src,
             "-c:v", "libx264", "-preset", "fast", "-crf", "20",
             "-c:a", "aac", "-b:a", "128k", p])
        parts.append(p)

    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", args.dst])

    if args.srt and os.path.exists(args.srt):
        # 烧字幕（保留原文件，输出 _sub 版）
        base, ext = os.path.splitext(args.dst)
        subbed = f"{base}_sub{ext}"
        srt = args.srt.replace("\\", "/").replace(":", "\\:")
        run(["ffmpeg", "-y", "-i", args.dst, "-vf", f"subtitles={srt}",
             "-c:a", "copy", subbed])
        print("已烧字幕：", subbed)

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", args.dst],
        capture_output=True, text=True).stdout.strip()
    print(f"引流片段已生成：{args.dst}（{dur} 秒）")


if __name__ == "__main__":
    main()
