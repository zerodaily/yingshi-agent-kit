#!/usr/bin/env python3
"""props.py - 代码画道具：信纸 / 蓝图 / 剪报。

为什么不用 AI 生成：图像模型画不出真文字，铺满面板的假字就是"乱码"。
这类"带字的道具"一律用 HTML/CSS 画——文字可控、字号可读、风格统一。

build_film 里 story 的 what 写成 "draw:letter" / "draw:blueprint" / "draw:newspaper"
就会走这里。
"""
from __future__ import annotations


def build(kind: str, params: dict, sid: str, orient: str, W: int, H: int,
          tscale: dict) -> tuple[list, list, list]:
    px = lambda f, b: int(round(f * b))  # noqa: E731
    css: list[str] = []
    html: list[str] = []
    events: list[tuple[str, str, float, str]] = []
    base = f"{sid}-prop"
    cn = tscale["cn"]
    big = tscale["big"]

    if kind == "letter":
        w, h = px(0.42, W), px(0.44, H)
        css.append(
            f"#{base}{{position:absolute;left:{px(0.08, W)}px;top:{px(0.22, H)}px;"
            f"width:{w}px;min-height:{h}px;background:#efe7d6;z-index:12;"
            f"box-shadow:0 14px 30px rgba(44,30,14,.38);padding:{int(h*0.10)}px {int(w*0.07)}px}}"
            f"#{base} .hd{{font-family:'Mono',monospace;font-size:{int(cn*0.72)}px;"
            f"letter-spacing:3px;color:#6b6152;border-bottom:2px solid #b9ad93;"
            f"padding-bottom:8px;margin-bottom:{int(h*0.06)}px}}"
            f"#{base} .ln{{height:{max(6,int(cn*0.30))}px;background:#4a4436;opacity:.72;"
            f"margin:{max(8,int(cn*0.34))}px 0;border-radius:2px}}"
            f"#{base} .key{{font-family:'TypeCN',sans-serif;font-weight:700;"
            f"font-size:{int(cn*1.15)}px;color:#23201a;margin:{int(cn*0.5)}px 0}}"
            f"#{base} .st{{position:absolute;right:{int(w*0.07)}px;bottom:{int(h*0.07)}px;"
            f"border:6px solid #a82a1c;color:#a82a1c;font-family:'Mono',monospace;"
            f"font-size:{int(cn*1.4)}px;line-height:1;padding:6px 14px;opacity:.85;"
            f"transform:rotate(-8deg)}}")
        html.append(
            f'<div class="prop" id="{base}">'
            f'<div class="hd">{params.get("head", "PARIS 1963")}</div>'
            f'<div class="ln" style="width:88%"></div>'
            f'<div class="ln" style="width:96%"></div>'
            f'<div class="key">{params.get("key", "车名中间的那个零，是我们的")}</div>'
            f'<div class="ln" style="width:72%"></div>'
            f'<div class="st">{params.get("stamp", "0")}</div></div>')
        events.append((f"#{base}", "scrap", -1.5, "d1"))

    elif kind == "blueprint":
        w, h = px(0.46, W), px(0.40, H)
        grid = px(0.012, W)
        css.append(
            f"#{base}{{position:absolute;left:{px(0.06, W)}px;top:{px(0.20, H)}px;"
            f"width:{w}px;height:{h}px;background:#1d2a3a;z-index:12;"
            f"box-shadow:0 14px 30px rgba(30,22,10,.42);overflow:hidden}}"
            f"#{base} .g{{position:absolute;inset:0;opacity:.30;"
            f"background-image:linear-gradient(#8fb0d0 1px,transparent 1px),"
            f"linear-gradient(90deg,#8fb0d0 1px,transparent 1px);"
            f"background-size:{grid}px {grid}px}}"
            f"#{base} .body{{position:absolute;left:12%;right:12%;top:36%;height:26%;"
            f"border:3px solid #dfe9f5;border-radius:6px 22px 22px 6px}}"
            f"#{base} .w1,#{base} .w2{{position:absolute;width:12%;height:12%;"
            f"border:3px solid #dfe9f5;border-radius:50%;top:52%}}"
            f"#{base} .w1{{left:16%}}#{base} .w2{{right:16%}}"
            f"#{base} .cap{{position:absolute;left:12%;bottom:8%;font-family:'Mono',monospace;"
            f"font-size:{int(cn*0.66)}px;letter-spacing:2px;color:#dfe9f5;opacity:.9}}")
        html.append(
            f'<div class="prop" id="{base}"><div class="g"></div><div class="body"></div>'
            f'<div class="w1"></div><div class="w2"></div>'
            f'<div class="cap">{params.get("cap", "SEITENANSICHT 1:20")}</div></div>')
        events.append((f"#{base}", "scrap", 1.2, "d1"))

    elif kind == "newspaper":
        w, h = px(0.44, W), px(0.30, H)
        css.append(
            f"#{base}{{position:absolute;left:{px(0.06, W)}px;top:{px(0.26, H)}px;"
            f"width:{w}px;min-height:{h}px;background:#e8e0cc;z-index:12;"
            f"box-shadow:0 12px 26px rgba(44,30,14,.36);padding:{int(h*0.08)}px}}"
            f"#{base} .hl{{font-family:'TypeCN',sans-serif;font-weight:700;"
            f"font-size:{int(cn*1.5)}px;line-height:1.25;color:#23201a;"
            f"border-bottom:3px solid #23201a;padding-bottom:10px;margin-bottom:10px}}"
            f"#{base} .sub{{font-family:'TypeCN',sans-serif;font-size:{int(cn*0.72)}px;"
            f"color:#5a5145;margin-bottom:14px}}"
            f"#{base} .col{{column-count:2;column-gap:18px}}"
            f"#{base} .col i{{display:block;height:{max(6,int(cn*0.26))}px;"
            f"background:#4a4436;opacity:.55;margin:7px 0;border-radius:2px}}")
        rows = "".join('<i style="width:%d%%"></i>' % n for n in (100, 94, 88, 96, 72))
        html.append(
            f'<div class="prop" id="{base}">'
            f'<div class="hl">{params.get("headline", "保时捷可能被出售")}</div>'
            f'<div class="sub">{params.get("sub", "一九九三年 · 销量下滑")}</div>'
            f'<div class="col">{rows}</div></div>')
        events.append((f"#{base}", "scrap", -1.0, "d1"))

    return css, html, events
