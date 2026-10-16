#!/usr/bin/env python3
"""build_film.py — 把场景 JSON 生成 HyperFrames 分层舞台工程（横屏或竖屏）。

用法：
  python build_film.py film.json --orientation land --out index.html
  python build_film.py film.json --orientation port --out vertical_douyin/index.html

设计要点：
- 底板（旧纸 + 档案图 + 污渍 + 颗粒 + 暗角）挂在 root 下、所有 clip 之上，
  全片共用一张纸，场景之间只换拼贴元素。
- 每个场景是一个 .clip，元素按「碎片 → 主图 → 人物 → 胶带 → 标签 → 印章 → 图钉红绳 → 下划线」
  的顺序落位，全部走 steps() 定格缓动。
- 场景结束前 0.24 秒主图向左滑出并淡出；下一场主图从右侧滑入，方向一致（不违反矢量律）。
- 长场景在 50% 处追加一个 late 元素，避免出现「画面在等人」的空转。
"""
from __future__ import annotations

import argparse
import json
import math
import os

try:
    import shotgram
except Exception:  # noqa: BLE001
    shotgram = None

try:
    import devices
except Exception:  # noqa: BLE001
    devices = None

try:
    import props as props_mod
except Exception:  # noqa: BLE001
    props_mod = None


def px(v: float, base: int) -> int:
    return int(round(v * base))


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# 场景变体：同样是「碎片 + 主图 + 标签」，靠落点与入场方向轮换，避免 150 个画面长得一样。
# 每个变体只重映射槽位，不改元素数量——场景给什么就摆什么。
VARIANT_SLOTS = {
    "assembly": {"hero": "hero1", "scrap": "scrap1", "portrait": "portrait1", "mini": "mini1"},
    "reveal":   {"hero": "hero2", "scrap": "scrap2", "portrait": "portrait2", "mini": "mini2"},
    "wide":     {"hero": "hero3", "scrap": "scrap1", "portrait": "portrait1", "mini": "mini2"},
    "left":     {"hero": "hero_l", "scrap": "scrap3", "portrait": "portrait2", "mini": "mini1"},
    "board":    {"hero": "hero2", "scrap": "scrap1", "portrait": "portrait1", "mini": "mini1"},
    "document": {"hero": "mini2", "scrap": "scrap3", "portrait": "portrait1", "mini": "mini1"},
}

# 变体改入场方向与事件次序：先落碎片还是先落主图，读起来是两种节奏
VARIANT_FIRST = {"assembly": "scrap", "reveal": "hero", "wide": "hero",
                 "left": "scrap", "board": "scrap", "document": "scrap"}

VARIANT_ROTATION = ["assembly", "reveal", "wide", "left", "board", "assembly", "reveal", "wide"]

# ---- 场景类型（镜头语言）--------------------------------------------------
# 光换元素落点还是会单调，长片必须换「镜头」：满幅、双联、巨数字、照片墙、年表、
# 文献、引语。每种类型用不同的槽位组合与不同的版式，与上面的变体正交。
LAYOUT_ROTATION = ["stage", "stage", "fullbleed", "stage", "duo", "stage",
                   "bignum", "stage", "wall", "stage", "timeline", "stage",
                   "document", "stage", "quote"]

# 三种纸色轮换，避免整片同一张纸
PLATE_TONES = [
    ("warm", "#d9cfbb", 0.30),
    ("pale", "#e6ddc9", 0.22),
    ("grey", "#cfc7b6", 0.34),
]

# 每种镜头类型给不同的槽位：照片落点、大小、出血方式都不一样
LAYOUT_SLOTS = {
    "fullbleed": {"hero": "hero_fb", "scrap": "scrap2", "portrait": "mini2",
                  "mini": "mini1", "label1": "label1_fb", "label2": "label2_fb"},
    "duo":       {"hero": "duo_l", "mini": "duo_r", "portrait": "mini2",
                  "scrap": "scrap3", "label1": "label1_fb", "label2": "label2_fb"},
    "bignum":    {"hero": "hero_num", "scrap": "scrap3", "mini": "mini2",
                  "portrait": "portrait2", "label1": "label1_num", "label2": "label2"},
    "wall":      {"hero": "wall1", "mini": "wall2", "hero_b": "wall3",
                  "portrait": "wall4", "scrap": "scrap2", "label1": "label1_fb"},
    "timeline":  {"hero": "hero_tl", "mini": "mini_tl", "portrait": "mini2",
                  "scrap": "scrap2", "label1": "label1_num", "label2": "label2_fb"},
    "quote":     {"portrait": "quote_por", "hero": "mini2", "mini": "mini1",
                  "scrap": "scrap2", "label1": "label1_fb", "label2": "label2"},
}


class Film:
    def __init__(self, cfg: dict, orientation: str, layout: bool = False):
        self.cfg = cfg
        self.orient = orientation
        self.use_layouts = layout
        self.w, self.h = cfg["canvas"][orientation]
        self.slots = cfg["slots"][orientation]
        self.type = cfg["type"][orientation]
        self.css: list[str] = []
        self.html: list[str] = []
        self.js: list[str] = []
        self.base = 0.0          # 子合成模式下的时间基准：补间时间统一减去它
        self.extra_css: list[str] = []
        self.n = 0               # 场景序号，用来轮换纸色

    def tb(self, x: float) -> float:
        """绝对时间 → 当前（子）合成内的时间。"""
        return max(0.0, x - self.base)

    # ---------- 元素定位 ----------
    def slot(self, name: str) -> dict:
        if name in self.slots:
            return self.slots[name]
        return self.slots[name.rstrip("123") or name]

    def resolve(self, scene_variant: str, key: str) -> str:
        return VARIANT_SLOTS.get(scene_variant, {}).get(key, VARIANT_SLOTS["assembly"].get(key, key))

    def resolve_layout(self, layout: str, key: str, variant: str) -> str:
        """先看场景类型给的槽位，再退回变体槽位。"""
        return LAYOUT_SLOTS.get(layout, {}).get(key) or self.resolve(variant, key)

    def place(self, el_id: str, slot: dict, z: int) -> None:
        left = px(slot["x"], self.w)
        top = px(slot["y"], self.h)
        width = px(slot["w"], self.w) if slot.get("w") is not None else None
        if slot.get("right") is not None and width is not None:
            left = px(slot["right"], self.w) - width
        rot = slot.get("rot", 0.0)
        rule = f"#{el_id}{{left:{left}px;top:{top}px;"
        if width is not None:
            rule += f"width:{width}px;"
        if slot.get("h") is not None:
            rule += f"height:{px(slot['h'], self.h)}px;"
        rule += f"z-index:{z};--rot:{rot}deg}}"
        self.css.append(rule)

    def layer_px(self, name: str) -> tuple[int, int, int, int]:
        s = self.slot(name)
        left = px(s["x"], self.w)
        top = px(s["y"], self.h)
        width = px(s["w"], self.w) if s.get("w") is not None else 0
        if s.get("right") is not None and width:
            left = px(s["right"], self.w) - width
        return left, top, width, 0

    # ---------- 场景 ----------
    def tween_in(self, sel: str, kind: str, t: float, dur: float, rot: float) -> None:
        """按元素类型给不同的入场方式。"""
        e = f"{dur:.2f}"
        if kind == "scrap":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,x:-150,y:40,rotation:{rot-5:.2f}}},'
                f'{{autoAlpha:1,x:0,y:0,rotation:{rot:.2f},duration:{e},ease:"steps(6)"}},{t:.2f});'
            )
        elif kind == "scrap2":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,y:-120,rotation:{rot+4:.2f}}},'
                f'{{autoAlpha:1,y:0,rotation:{rot:.2f},duration:{e},ease:"steps(6)"}},{t:.2f});'
            )
        elif kind == "hero":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,x:90,scale:1.05}},'
                f'{{autoAlpha:1,x:0,scale:1,duration:{e},ease:"steps(7)"}},{t:.2f});'
            )
        elif kind == "photo":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,y:110}},'
                f'{{autoAlpha:1,y:0,duration:{e},ease:"steps(6)"}},{t:.2f});'
            )
        elif kind == "portrait":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,y:-130,rotation:{rot-4:.2f}}},'
                f'{{autoAlpha:1,y:0,rotation:{rot:.2f},duration:{e},ease:"steps(6)"}},{t:.2f});'
            )
        elif kind == "tape":
            self.js.append(
                f'tl.fromTo("{sel}",{{scaleY:0,autoAlpha:0}},'
                f'{{scaleY:1,autoAlpha:1,duration:{min(dur,0.22):.2f},ease:"steps(3)",'
                f'transformOrigin:"50% 0%"}},{t:.2f});'
            )
        elif kind == "label":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,x:-110}},'
                f'{{autoAlpha:1,x:0,duration:{e},ease:"steps(5)"}},{t:.2f});'
            )
        elif kind == "label2":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,x:110}},'
                f'{{autoAlpha:1,x:0,duration:{e},ease:"steps(5)"}},{t:.2f});'
            )
        elif kind == "stamp":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,scale:1.6,rotation:{rot-12:.2f}}},'
                f'{{autoAlpha:1,scale:1,rotation:{rot:.2f},duration:{min(dur,0.26):.2f},'
                f'ease:"steps(3)",transformOrigin:"50% 50%"}},{t:.2f});'
            )
        elif kind in ("pin", "tick"):
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,scale:1.8}},'
                f'{{autoAlpha:1,scale:1,duration:{min(dur,0.18):.2f},ease:"steps(3)",'
                f'transformOrigin:"50% 50%"}},{t:.2f});'
            )
        elif kind == "string":
            self.js.append(
                f'tl.fromTo("{sel}",{{scaleX:0}},'
                f'{{scaleX:1,duration:{max(dur,0.7):.2f},ease:"steps(6)",'
                f'transformOrigin:"0% 50%"}},{t:.2f});'
            )
        elif kind == "underline":
            self.js.append(
                f'tl.fromTo("{sel}",{{scaleX:0}},'
                f'{{scaleX:1,duration:{min(dur,0.34):.2f},ease:"steps(4)",'
                f'transformOrigin:"0% 50%"}},{t:.2f});'
            )
        elif kind == "chapter_no":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,scale:1.5}},'
                f'{{autoAlpha:1,scale:1,duration:{max(dur,0.30):.2f},ease:"steps(4)",'
                f'transformOrigin:"50% 50%"}},{t:.2f});'
            )
        elif kind == "chapter_ti":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,y:60}},'
                f'{{autoAlpha:1,y:0,duration:{e},ease:"steps(6)"}},{t:.2f});'
            )
        elif kind == "band":
            self.js.append(
                f'tl.fromTo("{sel}",{{autoAlpha:0,y:70,rotation:{rot - 2:.2f}}},'
                f'{{autoAlpha:1,y:0,rotation:{rot:.2f},duration:{max(dur,0.34):.2f},'
                f'ease:"steps(5)"}},{t:.2f});'
            )
        elif kind == "underline_v":
            self.js.append(
                f'tl.fromTo("{sel}",{{scaleY:0}},'
                f'{{scaleY:1,duration:{max(dur,0.36):.2f},ease:"steps(5)",'
                f'transformOrigin:"50% 0%"}},{t:.2f});'
            )
        elif kind == "counter":
            # 数字自己长出来：从 0 数到目标值（目标值走 rot 传进来）
            target = int(round(abs(rot)))
            eid = sel.strip("#")
            var = "_cv" + str(abs(hash(eid)) % 100000)
            self.js.append(
                "var " + var + "={v:0};"
                "tl.fromTo(" + var + ",{v:0},{v:" + str(target) +
                ',duration:1.4,ease:"power2.out",onUpdate:function(){var o=this.targets()[0];'
                'document.getElementById("' + eid + '").textContent=_fmt(o.v);}},'
                + f'{t:.2f});'
            )

    def scene(self, sc: dict) -> None:
        sid = sc["id"]
        self.n += 1
        shot = sc.get("_shot") if (self.use_layouts and shotgram) else None
        start = float(sc["start"])
        dur = float(sc["duration"])
        end = start + dur
        cast = sc.get("cast", {})
        cast_late = sc.get("cast_late", {})

        track = int(sc.get("track", 1))
        html = [f'<section class="clip" id="{sid}" data-start="{start:.3f}" '
                f'data-duration="{dur:.3f}" data-track-index="{track}">']
        if shot:
            html.append(f'<div class="shot" id="{sid}-shot">')

        events: list[tuple[str, str, float, str]] = []   # (selector, kind, rot, sortkey)

        variant = sc.get("_variant", "assembly")
        # 叙事场景自带舞台，不走镜头的版式附加件（纸带/中缝/红圈那些）
        layout = (sc.get("_layout", "stage")
                  if (self.use_layouts and not sc.get("story")) else "stage")

        # 章节卡：大编号 + 标题 + 红线，居中压在纸上
        if sc.get("chapter"):
            ch = sc["chapter"]
            eid = f"{sid}-chap"
            self.css.append(
                f"#{eid}{{position:absolute;left:0;right:0;top:34%;text-align:center;z-index:50}}"
                f"#{eid} .no{{font-family:'Mono',monospace;line-height:1;color:#8f2b1c;"
                f"font-size:{int(self.type['big'] * 1.9)}px}}"
                f"#{eid} .ti{{font-family:'TypeCN',sans-serif;font-weight:700;color:#221d16;"
                f"font-size:{int(self.type['cn'] * 1.5)}px;margin-top:16px}}"
                f"#{eid} .rl{{margin:24px auto 0;height:10px;border-radius:5px;background:#c0392b;"
                f"width:{px(0.28, self.w)}px}}"
            )
            html.append(
                f'<div class="chap" id="{eid}"><div class="no">{esc(str(ch.get("no", "")))}</div>'
                f'<div class="ti">{esc(ch.get("title", ""))}</div><div class="rl"></div></div>'
            )
            events.append((f"#{eid} .no", "chapter_no", 0.0, "00a"))
            events.append((f"#{eid} .ti", "chapter_ti", 0.0, "00b"))
            events.append((f"#{eid} .rl", "underline", 0.0, "00c"))

        # ---- 叙事舞台：谁（人物）+ 在哪（场景）+ 做什么（事件主体）----
        story = sc.get("story")
        if story:
            cast = {}          # 有叙事舞台时，关掉自动选角/胶带/标签那一套
            cast_late = {}
            hero_geo = shotgram.hero_geom(shot, self.orient) if shot else {"x": 0.3, "y": 0.3, "w": 0.46}
            hero_right = (hero_geo["x"] + hero_geo["w"] / 2) > 0.5
            show = story.get("show") or ["where", "who", "what"]
            # 场景面板：照片面板压在主体反侧
            if story.get("where") and "where" in show:
                eid, x, y, w = f"{sid}-panel", (0.02 if hero_right else 0.52), 0.10, 0.45
                if self.orient == "port":
                    x, y, w = 0.05, 0.52, 0.90
                self.css.append(
                    f"#{eid}{{left:{px(x, self.w)}px;top:{px(y, self.h)}px;"
                    f"width:{px(w, self.w)}px;z-index:2}}")
                html.append(f'<img class="el panel" id="{eid}" '
                            f'src="assets/elements/{story["where"]}.png" alt="" />')
                events.append((f"#{eid}", "scrap", 1.5, "0-1-panel"))
            # 人物：站在画面下缘，先于主体入场
            for i, who in enumerate((story.get("who", [])[:3] if "who" in show else [])):
                eid = f"{sid}-who{i}"
                if self.orient == "port":
                    x, y, w = 0.04 + i * 0.30, 0.06, 0.28
                else:
                    x, y, w = 0.05 + i * 0.17, 0.60, 0.16
                self.place(eid, {"x": x, "y": y, "w": w, "rot": -1.5 + i}, 6 + i)
                html.append(f'<img class="el" id="{eid}" '
                            f'src="assets/elements/{who}.png" alt="" />')
                events.append((f"#{eid}", "portrait", 0.0, f"0-2-who{i}"))
            # 事件主体：车/道具，用镜头几何落位
            what = story.get("what") or ""
            if what.startswith("draw:") and props_mod:
                _dc, _dh, _de = props_mod.build(what.split(":", 1)[1], story.get("prop", {}),
                                                sid, self.orient, self.w, self.h, self.type)
                self.css.extend(_dc)
                html.extend(_dh)
                events.extend(_de)
                what = ""
            if what and "what" in show:
                eid = f"{sid}-hero"
                self.place(eid, hero_geo, 10)
                html.append(f'<img class="el" id="{eid}" '
                            f'src="assets/elements/{story["what"]}.png" alt="" />')
                events.append((f"#{eid}", "hero", 0.0, "0-3-hero"))
            # 事件文字：由人写好的事件描述，不再截断旁白
            if story.get("event"):
                eid = f"{sid}-l2"
                lx, ly = (0.06, 0.80) if self.orient == "land" else (0.06, 0.80)
                self.css.append(
                    f"#{eid}{{left:{px(lx, self.w)}px;top:{px(ly, self.h)}px;z-index:40}}"
                    f"#{eid} .cn{{font-size:{self.type['cn']}px}}")
                html.append(f'<div class="label label-2" id="{eid}">'
                            f'<div class="cn">{esc(story["event"])}</div></div>')
                events.append((f"#{eid}", "label2", 0.0, "0-4-event"))
            if story.get("year"):
                eid = f"{sid}-l1"
                self.css.append(
                    f"#{eid}{{left:{px(0.05, self.w)}px;top:{px(0.06, self.h)}px;z-index:40}}"
                    f"#{eid} .big{{font-size:{self.type['big']}px}}"
                    f"#{eid} .small{{font-size:{self.type['small']}px}}")
                html.append(
                    f'<div class="label label-1" id="{eid}">'
                    f'<div class="big">{esc(story["year"])}</div>'
                    f'<div class="small">{esc(story.get("tag", ""))}</div></div>')
                events.append((f"#{eid}", "label", 0.0, "0-5-year"))

        first = VARIANT_FIRST.get(variant, "scrap")
        order = ["scrap", "scrap2", "hero", "hero_b", "portrait", "mini", "photo1", "photo2"]
        if first == "hero":
            order = ["hero", "scrap", "hero_b", "portrait", "mini", "scrap2", "photo1", "photo2"]
        for i, slot_name in enumerate(order):
            if slot_name not in cast:
                continue
            el = cast[slot_name]
            eid = f"{sid}-{slot_name.replace('_', '')}"
            mapped = slot_name in ("hero", "scrap", "portrait", "mini", "hero_b")
            if shot and mapped:
                hg = shotgram.hero_geom(shot, self.orient) if slot_name == "hero" else \
                    shotgram.support_geom(shot, slot_name, self.orient,
                                          shotgram.hero_geom(shot, self.orient))
                self.place(eid, hg, 2 + i)
                target = slot_name
            else:
                target = self.resolve_layout(layout, slot_name, variant) if mapped else slot_name
                self.place(eid, self.slot(target), 2 + i)
            kind = {"scrap": "scrap", "scrap2": "scrap2", "hero": "hero",
                    "hero_b": "photo", "portrait": "portrait", "mini": "photo",
                    "photo1": "photo", "photo2": "photo"}[slot_name]
            html.append(f'<img class="el" id="{eid}" src="assets/elements/{el}.png" alt="" />')
            rot = self.slot(target).get("rot", 0.0)
            events.append((f"#{eid}", kind, rot, f"cast{i:02d}"))

        # 胶带
        for i, tape_slot in enumerate(sc.get("tape", [])):
            eid = f"{sid}-tape{i}"
            self.place(eid, self.slot(tape_slot), 30 + i)
            html.append(f'<div class="tape" id="{eid}"></div>')
            events.append((f"#{eid}", "tape", 0.0, f"tape{i:02d}"))

        # 红绳与图钉
        if sc.get("string"):
            pts = [self.layer_px(p) for p in sc["string"]]
            coords = [(p[0] + 14, p[1] + 14) for p in pts]
            d = f"M {coords[0][0]} {coords[0][1]}"
            for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + self.h * 0.035
                d += f" Q {mx:.0f} {my:.0f} {x1} {y1}"
            self.css.append(f"#{sid}-string svg{{width:{self.w}px;height:{self.h}px}}")
            self.css.append(f"#{sid}-string{{position:absolute;inset:0;z-index:26;overflow:hidden}}")
            html.append(
                f'<div class="string-wrap" id="{sid}-string"><svg viewBox="0 0 {self.w} {self.h}" '
                f'xmlns="http://www.w3.org/2000/svg"><path d="{d}" fill="none" '
                f'stroke="#b3271c" stroke-width="3.2" stroke-linecap="round"/></svg></div>'
            )
            for i, (x, y) in enumerate(coords):
                eid = f"{sid}-pin{i}"
                self.css.append(
                    f"#{eid}{{position:absolute;left:{x - 14}px;top:{y - 14}px;width:28px;height:28px;"
                    f"z-index:27}}"
                )
                html.append(f'<div class="pin" id="{eid}"></div>')
            events.append((f"#{sid}-pin0", "pin", 0.0, "pin0"))
            events.append((f"#{sid}-pin1", "pin", 0.0, "pin1"))
            events.append((f"#{sid}-pin2", "pin", 0.0, "pin2"))
            events.append((f"#{sid}-string", "string", 0.0, "string"))

        # 标签与印章
        l1 = sc.get("label1")
        if l1 and layout != "bignum":
            eid = f"{sid}-l1"
            self.place(eid, self.slot(self.resolve_layout(layout, "label1", variant)), 40)
            self.css.append(
                f"#{eid} .big{{font-size:{self.type['big']}px}}"
                f"#{eid} .small{{font-size:{self.type['small']}px}}"
            )
            html.append(
                f'<div class="label label-1" id="{eid}"><div class="big">{esc(l1["big"])}</div>'
                f'<div class="small">{esc(l1["small"])}</div></div>'
            )
            events.append((f"#{eid}", "label", 0.0, "label1"))
            # 下划线跟着标签走
            if sc.get("underline"):
                pad = 14 + 18
                lab_h = pad + self.type["big"] * 1.02 + 4 + self.type["small"] * 1.2
                left, top, _, _ = self.layer_px("label1")
                tw = len(str(l1["big"]))
                lab_w = int(tw * (self.type["big"] * 0.60 + 5) + 48)
                eid = f"{sid}-ul"
                self.css.append(
                    f"#{eid}{{left:{left + 8}px;top:{top + int(lab_h) + 6}px;"
                    f"width:{int(lab_w * 0.82)}px;z-index:41}}"
                )
                html.append(f'<div class="underline" id="{eid}"></div>')
                events.append((f"#{eid}", "underline", 0.0, "zz-underline"))

        l2 = sc.get("label2")
        if l2:
            eid = f"{sid}-l2"
            self.place(eid, self.slot(self.resolve_layout(layout, "label2", variant)), 40)
            self.css.append(f"#{eid} .cn{{font-size:{self.type['cn']}px}}")
            html.append(f'<div class="label label-2" id="{eid}"><div class="cn">{esc(l2)}</div></div>')
            events.append((f"#{eid}", "label2", 0.0, "label2"))

        if sc.get("stamp"):
            eid = f"{sid}-st"
            self.place(eid, self.slot("stamp"), 42)
            self.css.append(
                f"#{eid} .cn{{font-size:{self.type['stamp_cn']}px}}"
                f"#{eid} .en{{font-size:{self.type['stamp_en']}px}}"
            )
            html.append(
                f'<div class="stamp" id="{eid}">'
                f'<div class="cn" data-layout-allow-overlap>{esc(sc["stamp"])}</div>'
                f'<span class="en">ARCHIVE</span></div>'
            )
            rot = self.slot("stamp").get("rot", -6.0)
            events.append((f"#{eid}", "stamp", rot, "stamp"))

        # late 元素（长场景的第二个信息波）
        late_events = []
        for slot_name, el in cast_late.items():
            eid = f"{sid}-late-{slot_name}"
            target = self.resolve(variant, slot_name) if slot_name in ("hero", "scrap", "portrait", "mini") else slot_name
            self.place(eid, self.slot(target), 12)
            html.append(f'<img class="el" id="{eid}" src="assets/elements/{el}.png" alt="" />')
            late_events.append(f"#{eid}")

        # ---- 镜头附加件：纸色、纸带、中缝、年表轴、巨数字、红圈 ----
        tone = PLATE_TONES[self.n % len(PLATE_TONES)][0]
        html.insert(1, f'<div class="tone tone-{tone}"></div>')
        W, H = self.w, self.h
        if layout == "fullbleed":
            eid = f"{sid}-band"
            self.css.append(
                f"#{eid}{{position:absolute;left:-2%;right:-2%;top:{int(H * 0.62)}px;"
                f"height:{int(H * 0.30)}px;background:#efe7d6;z-index:30;"
                f"box-shadow:0 10px 26px rgba(40,28,12,.34)}}")
            html.append(f'<div class="band" id="{eid}"></div>')
            events.append((f"#{eid}", "band", -1.2, "z1-band"))
        elif layout == "duo":
            eid = f"{sid}-div"
            self.css.append(
                f"#{eid}{{position:absolute;left:{int(W * 0.495)}px;top:{int(H * 0.12)}px;"
                f"width:6px;height:{int(H * 0.72)}px;background:#b3271c;opacity:.78;"
                f"z-index:30}}")
            html.append(f'<div class="divider" id="{eid}"></div>')
            events.append((f"#{eid}", "underline_v", 0.0, "z1-div"))
        elif layout == "timeline":
            eid = f"{sid}-axis"
            self.css.append(
                f"#{eid}{{position:absolute;left:6%;right:6%;top:{int(H * 0.60)}px;"
                f"height:6px;background:#2a2418;opacity:.72;z-index:30}}")
            html.append(f'<div class="axis" id="{eid}"></div>')
            events.append((f"#{eid}", "underline", 0.0, "z1-axis"))
            eid2 = f"{sid}-mark"
            self.css.append(
                f"#{eid2}{{position:absolute;left:{int(W * 0.30)}px;top:{int(H * 0.595)}px;"
                f"width:{int(W * 0.26)}px;height:10px;background:#b3271c;z-index:31;"
                f"border-radius:5px}}")
            html.append(f'<div class="mark" id="{eid2}"></div>')
            events.append((f"#{eid2}", "underline", 0.0, "z2-mark"))
        elif layout == "bignum":
            eid = f"{sid}-bn"
            nfs = int(self.type["big"] * 2.4)
            self.css.append(
                f"#{eid}{{position:absolute;left:{int(W * 0.04)}px;top:{int(H * 0.20)}px;"
                f"z-index:32;background:#efe7d6;padding:{int(nfs * 0.10)}px {int(nfs * 0.16)}px;"
                f"box-shadow:0 10px 26px rgba(40,28,12,.34)}}"
                f"#{eid} .n{{display:block;font-family:'Mono',monospace;font-size:{nfs}px;"
                f"line-height:1.05;letter-spacing:4px;color:#8f2b1c}}"
                f"#{eid} .u{{display:block;font-family:'TypeCN',sans-serif;"
                f"font-size:{int(self.type['cn'])}px;color:#2a241a;margin-top:6px}}")
            html.append(
                f'<div class="bignum" id="{eid}"><span class="n">{esc(str(l1["big"])) if l1 else ""}'
                f'</span><span class="u">{esc(l1["small"]) if l1 else ""}</span></div>')
            events.append((f"#{eid}", "stamp", -2.0, "z1-bn"))
        elif layout == "quote":
            ps = self.slot(self.resolve_layout(layout, "portrait", variant))
            eid = f"{sid}-ring"
            self.css.append(
                f"#{eid}{{position:absolute;left:{px(ps['x'], W) + int(W * ps['w'] * 0.06)}px;"
                f"top:{px(ps['y'], H) + int(H * 0.04)}px;width:{int(W * ps['w'] * 0.90)}px;"
                f"height:{int(H * 0.34)}px;border:5px solid #b3271c;border-radius:50%;"
                f"opacity:.80;z-index:31}}")
            html.append(f'<div class="ring" id="{eid}"></div>')
            events.append((f"#{eid}", "pin", 0.0, "z1-ring"))
        # ---- 镜头运动：按景别给推/拉/缓移/横摇，静止镜头不动 ----
        if shot:
            t0 = self.tb(start)
            span = max(0.8, self.tb(start + dur) - t0)
            mv = shot["move"]
            if mv == "push":
                self.js.append(
                    f'tl.fromTo("#{sid}-shot",{{scale:1.0}},'
                    f'{{scale:1.05,duration:{span:.2f},ease:"power1.inOut",'
                    f'transformOrigin:"50% 50%"}},{t0:.2f});')
            elif mv == "pull":
                self.js.append(
                    f'tl.fromTo("#{sid}-shot",{{scale:1.06}},'
                    f'{{scale:1.0,duration:{span:.2f},ease:"power1.inOut",'
                    f'transformOrigin:"50% 50%"}},{t0:.2f});')
            elif mv == "drift":
                dx = int(self.w * 0.018)
                self.js.append(
                    f'tl.fromTo("#{sid}-shot",{{x:{-dx}}},'
                    f'{{x:{dx},duration:{span:.2f},ease:"none"}},{t0:.2f});')
            elif mv == "pan":
                dy = int(self.h * 0.022)
                self.js.append(
                    f'tl.fromTo("#{sid}-shot",{{y:{-dy}}},'
                    f'{{y:{dy},duration:{span:.2f},ease:"none"}},{t0:.2f});')
        if shot:
            html.append("</div>")
        dev = sc.get("_device") if (self.use_layouts and devices) else None
        if dev:
            dc, dh, de = devices.build(dev, sid, self.orient, self.w, self.h, self.type)
            self.css.extend(dc)
            pos = max(0, len(html) - 1)
            while pos > 0 and "</section>" not in html[pos]:
                pos -= 1
            html.insert(pos, "".join(dh))
            events.extend(de)
        html.append("</section>")
        self.html.extend(html)

        # ---- 时间分配 ----
        events.sort(key=lambda e: e[3])
        n = len(events)
        budget = min(max(dur - 0.8, 0.9), 2.6)
        step = min(0.26, max(0.09, budget / max(n - 1, 1)))
        for i, (sel, kind, rot, _) in enumerate(events):
            t = start + 0.10 + i * step
            tdur = min(0.32, step * 1.5)
            if kind == "string":
                tdur = min(0.9, max(0.5, step * 3.2))
            self.tween_in(sel, kind, self.tb(t), tdur, rot)

        for j, sel in enumerate(late_events):
            t = start + dur * 0.5 + j * 0.26
            self.tween_in(sel, "photo", self.tb(t), 0.3, 0.0)

        # ---- 出场：主图向左滑出，下一场从右侧滑入（同向，符合矢量律）----
        exit_t = max(start + 0.3, end - 0.24)
        for slot_name in ("hero", "hero_b", "portrait", "mini", "photo1", "photo2"):
            if slot_name in cast:
                eid = f"{sid}-{slot_name.replace('_', '')}"
                self.js.append(
                    f'tl.to("#{eid}",{{x:-46,autoAlpha:0,duration:0.24,ease:"steps(3)"}},'
                    f'{self.tb(exit_t):.2f});'
                )
                # 出场补间结束在 clip 边界上，必须跟一个硬杀，否则乱序 seek 会留下脏状态
                self.js.append(
                    f'tl.set("#{eid}",{{visibility:"hidden"}},{self.tb(end):.2f});'
                )

    # ---------- 输出 ----------
    def css_block(self) -> str:
        cfg = self.cfg
        plate_cfg = cfg["plate"][self.orient]
        plate_css = (
            f".plate-map{{background-image:url('{plate_cfg['map']}');"
            f"background-position:{plate_cfg.get('pos', '50% 45%')};"
            f"opacity:{plate_cfg.get('opacity', 0.30)};}}"
        )
        el_shadow = cfg.get("element_shadow", "css")
        return (BASE_CSS.replace("__W__", str(self.w))
                .replace("__H__", str(self.h))
                .replace("__EL_SHADOW__", "" if el_shadow == "baked"
                         else "filter: drop-shadow(6px 8px 12px rgba(42, 30, 14, .40));")
                .replace("__PLATE__", plate_css)
                .replace("__GEN__", "\n      ".join(self.css)))

    def render(self) -> str:
        cfg = self.cfg
        plate_cfg = cfg["plate"][self.orient]
        plate_css = (
            f".plate-map{{background-image:url('{plate_cfg['map']}');"
            f"background-position:{plate_cfg.get('pos', '50% 45%')};"
            f"opacity:{plate_cfg.get('opacity', 0.30)};}}"
        )
        el_shadow = cfg.get("element_shadow", "css")
        bgm = cfg.get("bgm")
        base_css = (
            BASE_CSS.replace("__W__", str(self.w))
            .replace("__H__", str(self.h))
            .replace("__EL_SHADOW__", "" if el_shadow == "baked"
                     else "filter: drop-shadow(6px 8px 12px rgba(42, 30, 14, .40));")
            .replace("__PLATE__", plate_css)
            .replace("__GEN__", "\n      ".join(self.css))
        )
        return TEMPLATE.format(
            w=self.w, h=self.h, dur=f"{cfg['duration']:.3f}", audio=cfg["audio"],
            base_css=base_css, plate_css=plate_css,
            bgm_html=(
                f'<audio id="bgm" src="{bgm["src"]}" data-start="0" '
                f'data-duration="{cfg["duration"]:.3f}" loop '
                f'volume="{bgm.get("volume", 0.16)}"></audio>'
                if bgm else ""
            ),
            plate_html=(
                '<div class="plate" id="plate">'
                '<div class="plate-map"></div>'
                '<div class="plate-stain a"></div>'
                '<div class="plate-stain b"></div>'
                '<div class="plate-vignette"></div>'
                '<div class="plate-grain"></div></div>'
            ),
            scenes="\n      ".join(self.html),
            js="\n      ".join(self.js),
        )


BASE_CSS = """
      @font-face { font-family: "TypeCN"; src: local("Microsoft YaHei"); }
      @font-face { font-family: "Deck"; src: local("Impact"); }
      @font-face { font-family: "Mono"; src: local("Courier New"); }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: __W__px; height: __H__px; overflow: hidden; background: #4b4335; }
      #root { position: relative; width: __W__px; height: __H__px; overflow: hidden; }
      .clip { position: absolute; inset: 0; overflow: hidden; }
      .shot { position: absolute; inset: 0; will-change: transform; }
      .plate { position: absolute; inset: 0; background: #d9cfbb; z-index: 0; }
      .plate-stain { position: absolute; mix-blend-mode: multiply; }
      .plate-stain.a { left: -10%; top: 34%; width: 70%; height: 60%;
        background: radial-gradient(closest-side, rgba(126,98,54,.30), rgba(126,98,54,0) 72%); }
      .plate-stain.b { right: -12%; top: -12%; width: 66%; height: 56%;
        background: radial-gradient(closest-side, rgba(104,84,48,.26), rgba(104,84,48,0) 70%); }
      .plate-vignette { position: absolute; inset: 0; box-shadow: inset 0 0 260px rgba(52, 38, 18, .42); }
      .plate-grain { position: absolute; inset: 0; pointer-events: none; opacity: .13; mix-blend-mode: multiply; }
      .plate-grain::after { content: ""; position: absolute; inset: 0;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/></filter><rect width='260' height='260' filter='url(%23n)' opacity='0.6'/></svg>"); }
      .el { position: absolute; display: block; __EL_SHADOW__ }
      .tape { position: absolute; background: rgba(238, 226, 194, .72);
        border-left: 1px solid rgba(150, 130, 92, .45); border-right: 1px solid rgba(150, 130, 92, .45);
        box-shadow: 0 2px 6px rgba(48, 34, 16, .22); }
      /* 图钉不要用 radial-gradient：长片里几百个渐变会被判为「重叠加层过多」，
         有捕捉出黑帧的风险。改用实色 + 内阴影。 */
      .pin { border-radius: 50%; background: #b3271c; border: 2px solid #8a1f14;
        box-shadow: inset -2px -2px 0 rgba(0, 0, 0, .22), 3px 5px 8px rgba(40, 26, 12, .45); }
      .label { position: absolute; background: #efe7d6; box-shadow: 0 6px 14px rgba(44, 30, 14, .34); }
      .label-1 { padding: 14px 24px 18px; border: 2px solid rgba(70, 56, 32, .45); }
      .label-1 .big { font-family: "Mono", monospace; line-height: 1.02; letter-spacing: 5px; color: #211d16; }
      .label-1 .small { font-family: "Deck", "TypeCN", sans-serif; line-height: 1.2; letter-spacing: 3px; color: #8f2b1c; margin-top: 4px; }
      .label-2 { padding: 14px 24px 18px; background: #e6dcc4; }
      .label-2 .cn { font-family: "TypeCN", sans-serif; line-height: 1.2; letter-spacing: 2px; color: #2a241a; }
      .stamp { border: 6px solid #a82a1c; color: #a82a1c; opacity: .84; padding: 10px 18px 14px; text-align: center; }
      .stamp .cn { font-family: "TypeCN", sans-serif; line-height: 1.15; letter-spacing: 7px; font-weight: 700; }
      .stamp .en { font-family: "Deck", sans-serif; letter-spacing: 6px; display: block; margin-top: 12px; }
      .underline { position: absolute; height: 11px; background: #c0392b; opacity: .88; border-radius: 6px; }
      .tone { position: absolute; inset: 0; z-index: 1; pointer-events: none; }
      .tone-warm { background: #cdb894; mix-blend-mode: multiply; opacity: .34; }
      .tone-pale { background: #fff6e4; opacity: .20; }
      .tone-grey { background: #9d9788; mix-blend-mode: multiply; opacity: .20; }
      .tick { position: absolute; border: 5px solid #f4ead6; opacity: .8; }
      __PLATE__
      __GEN__
"""

TEMPLATE = """<!doctype html>
<!-- 由 build_film.py 生成；手改会在下次生成时被覆盖 -->
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <style>{base_css}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}"
         data-width="{w}" data-height="{h}">
      <audio id="narration" src="{audio}" data-start="0" data-duration="{dur}"></audio>
      {bgm_html}
      {plate_html}
      {scenes}
    </div>
    <script src="assets/vendor/gsap.min.js"></script>
    <script>
      window.__timelines = window.__timelines || {{}};
      var _fmt = function (v) {{ return String(Math.round(v)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ","); }};
      const tl = gsap.timeline({{ paused: true }});
      {js}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--orientation", choices=["land", "port"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.film, encoding="utf-8") as fh:
        cfg = json.load(fh)

    # 逐场分配变体：同一种构图绝不连着出现，长片才不会看腻
    prev = None
    for i, sc in enumerate(cfg["scenes"]):
        if sc.get("chapter"):
            v = "chapter"
        elif sc.get("variant"):
            v = sc["variant"]
        else:
            has_hero = "hero" in sc.get("cast", {})
            pool = [x for x in (VARIANT_ROTATION if has_hero else ["board", "assembly", "reveal"])
                    if x != prev] or ["assembly"]
            v = pool[i % len(pool)]
        sc["_variant"] = v
        prev = v

    for i, sc in enumerate(cfg["scenes"]):
        sc["_layout"] = ("chapter" if sc.get("chapter")
                         else LAYOUT_ROTATION[i % len(LAYOUT_ROTATION)])

    film = Film(cfg, args.orientation, layout=True)
    for sc in cfg["scenes"]:
        film.scene(sc)
    html = film.render()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    # ---- 质检摘要 ----
    import collections
    variants = [sc["_variant"] for sc in cfg["scenes"]]
    dup = sum(1 for a, b in zip(variants, variants[1:]) if a == b)
    used = collections.Counter(
        el for sc in cfg["scenes"] for el in sc.get("cast", {}).values()
    )
    total = sum(float(sc["duration"]) for sc in cfg["scenes"])
    print(f"{args.out}  {len(html) / 1024:.1f} KB  scenes={len(cfg['scenes'])}  "
          f"canvas={film.w}x{film.h}  {total:.1f}s")
    print(f"  变体分布: {dict(collections.Counter(variants))}")
    print(f"  相邻同构图: {dup} 处{'（应为 0）' if dup else ''}")
    print("  元素库用量: 共 {} 个，最高 {}".format(
        len(used), ", ".join(f"{k}×{v}" for k, v in used.most_common(5))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
