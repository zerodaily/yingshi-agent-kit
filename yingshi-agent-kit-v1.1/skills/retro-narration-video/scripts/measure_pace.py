#!/usr/bin/env python3
"""量一下现有产线的真实语速：字数 / 时长 → 字每秒，用来把「目标字数」换算成时长与画面数。"""
import glob
import json
import os
import re
import statistics
import subprocess
import sys


def probe(path: str) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, check=True).stdout.strip()
        return float(out)
    except Exception:  # noqa: BLE001
        return 0.0


def main(root: str) -> int:
    rows = []
    for d in sorted(glob.glob(os.path.join(root, "2026*")))[-14:]:
        ch = os.path.join(d, "audio", "chapters.json")
        au = os.path.join(d, "口播拼接.wav")
        if not (os.path.exists(ch) and os.path.exists(au)):
            continue
        try:
            data = json.load(open(ch, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        text = "".join(c.get("text", "") for c in data if isinstance(c, dict))
        body = re.sub(r"\s+", "", text)
        dur = probe(au)
        if dur:
            rows.append((os.path.basename(d), len(body), dur, len(body) / dur))

    print(f"{'project':40s} {'chars':>6s} {'sec':>8s} {'chars/s':>8s}")
    for name, n, dur, rate in rows:
        print(f"{name[:38]:40s} {n:6d} {dur:8.1f} {rate:8.2f}")
    if not rows:
        print("没有找到可统计的项目")
        return 1

    rate = statistics.mean([r[3] for r in rows])
    print(f"\n平均语速 {rate:.2f} 字/秒（样本 {len(rows)} 集）")
    for target in (1500, 3000, 4000, 5000):
        sec = target / rate
        print(f"{target:5d} 字 → {sec/60:5.1f} 分钟 | 4 秒/画面 = {sec/4:4.0f} 个画面 "
              f"| 6 秒/画面 = {sec/6:4.0f} 个画面")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else r"Y:\Projects\自媒体"))
