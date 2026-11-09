#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""硬视风格路由（风格选择的唯一机器可读权威）。

用途：
  1) 从一句话 / 一个需求文件里识别该走哪条产线（vox → A2，vibe → B …）
  2) 列出全部风格、打印某一风格的完整规格（正文实时取自 style-library.md，不复制内容）

用法：
    python style.py list
    python style.py show B
    python style.py detect "用 vibe 风格做个红皇后效应的片子"
    python style.py detect --file BRIEF.md
    python style.py detect --brief "3D 科普，讲 GitHub"

退出码：
    0  识别成功
    1  无法识别（需显式 --style）
    2  歧义（命中多个同等具体的风格）
"""
import argparse
import os
import re
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(SKILL_ROOT, "references", "style-library.md")

# 风格路由表 = 关键词 → 产线。aliases 越具体越长，匹配时长词优先。
STYLES = {
    "B": {
        "route": 2,
        "name": "人文纪录片（纸面 2D · 锚词法 · 音乐驱动）",
        "scaffold": "starter_style_b",
        "spec_anchor": "# 风格 B",
        "aliases": ["vibe", "人文纪录片", "纪录片风格", "纪录片", "锚词", "纸面动画",
                    "羊皮纸", "宣纸", "抽象原理", "心理学", "社会现象", "反直觉",
                    "红皇后", "幸存者偏差", "沉没成本"],
        "note": "无口播，字幕承担叙事；第 17 秒砸锚词。",
    },
    "C": {
        "route": 2,
        "name": "3D 科普电影（three.js · 音乐驱动）",
        "scaffold": None,
        "spec_anchor": "# 风格 C",
        "aliases": ["3d科普", "3d 科普", "三维科普", "科普电影", "three.js", "threejs",
                    "电影感", "粒子", "辉光", "太空背景"],
        "note": "无口播；第 17 秒揭晓核心拆解。脚手架尚未落地（只有规则）。",
    },
    "A2": {
        "route": 1,
        "name": "Vox 拼贴（口播 · 桌面拼贴）",
        "scaffold": "starter_retro_v2",
        "spec_anchor": None,
        "aliases": ["vox拼贴", "vox 拼贴", "vox风格", "vox 风格", "vox", "拼贴风",
                    "拼贴", "剪报", "报纸拼贴"],
        "note": "有口播；60–180 秒硬核解释、反常识冷知识。镜头语法见 visual-craft.md §6.2",
    },
    "A3": {
        "route": 1,
        "name": "huashu 艺术动态（口播 · 快节奏）",
        "scaffold": "starter_retro_v2",
        "spec_anchor": None,
        "aliases": ["huashu", "花叔", "艺术动态", "视觉冲击", "快节奏短片"],
        "note": "有口播；15–180 秒视觉冲击强的实验短片。语法见 visual-craft.md §6.3",
    },
    "A1": {
        "route": 1,
        "name": "动态纸墨（口播 · 默认主产线）",
        "scaffold": "starter_retro_v2",
        "spec_anchor": None,
        "aliases": ["动态纸墨", "纸墨", "口播", "品牌史", "人物传记", "汽车历史",
                    "长视频", "b站长版"],
        "note": "有口播（IndexTTS2），5–8 分钟；B 站长片默认用这条。",
    },
}

ORDER = ["A1", "A2", "A3", "B", "C"]

# 「不要口播 / 无口播」里的「口播」不能当成 A1 的正面命中
NEG_VOICE = ("不要口播", "无口播", "不用口播", "没有口播", "不带口播",
             "不配音", "不配旁白", "不用配音")


def _norm(s):
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    return s


def detect(text):
    """返回 (code, hits)。hits 为 [(alias_len, code, alias)] 降序。"""
    t = _norm(text)
    no_voice = any(_norm(n) in t for n in NEG_VOICE)
    hits = []
    for code, spec in STYLES.items():
        for alias in spec["aliases"]:
            # 用户明确说「不要口播」时，口播类关键词不参与匹配
            if code == "A1" and no_voice and "口播" in _norm(alias):
                continue
            if _norm(alias) in t:
                hits.append((len(_norm(alias)), code, alias))
    if not hits:
        return None, []
    hits.sort(key=lambda x: -x[0])
    top_len = hits[0][0]
    winners = {h[1] for h in hits if h[0] == top_len}
    if len(winners) > 1:
        return None, hits            # 歧义
    return hits[0][1], hits


def wants_no_voice(text):
    """需求里是否明确「不要口播」——用来拦住误回落 A1。"""
    t = _norm(text or "")
    return any(_norm(n) in t for n in NEG_VOICE)


def resolve(value=None, text=None, path=None):
    """把 --style 的值或需求文本/文件解析成代号。返回 (code, hits, err)。"""
    if value:
        v = value.strip()
        if v.upper() in STYLES:
            return v.upper(), [], None
        code, hits = detect(v)
        if code:
            return code, hits, None
        return None, [], f"无法识别的风格：{v}（可选 {', '.join(ORDER)}）"

    src = text
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                src = (src or "") + "\n" + f.read()
        except Exception as e:
            return None, [], f"读取需求文件失败：{e}"

    if not src:
        return None, [], None

    code, hits = detect(src)
    if code:
        return code, hits, None
    if hits:
        cands = sorted({h[1] for h in hits})
        return None, hits, f"命中多个风格（{', '.join(cands)}），请显式 --style"
    return None, [], None


def extract_spec(code):
    """从 style-library.md 实时抽取该风格段落（单一权威，不做副本）。"""
    anchor = STYLES[code]["spec_anchor"]
    if not anchor or not os.path.exists(LIB):
        return ""
    with open(LIB, encoding="utf-8") as f:
        lines = f.read().splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith(anchor))
    except StopIteration:
        return ""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("# 风格 ") or lines[i].startswith("# 风格库"):
            end = i
            break
    return "\n".join(lines[start:end]).rstrip()


def cmd_list():
    print("代号  路线  风格                                      脚手架")
    print("-" * 74)
    for c in ORDER:
        s = STYLES[c]
        sc = s["scaffold"] or "（未落地）"
        print(f"{c:<5} {s['route']:<4} {s['name']:<40} {sc}")
    print("\n路线 1 = 口播产线（IndexTTS2 + HyperFrames，8 步）")
    print("路线 2 = 无口播音乐驱动（字幕叙事，逐帧渲染）")


def cmd_show(code):
    code = code.upper()
    if code not in STYLES:
        print(f"未知风格：{code}；可选 {', '.join(ORDER)}", file=sys.stderr)
        sys.exit(1)
    s = STYLES[code]
    print(f"# 风格 {code} · {s['name']}")
    print(f"- 路线：{s['route']}（{'口播产线 8 步' if s['route']==1 else '无口播音乐驱动'}）")
    print(f"- 脚手架：{s['scaffold'] or '（尚未落地，只有规则）'}")
    print(f"- 触发词：{'、'.join(s['aliases'])}")
    print(f"- 摘要：{s['note']}")
    spec = extract_spec(code)
    if spec:
        print("\n" + "-" * 40 + " 规格正文（取自 style-library.md）" + "-" * 40 + "\n")
        print(spec)
    else:
        ref = "visual-craft.md §6.2/§6.3" if code in ("A2", "A3") else "SKILL.md 路线 1"
        print(f"\n完整细则见 {ref}")

    if code == "B":
        print("\n" + "-" * 40 + " 质感档位（vibe-style-spec.md）" + "-" * 40)
        print("  P1 parchment  羊皮纸·默片  暖黄纸 / 深褐墨 / 字幕居中（默认）")
        print("  P2 linen      宣纸·单墨    近白纸 / 乌黑墨 / 一点朱红 / 字幕偏左")
        print("  P3 archive    旧报·档案    灰绿纸 / 重颗粒 / 深暗角 / 暗红点睛")
        print("  用法：film.html 里 CONFIG.look 改成档位名；CONFIG.camZoom 控制镜头推进（0 = 静止）")
        print("  说清一支 vibe 的公式：[档位] + [节奏] + [图形语言] + [一条特殊要求]")


def cmd_detect(args):
    src = args.text
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                src = (src or "") + "\n" + f.read()
        except Exception as e:
            print(f"读取失败：{e}", file=sys.stderr)
            sys.exit(1)
    if args.brief:
        src = (src or "") + "\n" + args.brief
    if not src:
        print("需要一句话、--file 或 --brief 之一", file=sys.stderr)
        sys.exit(1)

    code, hits = detect(src)
    if code:
        print(f"{code}\t{STYLES[code]['name']}")
        for ln, c, a in hits[:5]:
            print(f"  hit: {a} → {c}", file=sys.stderr)
        return
    if hits:
        cands = sorted({h[1] for h in hits})
        print(f"AMBIGUOUS\t{', '.join(cands)}", file=sys.stderr)
        sys.exit(2)
    print("UNKNOWN\t未识别到风格关键词，请显式 --style " + "/".join(ORDER), file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="硬视风格路由")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="列出全部风格")

    p = sub.add_parser("show", help="打印某风格的完整规格")
    p.add_argument("code")

    p = sub.add_parser("detect", help="从文本/文件识别风格")
    p.add_argument("text", nargs="?", default=None)
    p.add_argument("--file", default=None, help="需求文件或 BRIEF.md")
    p.add_argument("--brief", default=None, help="补充描述")

    args = ap.parse_args()
    if args.cmd == "list":
        cmd_list()
    elif args.cmd == "show":
        cmd_show(args.code)
    elif args.cmd == "detect":
        cmd_detect(args)


if __name__ == "__main__":
    main()
