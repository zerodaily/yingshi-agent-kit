#!/usr/bin/env python3
"""元素质检：尺寸 / 有效覆盖率 / 平均不透明度 / 平均亮度。"""
import json
import os
import sys

import numpy as np
from PIL import Image


def main(out_dir: str) -> int:
    man = json.load(open(os.path.join(out_dir, "manifest.json"), encoding="utf-8"))
    print(f"{'element':26s} {'size':>12s} {'cov':>6s} {'alpha':>7s} {'lum':>6s}")
    for e in man["elements"]:
        im = Image.open(e["out"]).convert("RGBA")
        arr = np.asarray(im).astype(np.float32)
        a = arr[:, :, 3]
        lum = arr[:, :, :3].mean(axis=2)
        vis = a > 32
        print(
            f"{e['name']:26s} {im.size[0]:5d}x{im.size[1]:<5d} "
            f"{vis.mean():6.3f} {a.mean():7.1f} "
            f"{(lum[vis].mean() if vis.any() else 0):6.1f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
