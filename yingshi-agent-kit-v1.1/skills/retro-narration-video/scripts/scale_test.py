#!/usr/bin/env python3
"""scale_test.py — 把一份短分镜扩写成目标时长（默认 10 分钟 / 150 场），
验证长片路径：构建器能不能扛住、变体有没有重复、HTML 有多大。

用法: python scale_test.py film.json --minutes 10 --out-dir /tmp/longfilm
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--scene", type=float, default=4.0, help="每场秒数")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    cfg = json.load(open(args.film, encoding="utf-8"))
    base = cfg["scenes"]
    want = int(args.minutes * 60 / args.scene)
    cycle_keys = ["hero", "scrap", "portrait", "mini", "hero_b"]
    items = [k for k in cycle_keys if any(k in sc.get("cast", {}) for sc in base)]

    # 用原分镜的元素池循环拼场，每 12 场插一张章节卡
    pool = sorted({el for sc in base for el in sc.get("cast", {}).values()})
    scenes = []
    t = 0.0
    for i in range(want):
        if i % 12 == 0 and i > 0:
            scenes.append({
                "id": f"c{i:03d}", "start": round(t, 3), "duration": 3.0,
                "chapter": {"no": f"{i // 12 + 1:02d}", "title": f"第 {i // 12 + 1} 段"},
            })
            t += 3.0
        src = base[i % len(base)]
        cast = {}
        for k in items:
            if k in src.get("cast", {}):
                cast[k] = pool[(i * 3 + hash(k) % 5) % len(pool)]
        sc = {
            "id": f"n{i:03d}", "start": round(t, 3), "duration": args.scene,
            "cast": cast,
            "label1": src.get("label1", {"big": "2024", "small": "DEMO"}),
            "label2": (src.get("label2", "") or "")[:18],
        }
        if i % 3 == 0:
            sc["stamp"] = "档案"
        if i % 4 == 0:
            sc["string"] = ["pinA", "pinB", "pinC"]
        if i % 5 == 0:
            sc["underline"] = True
        scenes.append(sc)
        t += args.scene

    cfg["scenes"] = scenes
    cfg["duration"] = round(t, 3)
    os.makedirs(args.out_dir, exist_ok=True)
    long_film = os.path.join(args.out_dir, "film-long.json")
    with open(long_film, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=1)

    for orient, out in (("land", "index.html"), ("port", "vertical_douyin/index.html")):
        path = os.path.join(args.out_dir, out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run([sys.executable, os.path.join(HERE, "build_film.py"),
                        long_film, "--orientation", orient, "--out", path], check=True)
    print(f"长片测试：{len(scenes)} 场 / {cfg['duration'] / 60:.1f} 分钟 → {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
