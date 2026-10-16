#!/usr/bin/env python3
"""make_element_job.py — 把一整个素材目录变成 photo_to_cutout 的 job.json。

用法:
  python make_element_job.py <素材目录> <元素输出目录> [--style archive|design] [--out job.json]

命名的元素自动分角色（见 _classify），plan_scenes.py 会读这个角色。
"""
import argparse
import json
import os
import re

STYLE_PRESETS = {
    "archive": {
        "dot_pitch": 7, "screen_angle": 45, "ink": "#1b1a17", "paper": "#efe7d6",
        "edge": "torn", "edge_strength": 0.085, "density": 0.7, "target_px": 1100,
        "shadow": {"dx": 10, "dy": 12, "blur": 11, "alpha": 0.38},
    },
    "design": {
        "dot_pitch": 8, "screen_angle": 45, "ink": "#141414", "paper": "#f4ead6",
        "edge": "cut", "edge_strength": 0.02, "lip_px": 3, "lip_color": "#f4ead6",
        "density": 0.78, "target_px": 1200,
        "shadow": {"dx": 10, "dy": 12, "blur": 11, "alpha": 0.34},
    },
}

# 名字里带这些词的当人物/地图/碎片，其余按实物（车、产品、硬件）处理
ROLE_RULES = [
    ("portrait", r"ferry|ferdinand|butzi|lyons|founder|portrait|man|person|driver"),
    ("map", r"map|karte|chart|circuit|plan"),
    ("scrap", r"scrap|news|document|paper|letter"),
]


def classify(name: str) -> str:
    low = name.lower()
    for role, pat in ROLE_RULES:
        if re.search(pat, low):
            return role
    return "object"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--style", choices=sorted(STYLE_PRESETS), default="archive")
    ap.add_argument("--out", default=None)
    ap.add_argument("--path-style", choices=["wsl", "win"], default="wsl",
                    help="元素引擎跑在 WSL 里，默认输出 /mnt/c/... 路径")
    args = ap.parse_args()

    def conv(p: str) -> str:
        p = p.replace("\\", "/")
        if args.path_style == "wsl" and len(p) > 1 and p[1] == ":":
            return "/mnt/" + p[0].lower() + p[2:]
        return p

    cfg = dict(STYLE_PRESETS[args.style])
    cfg["out_dir"] = conv(args.out_dir)
    items = []
    for fn in sorted(os.listdir(args.src_dir)):
        if not fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        name = os.path.splitext(fn)[0]
        items.append({
            "src": conv(os.path.join(args.src_dir, fn)),
            "name": name,
            "role": classify(name),
            "matte": "auto",
            "contrast": 1.05,
            "license": "", "credit": "",
        })
    cfg["items"] = items

    out = args.out or os.path.join(args.src_dir, "_element_job.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=1)
    roles = {}
    for it in items:
        roles[it["role"]] = roles.get(it["role"], 0) + 1
    print(f"{out}  素材 {len(items)} 张  角色分布 {roles}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
