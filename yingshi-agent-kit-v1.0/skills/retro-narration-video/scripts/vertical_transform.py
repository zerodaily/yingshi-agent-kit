#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""横屏 index.html -> 抖音竖屏工程（一键转换，不手改）。

规则来源：references/composition-and-render.md 竖屏工程 + SKILL.md 抖音安全区排版。
  - root/meta/body 1920x1080 -> 1080x1920
  - 所有 font-size x 0.62（round）
  - 横向宽容器（>=1200px 的 width/max-width）压到 950px
  - .inner 横向 padding 压到 54px
  - 复制 assets/illustrations 与根目录 口播拼接.wav
  - 注入安全区参考线（?guide=1 显示：顶部10% / 底部25% / 右侧10% 遮挡区）

用法：
    python vertical_transform.py <项目目录> [--src index.html] [--dst vertical_douyin/index.html]
"""
import argparse
import os
import re
import shutil
import sys

FONT_SCALE = 0.62
WIDE_CONTAINER = 950  # px，文档要求 940-960
INNER_PAD_X = 54      # px

SAFEZONE_CSS = """
.safezone-guide { display:none; position:fixed; inset:0; z-index:9999; pointer-events:none; }
body.guide .safezone-guide { display:block; }
.safezone-guide .top { position:absolute; top:0; left:0; right:0; height:10%; background:rgba(255,0,0,.18); }
.safezone-guide .bottom { position:absolute; bottom:0; left:0; right:0; height:25%; background:rgba(255,0,0,.18); }
.safezone-guide .right { position:absolute; top:10%; bottom:25%; right:0; width:10%; background:rgba(255,0,0,.18); }
.safezone-guide .label { position:absolute; color:#c00; font-size:28px; font-family:sans-serif; }
"""
SAFEZONE_HTML = """
<div class="safezone-guide">
  <div class="top"></div><div class="bottom"></div><div class="right"></div>
  <div class="label" style="top:11%;left:20px;">安全区：核心内容放中间 15%-70% 高度</div>
</div>
<script>
if (new URLSearchParams(location.search).get('guide') === '1') document.body.classList.add('guide');
</script>
"""


def scale_fontsize(css):
    def repl(m):
        v = float(m.group(1))
        return "font-size:%dpx" % round(v * FONT_SCALE)
    return re.sub(r"font-size:\s*([\d.]+)px", repl, css)


def narrow_wide(css):
    def repl(m):
        prop, v = m.group(1), float(m.group(2))
        if v >= 1200:
            return f"{prop}:{WIDE_CONTAINER}px"
        return m.group(0)
    return re.sub(r"((?:max-)?width):\s*([\d.]+)px", repl, css)


def fix_inner_padding(css):
    # .inner { ... padding: 110px 170px; ... } -> 横向压到 54px，纵向按比例
    def repl(m):
        top, right = float(m.group(1)), float(m.group(2))
        return "padding:%dpx %dpx" % (round(top * 0.55), INNER_PAD_X)
    return re.sub(r"padding:\s*([\d.]+)px\s+([\d.]+)px", repl, css)


def transform(html):
    # 1. 尺寸：1920x1080 -> 1080x1920（meta / css / data 属性）
    html = html.replace("width=1920, height=1080", "width=1080, height=1920")
    html = re.sub(r"width:\s*1920px", "width:1080px", html)
    html = re.sub(r"height:\s*1080px", "height:1920px", html)
    html = html.replace('data-width="1920"', 'data-width="1080"')
    html = html.replace('data-height="1080"', 'data-height="1920"')

    # 2. 字号 x0.62
    html = scale_fontsize(html)
    # 3. 宽容器压到 950
    html = narrow_wide(html)
    # 4. inner padding
    html = fix_inner_padding(html)

    # 5. 安全区参考线（默认隐藏，?guide=1 显示）
    if "safezone-guide" not in html:
        html = html.replace("</style>", SAFEZONE_CSS + "</style>")
        html = html.replace("</body>", SAFEZONE_HTML + "\n</body>")
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="项目根目录（含横屏 index.html）")
    ap.add_argument("--src", default="index.html")
    ap.add_argument("--dst", default=os.path.join("vertical_douyin", "index.html"))
    args = ap.parse_args()

    src = os.path.join(args.project, args.src)
    dst = os.path.join(args.project, args.dst)
    if not os.path.exists(src):
        print(f"找不到横屏工程：{src}", file=sys.stderr)
        sys.exit(1)

    with open(src, encoding="utf-8") as f:
        html = f.read()
    out = transform(html)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)

    # 复制配图与音频
    for rel in ["assets/illustrations", "口播拼接.wav"]:
        s, d = os.path.join(args.project, rel), os.path.join(args.project, "vertical_douyin", rel)
        if os.path.exists(s):
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
            print("copied", rel)
        else:
            print("WARN 缺少", rel)

    print("竖屏工程已生成：", dst)
    print("浏览器打开加 ?guide=1 可看抖音安全区参考线")


if __name__ == "__main__":
    main()
