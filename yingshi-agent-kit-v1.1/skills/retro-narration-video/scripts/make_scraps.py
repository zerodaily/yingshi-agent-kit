#!/usr/bin/env python3
"""从档案底图上裁几块纸片，作为拼贴的底衬碎片。

用法：
  python make_scraps.py                      # 默认：包 A 的波罗的海海图
  python make_scraps.py <底图> <输出目录> <前缀>
"""
import os
import sys

from PIL import Image

DEFAULT_SRC = ("/mnt/c/Users/jonny/Documents/Codex/2026-10-05/"
               "context-md-brief-md-skill-references/work/collage-style-kit/"
               "assets/source/baltic_chart_basemap.jpg")
DEFAULT_OUT = ("/mnt/c/Users/jonny/Documents/Codex/2026-10-05/"
               "context-md-brief-md-skill-references/work/collage-style-kit/"
               "assets/source")

# (name, left%, top%, right%, bottom%)
CROPS = [
    ("a", 0.02, 0.06, 0.46, 0.52),
    ("b", 0.52, 0.30, 0.96, 0.78),
    ("c", 0.18, 0.58, 0.62, 0.96),
]


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    prefix = sys.argv[3] if len(sys.argv) > 3 else "scrap_chart_"
    im = Image.open(src).convert("RGB")
    w, h = im.size
    for name, l, t, r, b in CROPS:
        box = (int(l * w), int(t * h), int(r * w), int(b * h))
        piece = im.crop(box)
        piece = piece.resize((min(1100, piece.width), int(min(1100, piece.width) * piece.height / piece.width)), Image.LANCZOS)
        path = os.path.join(out, f"{prefix}{name}.jpg")
        piece.save(path, quality=92)
        print(f"{path} {piece.size}")


if __name__ == "__main__":
    main()
