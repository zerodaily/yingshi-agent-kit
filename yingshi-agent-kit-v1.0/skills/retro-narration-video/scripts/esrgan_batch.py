#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量 Real-ESRGAN x4 放大：<项目>/assets/illustrations/*_512.png -> *_2048.png。

用法（Windows）：
    python esrgan_batch.py <项目目录> [--model realesrgan-x4plus] [--force]
已有 *_2048.png 且源文件未变更时自动跳过（中断可续跑）。
"""
import argparse
import glob
import os
import subprocess
import sys

try:
    from yingshi_config import load_config, cfg_get, expand
    _CFG = load_config()
except Exception:
    _CFG = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--model", default="realesrgan-x4plus")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    exe = expand(cfg_get(_CFG, "esrgan_exe", "") if _CFG else "")
    if not exe or not os.path.exists(exe):
        print(f"找不到 ESRGAN 可执行文件：{exe}\n请在 skill config.json 里配置 esrgan_exe", file=sys.stderr)
        sys.exit(1)

    ill = os.path.join(args.project, "assets", "illustrations")
    srcs = sorted(glob.glob(os.path.join(ill, "*_512.png")))
    if not srcs:
        print(f"{ill} 里没有 *_512.png", file=sys.stderr)
        sys.exit(1)
    print(f"共 {len(srcs)} 张待放大")
    for s in srcs:
        d = s[:-8] + "_2048.png"  # *_512.png -> *_2048.png
        if os.path.exists(d) and not args.force and os.path.getmtime(d) >= os.path.getmtime(s):
            print("skip", os.path.basename(d))
            continue
        r = subprocess.run([exe, "-i", s, "-o", d, "-n", args.model, "-s", "4"],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(d):
            print("FAILED", os.path.basename(s), (r.stderr or "")[-200:], file=sys.stderr)
            sys.exit(1)
        print("done", os.path.basename(d))
    print("全部放大完成")


if __name__ == "__main__":
    main()
