#!/usr/bin/env python3
"""photo_to_cutout.py — 真实照片 → 档案拼贴元素（半调剪影）

一套代码同时服务「档案调查拼贴」和「设计拼贴」两个画风包：
  照片 → 抠图 → 半调网点（带印刷网角）→ 双色调上纸 → 撕边/裁切 → 纸纤维颗粒 → 透明 PNG

用法（WSL，wan2gp 环境里有 rembg / numpy / Pillow）：
  ~/miniconda3/envs/wan2gp/bin/python photo_to_cutout.py job.json

job.json:
{
  "out_dir": "/path/to/elements",
  "dot_pitch": 7,              // 网点栅格边长（px，成品尺寸下）
  "screen_angle": 45,          // 印刷网角
  "ink": "#1b1a17",            // 墨色
  "paper": "#efe7d6",          // 纸色
  "edge": "torn",              // torn | cut
  "edge_strength": 0.09,       // 撕边抖动强度
  "target_px": 1200,           // 元素长边目标像素
  "items": [
    {"src": "/path/a.jpg", "name": "erik_carlsson", "matte": "auto", "gamma": 1.1, "contrast": 1.15}
  ]
}

matte: auto = rembg 抠图（失败自动降级为矩形照片碎片）；none = 不抠，整张照片做成碎片
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


# ---------------------------------------------------------------- 基础工具

def hex_rgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def blur_l(img: Image.Image, radius: float) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius)) if radius > 0 else img


def cover_rgb(img: Image.Image) -> Image.Image:
    return img.convert("RGB") if img.mode != "RGB" else img


def fit_long_edge(img: Image.Image, target: int) -> Image.Image:
    w, h = img.size
    longest = max(w, h)
    if longest <= target:
        return img
    scale = target / longest
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


# ---------------------------------------------------------------- 抠图

_REMBG_SESSION = None


def rembg_alpha(rgb: Image.Image) -> Image.Image | None:
    """返回 L 掩膜（255=主体）；不可用或失败返回 None。"""
    global _REMBG_SESSION
    try:
        from rembg import new_session, remove
    except Exception as exc:  # noqa: BLE001
        print(f"  ! rembg 不可用（{exc}），降级为矩形照片碎片")
        return None
    try:
        if _REMBG_SESSION is None:
            _REMBG_SESSION = new_session("u2net")
        out = remove(rgb, session=_REMBG_SESSION, only_mask=True)
        return out.convert("L")
    except Exception as exc:  # noqa: BLE001
        print(f"  ! rembg 抠图失败（{exc}），降级为矩形照片碎片")
        return None


def refine_alpha(alpha: Image.Image, floor: int = 96) -> Image.Image:
    """去掉半透明毛边，把掩膜推向硬边。"""
    a = np.asarray(alpha).astype(np.float32) / 255.0
    a = np.clip((a - 0.35) / 0.30, 0.0, 1.0)
    return Image.fromarray((a * 255).astype(np.uint8), "L")


# ---------------------------------------------------------------- 半调

def half_tone(ink_cov: Image.Image, pitch: int, angle: float) -> Image.Image:
    """ink_cov: L 图，255=满墨。返回同尺寸 L 网点图（255=着墨）。"""
    pitch = max(3, int(pitch))
    w, h = ink_cov.size

    # 旋转到网角坐标系，按栅格取单元均值，画点后再旋转回来
    rot = ink_cov.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=0)
    rw, rh = rot.size
    cols, rows = max(1, rw // pitch), max(1, rh // pitch)
    cell = np.asarray(
        rot.resize((cols, rows), Image.BOX), dtype=np.float32
    ) / 255.0

    ss = 2  # 超采样倍率
    dots = Image.new("L", (cols * pitch * ss, rows * pitch * ss), 0)
    draw = ImageDraw.Draw(dots)
    cx, cy = pitch * ss / 2.0, pitch * ss / 2.0
    rmax = pitch * ss * 0.5 * 1.15  # 暗部才让相邻点相接
    for j in range(rows):
        for i in range(cols):
            v = float(cell[j, i])
            if v <= 0.02:
                continue
            r = rmax * math.sqrt(min(1.0, v))
            x = i * pitch * ss + cx
            y = j * pitch * ss + cy
            draw.ellipse((x - r, y - r, x + r, y + r), fill=255)
    dots = dots.resize((cols * pitch, rows * pitch), Image.LANCZOS)

    back = dots.rotate(-angle, expand=True, resample=Image.BICUBIC, fillcolor=0)
    bw, bh = back.size
    left = max(0, (bw - w) // 2)
    top = max(0, (bh - h) // 2)
    back = back.crop((left, top, left + w, top + h))
    return back


def rect_mask(size: tuple[int, int], margin_frac: float = 0.022) -> Image.Image:
    """矩形碎片掩膜：留出内缩边距，好让撕边发生在画面内。"""
    w, h = size
    m = max(6, int(max(w, h) * margin_frac))
    mask = Image.new("L", (w, h), 0)
    mask.paste(255, (m, m, max(m + 1, w - m), max(m + 1, h - m)))
    return mask


def ink_coverage(rgb: Image.Image, gamma: float, contrast: float,
                 stretch: bool = True, density: float = 1.0) -> Image.Image:
    """照片 → 墨量（暗处多墨）。做一次印刷用的对比压缩。"""
    gray = rgb.convert("L")
    if stretch:
        # 老照片/旧地图普遍发白，先按百分位拉伸，否则网点几乎印不出来
        arr = np.asarray(gray, dtype=np.float32)
        lo, hi = np.percentile(arr, 2), np.percentile(arr, 98)
        if hi - lo > 8:
            arr = np.clip((arr - lo) / (hi - lo), 0, 1) * 255.0
            gray = Image.fromarray(arr.astype(np.uint8), "L")
    lum = np.asarray(gray, dtype=np.float32) / 255.0
    cov = 1.0 - lum
    cov = np.clip((cov - 0.5) * contrast + 0.5, 0.0, 1.0)
    cov = np.power(cov, max(0.05, gamma))
    cov = np.clip(cov * density, 0.0, 1.0)
    return Image.fromarray((cov * 255).astype(np.uint8), "L")


# ---------------------------------------------------------------- 边缘

def torn_mask(mask: Image.Image, wobble_px: float, seed: int) -> Image.Image:
    """把掩膜边界抖成手撕/手剪的边：近似有符号距离场 + 平滑噪声位移。

    wobble_px = 边界抖动幅度（像素）。剪裁 1px，手撕 3~5px。
    """
    hard = np.asarray(mask, dtype=np.float32) / 255.0
    sigma = max(2.0, wobble_px * 1.5)

    base = np.asarray(blur_l(mask, sigma), dtype=np.float32) / 255.0
    dist = (base - 0.5) * sigma / 0.4          # 近似有符号距离（px）

    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(hard.shape).astype(np.float32)
    noise_img = Image.fromarray(
        np.clip((noise * 0.25 + 0.5) * 255, 0, 255).astype(np.uint8), "L"
    )
    noise = np.asarray(blur_l(noise_img, sigma), dtype=np.float32) / 255.0 * 8.0 - 4.0
    noise = np.clip(noise, -1.0, 1.0)

    edge = np.clip(0.5 + (dist + noise * wobble_px) / max(0.6, wobble_px * 0.35), 0.0, 1.0)
    return Image.fromarray((edge * 255).astype(np.uint8), "L")


def paper_grain(size: tuple[int, int], seed: int, amount: float = 10.0) -> Image.Image:
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((size[1], size[0])).astype(np.float32) * amount + 128.0
    return Image.fromarray(np.clip(n, 0, 255).astype(np.uint8), "L")


def bake_shadow(piece: Image.Image, mask: Image.Image, dx: int, dy: int,
                blur: float, alpha: float, color: str = "#2a1e0e") -> Image.Image:
    """把投影烘进 PNG。

    长片里 150+ 个画面各带 CSS `filter: drop-shadow`，会被 HyperFrames 判为
    「重叠加层过多」，存在捕捉出黑帧的风险。烘进图片后每个元素只剩一个 <img>。
    """
    w, h = piece.size
    pad_x, pad_y = int(dx + blur * 2), int(dy + blur * 2)
    size = (w + pad_x, h + pad_y)

    sh = Image.new("L", size, 0)
    sh.paste(mask, (max(0, dx), max(0, dy)))
    sh = blur_l(sh, blur)
    sh = sh.point(lambda v: int(v * alpha))
    shadow = Image.new("RGB", size, hex_rgb(color))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(shadow, (0, 0), sh)
    out.alpha_composite(piece, (0, 0))
    return out


# ---------------------------------------------------------------- 主流程

def make_element(cfg: dict, global_cfg: dict, index: int) -> dict:
    name = cfg["name"]
    src = cfg["src"]
    print(f"[{index}] {name} <- {src}")

    base = cover_rgb(Image.open(src))
    base = fit_long_edge(base, int(global_cfg.get("target_px", 1200)))
    w, h = base.size

    matte_mode = cfg.get("matte", "auto")
    alpha = None
    if matte_mode == "auto":
        alpha = rembg_alpha(base)
        if alpha is not None:
            alpha = fit_long_edge(alpha.convert("L"), max(w, h))
            alpha = refine_alpha(alpha)
            print("  抠图 ok")

    if alpha is None:
        alpha = rect_mask((w, h))                    # 整张照片当撕下的碎片
    else:
        # 裁到主体外扩 4%
        box = alpha.getbbox()
        if box:
            pad = int(max(w, h) * 0.04)
            box = (
                max(0, box[0] - pad), max(0, box[1] - pad),
                min(w, box[2] + pad), min(h, box[3] + pad),
            )
            base = base.crop(box)
            alpha = alpha.crop(box)
            w, h = base.size

    c = cfg.get("contrast", 1.15) + global_cfg.get("contrast_bias", 0.0)
    g = cfg.get("gamma", 1.0) * global_cfg.get("gamma_bias", 1.0)
    stretch = bool(cfg.get("stretch", global_cfg.get("stretch", True)))
    density = float(cfg.get("density", global_cfg.get("density", 1.0)))
    cov = ink_coverage(base, g, c, stretch=stretch, density=density)
    dots = half_tone(cov, int(global_cfg.get("dot_pitch", 7)),
                     float(global_cfg.get("screen_angle", 45)))

    edge = global_cfg.get("edge", "torn")
    strength = float(global_cfg.get("edge_strength", 0.09))
    wobble_px = 1.0 if edge == "cut" else max(1.0, strength * 40.0)
    mask = torn_mask(alpha, wobble_px, seed=1000 + index)

    ink = Image.new("RGB", (w, h), hex_rgb(global_cfg.get("ink", "#1b1a17")))
    paper = Image.new("RGB", (w, h), hex_rgb(global_cfg.get("paper", "#efe7d6")))

    piece = Image.composite(ink, paper, dots)                  # 纸上印网点
    grain = paper_grain((w, h), seed=2000 + index, amount=8.0)
    piece = Image.blend(piece, Image.merge("RGB", (grain, grain, grain)), 0.06)

    # 纸边高光：沿裁切边留一圈更浅的纸色，做出撕口的纸纤维与厚度感
    lip = int(cfg.get("lip_px", global_cfg.get("lip_px", 2 if edge == "cut" else 3)))
    lip_color = cfg.get("lip_color", global_cfg.get("lip_color", "#fdf8ec"))
    eroded = mask.filter(ImageFilter.MinFilter(lip * 2 + 1))
    ring = ImageChops.subtract(mask, eroded)
    piece = Image.composite(Image.new("RGB", (w, h), hex_rgb(lip_color)), piece, ring)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(piece, (0, 0), mask)

    sh_cfg = cfg.get("shadow", global_cfg.get("shadow"))
    if sh_cfg:
        out = bake_shadow(
            out, mask,
            dx=int(sh_cfg.get("dx", 8)), dy=int(sh_cfg.get("dy", 10)),
            blur=float(sh_cfg.get("blur", 10)), alpha=float(sh_cfg.get("alpha", 0.38)),
            color=sh_cfg.get("color", "#2a1e0e"),
        )

    out_dir = global_cfg["out_dir"]
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.png")
    out.save(path)
    print(f"  -> {path}  ({w}x{h})")
    return {"name": name, "src": src, "out": path, "size": [w, h],
            "matted": alpha is not None and matte_mode == "auto",
            "license": cfg.get("license", ""), "credit": cfg.get("credit", "")}


def contact_sheet(items: list[dict], out_path: str, cell: int = 420) -> None:
    cols = min(3, max(1, len(items)))
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGB", (cols * cell, rows * cell), (120, 118, 112))
    for i, it in enumerate(items):
        im = Image.open(it["out"]).convert("RGBA")
        im.thumbnail((cell - 40, cell - 40), Image.LANCZOS)
        bg = Image.new("RGBA", (cell, cell), (120, 118, 112, 255))
        bg.alpha_composite(im, ((cell - im.width) // 2, (cell - im.height) // 2))
        sheet.paste(bg.convert("RGB"), ((i % cols) * cell, (i // cols) * cell))
    sheet.save(out_path)
    print(f"contact sheet -> {out_path}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    man_path = os.path.join(cfg["out_dir"], "manifest.json")
    os.makedirs(cfg["out_dir"], exist_ok=True)
    existing: list[dict] = []
    if os.path.exists(man_path):
        with open(man_path, "r", encoding="utf-8") as fh:
            existing = json.load(fh).get("elements", [])

    fresh = [make_element(it, cfg, i + 1) for i, it in enumerate(cfg["items"])]
    by_name = {e["name"]: e for e in existing}
    for e in fresh:
        by_name[e["name"]] = e
    manifest = list(by_name.values())
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump({"elements": manifest}, fh, ensure_ascii=False, indent=2)
    contact_sheet(manifest, os.path.join(cfg["out_dir"], "_contact_sheet.png"))
    print(f"manifest -> {man_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
