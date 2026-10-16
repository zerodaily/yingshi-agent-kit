#!/usr/bin/env python3
"""build_film_split.py - 长片拆章：把分镜切成多个子合成，宿主只挂载不承载场景。

单文件到 400KB / 4000 个补间时，浏览器 10 秒内建不完时间轴（check 会导航超时）。
拆成每 N 场一个子合成后，宿主页面只保留底板与音轨，每个子合成各自加载与 seek。

用法：
  python build_film_split.py film.json --orientation land --chunk 20 \
      --out index.html --sub-dir compositions
"""
from __future__ import annotations

import argparse
import json
import os

import build_film as bf

SUB_TEMPLATE = """<!doctype html>
<!-- 子合成 {cid}：由 build_film_split.py 生成，勿手改 -->
<html>
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <style>
{css}
      </style>
      <div id="root" data-composition-id="{cid}" data-start="0"
           data-duration="{dur:.3f}" data-width="{w}" data-height="{h}">
{scenes}
      </div>
      <script>
        window.__timelines = window.__timelines || {{}};
        const tl = gsap.timeline({{ paused: true }});
{js}
        window.__timelines["{cid}"] = tl;
      </script>
    </template>
  </body>
</html>
"""

MASTER_TEMPLATE = """<!doctype html>
<!-- 宿主：由 build_film_split.py 生成，勿手改。底板与音轨在这里，场景在 compositions/ 下 -->
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: #4b4335; }}
      #root {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; }}
      .clip {{ position: absolute; inset: 0; overflow: hidden; }}
      .plate {{ position: absolute; inset: 0; background: #d9cfbb; z-index: 0; }}
      .plate-map {{ position: absolute; inset: 0; background-image: url('{map}');
        background-position: {pos}; opacity: {opacity}; mix-blend-mode: multiply;
        filter: sepia(.45) contrast(.92) brightness(1.06) saturate(.55); }}
      .plate-stain {{ position: absolute; mix-blend-mode: multiply; }}
      .plate-stain.a {{ left: -10%; top: 34%; width: 70%; height: 60%;
        background: radial-gradient(closest-side, rgba(126,98,54,.30), rgba(126,98,54,0) 72%); }}
      .plate-stain.b {{ right: -12%; top: -12%; width: 66%; height: 56%;
        background: radial-gradient(closest-side, rgba(104,84,48,.26), rgba(104,84,48,0) 70%); }}
      .plate-vignette {{ position: absolute; inset: 0; box-shadow: inset 0 0 260px rgba(52, 38, 18, .42); }}
      .plate-grain {{ position: absolute; inset: 0; pointer-events: none; opacity: .13; mix-blend-mode: multiply; }}
      .plate-grain::after {{ content: ""; position: absolute; inset: 0;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/></filter><rect width='260' height='260' filter='url(%23n)' opacity='0.6'/></svg>"); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}"
         data-width="{w}" data-height="{h}">
      <audio id="narration" src="{audio}" data-start="0" data-duration="{dur}"></audio>
{bgm}
      <div class="plate" id="plate">
        <div class="plate-map"></div>
        <div class="plate-stain a"></div>
        <div class="plate-stain b"></div>
        <div class="plate-vignette"></div>
        <div class="plate-grain"></div>
      </div>
{hosts}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def chunk_scenes(scenes, size):
    scenes = sorted(scenes, key=lambda s: float(s["start"]))
    out, cur = [], []
    for sc in scenes:
        cur.append(sc)
        if len(cur) >= size:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--orientation", choices=["land", "port"], required=True)
    ap.add_argument("--chunk", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sub-dir", default="compositions")
    args = ap.parse_args()

    cfg = json.load(open(args.film, encoding="utf-8"))

    prev = None
    for i, sc in enumerate(cfg["scenes"]):
        if sc.get("chapter"):
            v = "chapter"
        elif sc.get("variant"):
            v = sc["variant"]
        else:
            has_hero = "hero" in sc.get("cast", {})
            pool = [x for x in (bf.VARIANT_ROTATION if has_hero
                                else ["board", "assembly", "reveal"]) if x != prev] or ["assembly"]
            v = pool[i % len(pool)]
        sc["_variant"] = v
        prev = v

    for i, sc in enumerate(cfg["scenes"]):
        sc["_layout"] = ("chapter" if sc.get("chapter")
                         else bf.LAYOUT_ROTATION[i % len(bf.LAYOUT_ROTATION)])

    out_dir = os.path.dirname(os.path.abspath(args.out))
    sub_dir = os.path.join(out_dir, args.sub_dir)
    os.makedirs(sub_dir, exist_ok=True)

    chunks = chunk_scenes(cfg["scenes"], args.chunk)
    # 宿主槽位不能在同一 track 上重叠：每段的结束时间取下一段的起点
    bases = [min(float(s["start"]) for s in g) for g in chunks]
    film_end = max(float(s["start"]) + float(s["duration"]) for s in cfg["scenes"])
    ends = bases[1:] + [film_end]
    hosts = []
    for k, group in enumerate(chunks):
        cid = "ch%02d" % (k + 1)
        base, end = bases[k], ends[k]
        f = bf.Film(cfg, args.orientation, layout=True)
        f.base = base
        for sc in group:
            f.scene(sc)
        sub = SUB_TEMPLATE.format(
            cid=cid, w=f.w, h=f.h, dur=end - base, css=f.css_block(),
            scenes="\n".join(f.html), js="\n".join(f.js))
        path = os.path.join(sub_dir, cid + ".html")
        open(path, "w", encoding="utf-8").write(sub)
        hosts.append(
            f'      <div id="host-{cid}" data-composition-id="{cid}" '
            f'data-composition-src="{args.sub_dir}/{cid}.html" '
            f'data-start="{base:.3f}" data-duration="{end - base:.3f}" '
            f'data-track-index="1" data-width="{f.w}" data-height="{f.h}"></div>')
        print("  %s  scenes=%2d  %.1f-%s  %.1f KB"
              % (cid, len(group), base, "%.1f" % end, len(sub) / 1024))

    cfg["_orientation_w"] = cfg["canvas"][args.orientation][0]
    w, h = cfg["canvas"][args.orientation]
    plate = cfg["plate"][args.orientation]
    bgm = cfg.get("bgm")
    dur = "%.3f" % float(cfg["duration"])
    master = MASTER_TEMPLATE.format(
        w=w, h=h, dur=dur, audio=cfg["audio"], map=plate["map"],
        pos=plate.get("pos", "50% 45%"), opacity=plate.get("opacity", 0.30),
        bgm=(f'      <audio id="bgm" src="{bgm["src"]}" data-start="0" data-duration="{dur}" '
             f'loop volume="{bgm.get("volume", 0.16)}"></audio>' if bgm else ""),
        hosts="\n".join(hosts))
    open(args.out, "w", encoding="utf-8").write(master)
    print("%s  chunks=%d  %.1f KB" % (args.out, len(chunks), len(master) / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
