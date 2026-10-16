#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共享配图库复用：通用场景（老报纸/旧工厂/街道…）跨项目复用，只给新场景出图。

库目录：config illustration_library（默认 Y:/Projects/自媒体/_配图库）
库结构：
    _配图库/
      library_index.json   # [{key, tags:[...], file, style, used_in:[...]}]
      <key>_2048.png       # 2048 成图

用法：
    python reuse_illustrations.py <项目目录> --prompts prompts.json [--apply]
不加 --apply 只打印匹配报告；加 --apply 把命中的图拷进 <项目>/assets/illustrations/，
并输出 still_needed.json（只剩这些场景需要出图）。
"""
import argparse
import json
import os
import shutil
import sys

try:
    from yingshi_config import load_config, cfg_get, expand
    _CFG = load_config()
except Exception:
    _CFG = {}


def load_index(lib):
    idx_path = os.path.join(lib, "library_index.json")
    if not os.path.exists(idx_path):
        return []
    with open(idx_path, encoding="utf-8") as f:
        return json.load(f)


def score(spec, entry):
    """简单匹配：key 相同得 2 分；tags 命中 prompt 文本每个得 1 分。"""
    s = 0
    if spec.get("key") == entry.get("key"):
        s += 2
    text = (spec.get("prompt") or "") + (spec.get("scene") or "")
    for t in entry.get("tags", []):
        if t and t in text:
            s += 1
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--prompts", default="prompts.json")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--min-score", type=int, default=2)
    args = ap.parse_args()

    lib = expand(cfg_get(_CFG, "illustration_library", "") if _CFG else "")
    index = load_index(lib)
    if not index:
        print(f"配图库为空或不存在：{lib}\n先按 library_index.template.json 建索引。", file=sys.stderr)
        sys.exit(1)

    with open(os.path.join(args.project, args.prompts), encoding="utf-8") as f:
        specs = json.load(f)

    hits, needed = [], []
    for spec in specs:
        ranked = sorted(((score(spec, e), e) for e in index), reverse=True)
        if ranked and ranked[0][0] >= args.min_score:
            hits.append((spec, ranked[0][1], ranked[0][0]))
        else:
            needed.append(spec)

    print(f"共 {len(specs)} 个场景：库命中 {len(hits)}，仍需出图 {len(needed)}")
    for spec, entry, sc in hits:
        print(f"  HIT[{sc}] {spec.get('key')} <- {entry['file']}  (tags={entry.get('tags')})")
    for spec in needed:
        print(f"  NEW  {spec.get('key')}")

    if args.apply and hits:
        ill = os.path.join(args.project, "assets", "illustrations")
        os.makedirs(ill, exist_ok=True)
        for spec, entry, _ in hits:
            src = os.path.join(lib, entry["file"])
            dst = os.path.join(ill, f"{spec['key']}_2048.png")
            if os.path.exists(src):
                shutil.copy2(src, dst)
                entry.setdefault("used_in", []).append(os.path.basename(args.project.rstrip("/\\")))
        # 回写 used_in
        with open(os.path.join(lib, "library_index.json"), "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=1)
        with open(os.path.join(args.project, "still_needed.json"), "w", encoding="utf-8") as f:
            json.dump(needed, f, ensure_ascii=False, indent=1)
        print(f"已复用 {len(hits)} 张；剩余 {len(needed)} 个场景写到 still_needed.json，直接拿去出图")


if __name__ == "__main__":
    main()
