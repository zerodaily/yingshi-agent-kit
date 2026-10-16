#!/usr/bin/env python3
"""成片抽帧质检：逐秒平均亮度 / 对比度 / 非纸面像素占比，顺便拼一张接触板。

用法: python qa_frames.py <video.mp4> <out_dir>
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw


def main(video: str, out_dir: str, every: float = 1.0, scale: int = 0) -> int:
    raw = os.path.join(out_dir, "_frames")
    os.makedirs(raw, exist_ok=True)
    vf = f"fps=1/{every}" if every > 1 else "fps=1"
    if scale:
        vf += f",scale={scale}:-2"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", video,
         "-vf", vf, os.path.join(raw, "f_%04d.png")],
        check=True,
    )
    files = sorted(f for f in os.listdir(raw) if f.endswith(".png"))
    print(f"{'t':>4s} {'mean':>7s} {'std':>7s} {'ink<110':>8s} {'paper>200':>10s}")
    tiles = []
    for i, name in enumerate(files):
        im = Image.open(os.path.join(raw, name)).convert("RGB")
        g = np.asarray(im.convert("L"), dtype=np.float32)
        print(f"{i * every:7.1f} {g.mean():7.1f} {g.std():7.1f} "
              f"{(g < 110).mean():8.3f} {(g > 200).mean():10.3f}")
        im.thumbnail((470, 470), Image.LANCZOS)
        tiles.append((i, im))

    cols, cell = 4, 480
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (26, 26, 26))
    draw = ImageDraw.Draw(sheet)
    for i, im in tiles:
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + 5, y + 5))
        draw.text((x + 14, y + 14), f"{i}s", fill=(255, 230, 120))
    path = os.path.join(out_dir, "contact_sheet.jpg")
    sheet.save(path, quality=88)
    print(f"contact sheet -> {path}")
    return 0


if __name__ == "__main__":
    every = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    scale = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    raise SystemExit(main(sys.argv[1], sys.argv[2], every, scale))
