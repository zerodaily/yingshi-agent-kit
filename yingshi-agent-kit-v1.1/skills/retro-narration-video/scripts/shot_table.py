#!/usr/bin/env python3
"""shot_table.py - 把 film.json 的镜头规格导成一张可读的表（分镜审查用）。

用法: python shot_table.py film.json out.md [行数]
"""
import io
import json
import sys


def main(film_path, out_path, limit=60):
    d = json.load(io.open(film_path, encoding="utf-8"))
    rows = [s for s in d["scenes"] if s.get("_shot")]
    lines = ["# 镜头表", "",
             "| # | 入点 | 时长 | 景别 | 机位 | 运动 | 构图 | 转场 | 标签 | 画面文字 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, s in enumerate(rows[:limit]):
        sh = s["_shot"]
        t = "%d:%02d" % (int(s["start"]) // 60, int(s["start"]) % 60)
        lab = (s.get("label1") or {}).get("big", "")
        lines.append("| %d | %s | %.1fs | %s | %s | %s | %s | %s | %s | %s |"
                     % (i + 1, t, s["duration"], sh["scale"], sh["angle"], sh["move"],
                        sh["comp"], sh["trans"], lab, (s.get("label2") or "")[:14]))
    io.open(out_path, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote %s (%d rows of %d shots)" % (out_path, min(limit, len(rows)), len(rows)))
    return 0


if __name__ == "__main__":
    lim = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    raise SystemExit(main(sys.argv[1], sys.argv[2], lim))
