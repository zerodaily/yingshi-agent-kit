# -*- coding: utf-8 -*-
"""把镜头类型需要的槽位坐标注入 slots_ref.json 与 film.json（两种方向）。"""
import io
import json
import os
import sys

LAND = {
    "hero_fb": {"x": -0.18, "y": -0.06, "w": 1.26},
    "duo_l": {"x": 0.02, "y": 0.24, "w": 0.45},
    "duo_r": {"x": 0.53, "y": 0.24, "w": 0.45},
    "hero_num": {"x": 0.44, "y": 0.26, "w": 0.50},
    "wall1": {"x": 0.03, "y": 0.08, "w": 0.30},
    "wall2": {"x": 0.36, "y": 0.14, "w": 0.27},
    "wall3": {"x": 0.12, "y": 0.52, "w": 0.31},
    "wall4": {"x": 0.56, "y": 0.46, "w": 0.26},
    "hero_tl": {"x": 0.05, "y": 0.42, "w": 0.30},
    "mini_tl": {"x": 0.64, "y": 0.44, "w": 0.28},
    "quote_por": {"x": 0.04, "y": 0.10, "w": 0.42},
    "label1_fb": {"x": 0.05, "y": 0.06},
    "label2_fb": {"x": 0.58, "y": 0.86},
    "label1_num": {"x": 0.05, "y": 0.74},
}

PORT = {
    "hero_fb": {"x": -0.20, "y": 0.10, "w": 1.32},
    "duo_l": {"x": 0.03, "y": 0.16, "w": 0.45},
    "duo_r": {"x": 0.52, "y": 0.16, "w": 0.45},
    "hero_num": {"x": 0.08, "y": 0.40, "w": 0.84},
    "wall1": {"x": 0.03, "y": 0.06, "w": 0.44},
    "wall2": {"x": 0.52, "y": 0.10, "w": 0.42},
    "wall3": {"x": 0.06, "y": 0.40, "w": 0.42},
    "wall4": {"x": 0.52, "y": 0.44, "w": 0.38},
    "hero_tl": {"x": 0.04, "y": 0.38, "w": 0.44},
    "mini_tl": {"x": 0.54, "y": 0.44, "w": 0.40},
    "quote_por": {"x": 0.08, "y": 0.06, "w": 0.62},
    "label1_fb": {"x": 0.06, "y": 0.03},
    "label2_fb": {"x": 0.06, "y": 0.80},
    "label1_num": {"x": 0.06, "y": 0.72},
}


def main(project):
    for fn in ("slots_ref.json", "film.json"):
        path = os.path.join(project, fn)
        if not os.path.exists(path):
            continue
        d = json.load(io.open(path, encoding="utf-8"))
        d["slots"]["land"].update(LAND)
        d["slots"]["port"].update(PORT)
        json.dump(d, io.open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("injected ->", fn, len(d["slots"]["land"]), "land slots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
