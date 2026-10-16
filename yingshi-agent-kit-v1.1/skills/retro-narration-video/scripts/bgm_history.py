#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BGM 使用历史（JSON），替代"扫描项目目录避重"的手工逻辑。

历史文件：<bgm_library>/bgm_history.json
    {"records": [{"project": "xxx", "track": "xxx.mp3", "category": "怀旧", "date": "2026-10-04"}]}

用法：
    python bgm_history.py record --project <项目名> --track <文件名> --category <分类>
    python bgm_history.py recent [--n 5]            # 最近 N 个项目用过的曲目
    python bgm_history.py pick --category <分类> --library <BGM库目录> [--n 5]
        # 从库里按分类随机挑一首，自动避开最近 N 个项目用过的
Select-BGM.ps1 选曲后调 record 登记；选曲前调 pick 拿候选。
"""
import argparse
import json
import os
import random
import sys
import time

try:
    from yingshi_config import load_config, cfg_get, expand
    _CFG = load_config()
except Exception:
    _CFG = {}


def lib_dir():
    return expand(cfg_get(_CFG, "bgm_library", "") if _CFG else "")


def hist_path():
    return os.path.join(lib_dir(), "bgm_history.json")


def load_hist():
    p = hist_path()
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"records": []}


def save_hist(h):
    os.makedirs(os.path.dirname(hist_path()), exist_ok=True)
    with open(hist_path(), "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record")
    r.add_argument("--project", required=True)
    r.add_argument("--track", required=True)
    r.add_argument("--category", default="")

    rn = sub.add_parser("recent")
    rn.add_argument("--n", type=int, default=5)

    p = sub.add_parser("pick")
    p.add_argument("--category", required=True)
    p.add_argument("--n", type=int, default=5)

    args = ap.parse_args()
    h = load_hist()

    if args.cmd == "record":
        h["records"] = [x for x in h["records"] if x.get("track") != args.track]
        h["records"].append({
            "project": args.project,
            "track": args.track,
            "category": args.category,
            "date": time.strftime("%Y-%m-%d"),
        })
        save_hist(h)
        print("已登记：", args.track)

    elif args.cmd == "recent":
        for x in h["records"][-args.n:]:
            print(x["date"], x["project"], x["track"], x.get("category", ""))

    elif args.cmd == "pick":
        libd = lib_dir()
        cands = []
        for root, _, files in os.walk(libd):
            for fn in files:
                if fn.lower().endswith((".mp3", ".wav", ".flac", ".m4a")):
                    rel = os.path.relpath(os.path.join(root, fn), libd)
                    # 分类：按子目录名或文件名关键词匹配
                    if args.category in rel:
                        cands.append(rel)
        if not cands:
            print(f"库里没有分类「{args.category}」的曲目", file=sys.stderr)
            sys.exit(1)
        recent_tracks = {x["track"] for x in h["records"][-args.n:]}
        fresh = [c for c in cands if os.path.basename(c) not in recent_tracks] or cands
        pick = random.choice(fresh)
        print(pick)


if __name__ == "__main__":
    main()
