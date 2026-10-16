#!/usr/bin/env python3
"""devices.py - 视觉诠释层：把旁白里的"意思"翻成画面装置。

镜头运动只是让画面动起来；这一层负责让画面**把话说明白**：
改名就演改名、销量就长条形、收购就盖章、因果就用红绳串起来、年代就上年表轴。

每个装置 = 拼贴料做的信息图：纸片、打字机字、印章红、红绳、马克笔。
由 plan_scenes 按文本识别挂到场景上，build_film 负责落位与播放。
"""
from __future__ import annotations

import re

CN_DIGIT = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9}

YEAR_RE = re.compile(r"[一二三四五六七八九零]{4}年")
NUM_UNIT_RE = re.compile(r"(\d[\d,\.]*)\s*(万台|万辆|万|台|辆|公里|千米|km|马力|匹|美元|亿|%|秒)")

VERDICT_WORDS = ["收购", "停产", "破产", "倒闭", "危机", "差点", "退出", "卖掉", "离职", "失败"]
SUBSTITUTE_WORDS = ["改名", "改成", "变成", "换成", "取代"]
CAUSE_WORDS = ["因为", "所以", "导致", "于是", "结果", "这才", "因此"]
BAR_WORDS = ["对比", "相比", "不如", "更", "反而", "比"]


def cn_year_to_int(y: str) -> int:
    body = y.replace("年", "")
    val = 0
    for ch in body:
        val = val * 10 + CN_DIGIT.get(ch, 0)
    return val


def detect(text: str, chapter_start: bool = False) -> dict | None:
    """识别这一场该用哪个装置。按特异性排序，一个场景只挂一个。"""
    t = re.sub(r"\s+", "", text)
    years = [cn_year_to_int(y) for y in YEAR_RE.findall(t)]

    # 1 改名/替代：明确抓「把A改成B」「A变成B」，抓不到就跳过（不硬凑旧/新）
    m = (re.search(r"把([0-9A-Za-z一二三四五六七八九零]{1,8})(?:改|换)成([0-9A-Za-z一二三四五六七八九零]{1,8})", t)
         or re.search(r"([0-9A-Za-z一二三四五六七八九零]{2,8})变成([0-9A-Za-z一二三四五六七八九零]{2,8})", t)
         or re.search(r"改名([0-9A-Za-z一二三四五六七八九零]{2,8})", t))
    if m:
        g = m.groups()
        if len(g) == 2 and g[0] != g[1]:
            return {"type": "substitute", "old": g[0], "new": g[1]}
        if len(g) == 1:
            return {"type": "substitute", "old": "SYMBOL", "new": g[0]}

    # 2 年份：两个以上 → 年表轴；单个年份不挂装置（标签里已经有了）
    if len(years) >= 2:
        return {"type": "timeline", "years": years[:4], "current": years[0]}

    # 3 判决/转折：盖章最有力量
    for w in VERDICT_WORDS:
        if w in t:
            return {"type": "verdict", "word": w}

    # 4 数字（非年份）：让它自己长出来；两个以上且有比较词 → 长条对比
    hits = NUM_UNIT_RE.findall(t)
    if len(hits) >= 2 and any(w in t for w in BAR_WORDS):
        bars = []
        for raw, unit in hits[:3]:
            try:
                bars.append({"label": raw + unit, "value": float(raw.replace(",", ""))})
            except ValueError:
                pass
        if len(bars) >= 2:
            return {"type": "bars", "bars": bars}
    if hits:
        raw, unit = hits[0]
        try:
            return {"type": "counter", "value": float(raw.replace(",", "")),
                    "unit": unit, "raw": raw}
        except ValueError:
            pass

    # 5 最高级/纪录 → 红圈标注
    for w in ("最美", "第一", "唯一", "最快", "纪录", "冠军"):
        if w in t:
            return {"type": "highlight", "word": w}

    # 6 因果 → 红绳串卡片
    if any(w in t for w in CAUSE_WORDS):
        parts = [p for p in re.split(r"[，。、,]", t) if 3 < len(p) <= 14][:3]
        if len(parts) >= 2:
            return {"type": "chain", "cards": parts}

    return None


# 装置画在哪：避开主图所在的一侧
PLACE = {
    "land": {"substitute": (0.10, 0.54), "verdict": (0.62, 0.10),
             "counter": (0.06, 0.60), "timeline": (0.06, 0.66),
             "chain": (0.32, 0.08), "highlight": (0.12, 0.58), "bars": (0.08, 0.54)},
    "port": {"substitute": (0.08, 0.56), "verdict": (0.52, 0.10),
             "counter": (0.06, 0.60), "timeline": (0.06, 0.66),
             "chain": (0.08, 0.08), "highlight": (0.08, 0.58), "bars": (0.06, 0.54)},
}


def build(dev: dict, sid: str, orient: str, W: int, H: int, tscale: dict) -> tuple[list, list, list]:
    """返回 (css, html, events)。events 里的 kind 由 build_film.tween_in 解释。"""
    css: list[str] = []
    html: list[str] = []
    events: list[tuple[str, str, float, str]] = []
    px = lambda f, b: int(round(f * b))  # noqa: E731
    x, y = PLACE[orient][dev["type"]]
    base = f"{sid}-dv"

    if dev["type"] == "substitute":
        css.append(
            f"#{base}{{position:absolute;left:{px(x, W)}px;top:{px(y, H)}px;z-index:44}}"
            f"#{base} .old{{display:inline-block;background:#efe7d6;color:#5a5145;"
            f"font-family:'Mono',monospace;font-size:{int(tscale['big']*0.9)}px;"
            f"padding:6px 16px;box-shadow:0 6px 14px rgba(44,30,14,.3)}}"
            f"#{base} .kill{{height:8px;background:#b3271c;border-radius:4px;margin-top:-{int(tscale['big']*0.45)}px;"
            f"width:{int(tscale['big']*2.6)}px}}"
            f"#{base} .new{{display:inline-block;margin-top:14px;background:#efe7d6;color:#8f2b1c;"
            f"font-family:'Mono',monospace;font-size:{int(tscale['big']*1.25)}px;padding:8px 18px;"
            f"box-shadow:0 8px 18px rgba(44,30,14,.36)}}")
        html.append(
            f'<div class="dv" id="{base}" data-layout-allow-overlap data-layout-allow-occlusion>'
            f'<span class="old" id="{base}-old" '
            f'data-layout-allow-occlusion>{dev["old"]}</span>'
            f'<div class="kill" id="{base}-kill"></div>'
            f'<span class="new" id="{base}-new" data-layout-allow-overlap data-layout-allow-occlusion>{dev["new"]}</span></div>')
        events.append((f"#{base}-old", "label", 0.0, "d1"))
        events.append((f"#{base}-kill", "underline", 0.0, "d2"))
        events.append((f"#{base}-new", "stamp", -2.0, "d3"))

    elif dev["type"] == "verdict":
        fs = int(tscale["big"] * 2.2)
        css.append(
            f"#{base}{{position:absolute;left:{px(x, W)}px;top:{px(y, H)}px;z-index:45;"
            f"border:9px solid #a82a1c;color:#a82a1c;font-family:'TypeCN',sans-serif;"
            f"font-weight:700;font-size:{fs}px;line-height:1.05;letter-spacing:10px;"
            f"padding:{int(fs*0.22)}px {int(fs*0.34)}px;opacity:.86}}")
        html.append(f'<div class="verdict" id="{base}" data-layout-allow-overlap data-layout-allow-occlusion>{dev["word"]}</div>')
        events.append((f"#{base}", "stamp", -7.0, "d1"))

    elif dev["type"] == "counter":
        fs = int(tscale["big"] * 1.9)
        css.append(
            f"#{base}{{position:absolute;left:{px(x, W)}px;top:{px(y, H)}px;z-index:62;"
            f"background:#efe7d6;padding:{int(fs*0.16)}px {int(fs*0.24)}px;"
            f"box-shadow:0 10px 24px rgba(44,30,14,.34)}}"
            f"#{base} .n{{display:block;font-family:'Mono',monospace;font-size:{fs}px;line-height:1.05;"
            f"color:#8f2b1c;letter-spacing:2px}}"
            f"#{base} .u{{display:block;font-family:'TypeCN',sans-serif;font-size:{int(tscale['cn'])}px;"
            f"color:#2a241a;margin-top:6px}}")
        html.append(f'<div class="counter" id="{base}" data-layout-allow-overlap data-layout-allow-occlusion>'
                    f'<span class="n" id="{base}-n">0</span>'
                    f'<span class="u">{dev["unit"]}</span></div>')
        events.append((f"#{base}", "counter", float(dev["value"]), "d1"))

    elif dev["type"] == "timeline":
        ys = dev["years"]
        css.append(
            f"#{base}{{position:absolute;left:{px(x, W)}px;top:{px(y, H)}px;"
            f"width:{px(0.62, W)}px;z-index:44}}"
            f"#{base} .ax{{height:6px;background:#2a2418;opacity:.75}}"
            f"#{base} .marks{{position:relative;height:{int(tscale['cn']*2.2)}px}}"
            f"#{base} .mk{{position:absolute;top:-6px;width:4px;height:{int(tscale['cn']*0.9)}px;"
            f"background:#2a2418;opacity:.8}}"
            f"#{base} .yr{{position:absolute;top:{int(tscale['cn']*0.9)}px;"
            f"font-family:'TypeCN',sans-serif;font-size:{int(tscale['cn']*0.78)}px;"
            f"color:#2a241a;transform:none}}")
        marks = ""
        n = len(ys)
        for i, yy in enumerate(ys):
            frac = 0.0 if n == 1 else i / (n - 1)
            # 年份标签交错上下，避免几个年份挤在同一高度互相压住
            top = int(tscale["cn"] * (0.9 if i % 2 == 0 else 2.15))
            marks += (f'<div class="mk" style="left:{int(frac*100)}%"></div>'
                      f'<div class="yr" data-layout-allow-overlap data-layout-allow-occlusion '
                      f'style="left:{int(frac*100)}%;top:{top}px">{yy}</div>')
        html.append(f'<div class="tl" id="{base}" data-layout-allow-overlap data-layout-allow-occlusion>'
                    f'<div class="ax" id="{base}-ax"></div>'
                    f'<div class="marks">{marks}</div></div>')
        events.append((f"#{base}-ax", "underline", 0.0, "d1"))

    elif dev["type"] == "chain":
        cards = dev["cards"]
        cw, ch = px(0.20, W), px(0.12, H)
        css.append(
            f"#{base}{{position:absolute;left:{px(x, W)}px;top:{px(y, H)}px;z-index:44}}"
            f"#{base} .card{{display:inline-block;width:{cw}px;min-height:{ch}px;margin-right:26px;"
            f"background:#efe7d6;box-shadow:0 8px 18px rgba(44,30,14,.32);padding:14px 16px;"
            f"font-family:'TypeCN',sans-serif;font-size:{int(tscale['cn']*0.82)}px;"
            f"color:#2a241a;line-height:1.3;vertical-align:top}}"
            f"#{base} .tie{{position:absolute;left:{cw+4}px;top:{int(ch*0.5)}px;"
            f"width:26px;height:4px;background:#b3271c}}")
        for i, c in enumerate(cards[:3]):
            html.append(f'<div class="card" id="{base}-c{i}">{c[:16]}</div>')
            events.append((f"#{base}-c{i}", "photo", 0.0, f"d{i+1}"))

    elif dev["type"] == "highlight":
        fs = int(tscale["big"] * 0.7)
        w, h = px(0.30, W), px(0.16, H)
        css.append(
            f"#{base}{{position:absolute;left:{px(x, W)}px;top:{px(y, H)}px;z-index:45;"
            f"width:{w}px;height:{h}px;border:5px solid #b3271c;border-radius:50%;opacity:.85}}"
            f"#{base} .w{{position:absolute;left:{w + 14}px;top:{int(h * 0.32)}px;"
            f"background:#efe7d6;color:#8f2b1c;font-family:'TypeCN',sans-serif;font-weight:700;"
            f"font-size:{fs}px;padding:4px 12px;box-shadow:0 6px 14px rgba(44,30,14,.3);"
            f"white-space:nowrap}}")
        html.append(f'<div class="hl" id="{base}" data-layout-allow-overlap data-layout-allow-occlusion>'
                    f'<span class="w">{dev["word"]}</span></div>')
        events.append((f"#{base}", "pin", 0.0, "d1"))

    elif dev["type"] == "bars":
        bw = px(0.42, W)
        bh = max(14, int(tscale["cn"] * 0.5))
        top = max(float(b["value"]) for b in dev["bars"]) or 1.0
        rows = ""
        for i, b in enumerate(dev["bars"]):
            frac = max(0.06, float(b["value"]) / top)
            rows += (f'<div class="row"><span class="lb">{b["label"]}</span>'
                     f'<span class="bar" id="{base}-b{i}" style="width:{int(bw * frac)}px"></span></div>')
        css.append(
            f"#{base}{{position:absolute;left:{px(x, W)}px;top:{px(y, H)}px;z-index:44;"
            f"background:#efe7d6;padding:14px 18px;box-shadow:0 8px 18px rgba(44,30,14,.32)}}"
            f"#{base} .row{{margin:6px 0;white-space:nowrap}}"
            f"#{base} .lb{{display:inline-block;width:{int(bw * 0.34)}px;"
            f"font-family:'TypeCN',sans-serif;font-size:{int(tscale['cn'] * 0.72)}px;color:#2a241a}}"
            f"#{base} .bar{{display:inline-block;height:{bh}px;background:#b3271c;"
            f"vertical-align:middle;border-radius:3px}}")
        html.append(f'<div class="bars" id="{base}" data-layout-allow-overlap data-layout-allow-occlusion>{rows}</div>')
        for i in range(len(dev["bars"])):
            events.append((f"#{base}-b{i}", "underline", 0.0, f"d{i+1}"))

    return css, html, events
