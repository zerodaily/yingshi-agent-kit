#!/usr/bin/env python3
"""split_film.py - 把整片分镜切成两半（长片单页渲染容易卡死，分半更稳）。
用法: python split_film.py <项目目录> <切点秒>
"""
import io
import json
import os
import sys


def main(proj, mid=353.0):
    d = json.load(io.open(os.path.join(proj, "film_story_full.json"), encoding="utf-8"))
    for tag, lo, hi in (("a", 0.0, mid), ("b", mid, 900.0)):
        sc = []
        for s in d["scenes"]:
            st, en = s["start"], s["start"] + s["duration"]
            if en <= lo + 0.01 or st >= hi - 0.01:
                continue
            n = dict(s)
            n["start"] = round(max(st, lo) - lo, 3)
            n["duration"] = round(min(en, hi) - max(st, lo), 3)
            if n["duration"] > 0.5:
                sc.append(n)
        out = dict(d)
        out["scenes"] = sc
        out["audio"] = "口播混音.wav"
        out["duration"] = round(sum(x["duration"] for x in sc), 3)
        json.dump(out, io.open(os.path.join(proj, "film_half_%s.json" % tag), "w",
                               encoding="utf-8"), ensure_ascii=False, indent=1)
        print("%s: %d scenes, %.1fs" % (tag, len(sc), out["duration"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 353.0))
