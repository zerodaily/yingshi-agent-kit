#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新项目脚手架：一键搭好硬视产线项目目录（替代"复制已验收工程再改"）。

用法：
    # 路线 1 口播产线（A1/A2/A3）
    python new_project.py "20261005-丰田-第一集" --style A1 --brief "8分钟，5章"
    python new_project.py "20261110-冷知识-vox" --style vox --brief "90秒"

    # 路线 2 无口播音乐驱动（B/C）
    python new_project.py "20261110-红皇后-vibe" --style vibe --brief "红皇后效应"

    # 不给 --style：从项目名 + --need + --brief 自动识别，识别不到才回落 A1（会打印警告）
    python new_project.py "20261110-幸存者偏差" --need "讲幸存者偏差，不要口播"

目录建在 config projects_root 下。两条路线目录结构不同：
    路线 1：scripts/ audio/ assets/illustrations/ compositions/ vertical_douyin/ ...
             index.html（动态纸墨 starter）
    路线 2：notes/ frames/ renders/ film.html + render.py + build.ps1
             不建 vertical_douyin、不出封面（路线 2 不适用口播产线的硬规则）
"""
import argparse
import datetime
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as styler

try:
    from yingshi_config import load_config, cfg_get, expand, skill_root
    _CFG = load_config()
except Exception:
    _CFG = {}

BRIEF_ROUTE1 = """# {name} · BRIEF

- 创建日期：{date}
- **风格：{code} · {style_name}**（路线 1 口播产线，走 8 步）
- 目标时长：{duration}（先定死，再写口播稿）
- 目标平台：{platform}
- 镜头目标：4–7 秒一镜；5 分钟 ≥45，8 分钟 ≥70
- 章节结构：
  1. （B站：炸弹钩子 → 欢迎语；抖音：炸弹钩子，无欢迎语）
  2.
  3.
  4.
  5. （B站：固定告别句 → 互动问题；抖音：直接互动问题）
- 选题来源/核心资料：
- 封面模板：templateN（1经典 / 2左图右文 / 3沉浸 / 4对比）
- BGM 分类：怀旧 / 史诗感 / 紧张 / 悲伤 / 轻松 / 激昂热血 / 悬疑揭秘
- 配置来源：<skill>/config.json 或 YINGSHI_CONFIG
- 备注：

> 流程顺序：研究 → 口播稿（parse_script.py 自动硬校验）→ 配音 → 出图 →
> vertical_transform.py 转竖屏 → hyperframes check → render → teaser_cut.py 引流片段
"""

BRIEF_ROUTE2 = """# {name} · BRIEF

- 创建日期：{date}
- **风格：{code} · {style_name}**（路线 2 无口播音乐驱动，**不走**口播产线 8 步）
- 主题：{topic}
- **锚词（2–4 字）**：{anchor}
  > 写任何文案之前先定。标准：有代入感 / 能概括整个原理 / 结尾可被重新定义。
- 背景音乐：{music}
- **高潮点（第一个重拍）**：{beat} 秒 = 第 {beat_frame} 帧
  > 换曲必须先用 ffmpeg 实测「换气 + 重拍」，误差 ≤2 帧，不许照抄 17.0。
- 片长：跟随音乐自然收束
- 字幕：约 25–30 句，中文 ≤18 字 + 英文字幕斜体；每句 3–5 秒
- 输出：MP4 1920×1080 30fps，含 BGM 与音效
- 交付：分镜表 + 成片 + 年份/人名/数字/引文核对清单
- 备注：

> 路线 2 不产出抖音竖屏套图与 6 尺寸封面（用户另行要求才出）。
"""


def _need_text(args):
    """拼出用于判断否定口播的原始需求文本。"""
    parts = [args.need or ""]
    if args.need_file:
        try:
            with open(args.need_file, encoding="utf-8") as f:
                parts.append(f.read())
        except Exception:
            pass
    return "\n".join(parts)


def _choose_style(args):
    """返回 (code, 来源说明)。识别不到 → A1 + 警告标记。"""
    code, hits, err = styler.resolve(value=args.style, text=args.need,
                                     path=args.need_file)
    if code:
        if args.style and args.style.strip().upper() == code:
            return code, f"--style {args.style}"
        return code, f"自动识别（命中：{hits[0][2]}）"
    if err:
        print(f"[!] {err}", file=sys.stderr)
        sys.exit(1)

    # 没给 --style 也没命中关键词：从项目名再试一次，最后回落 A1
    code, hits = styler.detect(args.name)
    if code:
        return code, f"自动识别（项目名命中：{hits[0][2]}）"

    # 需求明说不要口播，却回落 A1 = 方向性错误，必须让用户显式指定
    if styler.wants_no_voice(_need_text(args) or args.name):
        print("[!] 需求写了「不要口播」，但没识别出具体风格。\n"
              "    请用 --style B（人文纪录片）或 --style C（3D 科普）重建，"
              "不要落到口播产线。", file=sys.stderr)
        sys.exit(1)

    print("[!] 未识别到风格关键词，按默认 A1 动态纸墨建项目。"
          "如果这不是口播片，请用 --style B/C/vox/huashu 重建。", file=sys.stderr)
    return "A1", "默认（未指定）"


def build_route1(proj, args, code, spec):
    for d in ["scripts", "audio", "assets/illustrations", "assets/vendor", "compositions", "notes",
              "renders", "vertical_douyin", "抖音竖屏图集_9x16"]:
        os.makedirs(os.path.join(proj, d), exist_ok=True)

    template_dir = os.path.join(skill_root(), "assets", spec["scaffold"])
    if os.path.isdir(template_dir):
        shutil.copytree(template_dir, proj, dirs_exist_ok=True)
    else:
        tpl = os.path.join(skill_root(), "assets", "starter_retro_stage_16x9.html")
        if not os.path.exists(tpl):
            tpl = os.path.join(skill_root(), "assets", "starter_index_16x9.html")
        if os.path.exists(tpl):
            shutil.copy2(tpl, os.path.join(proj, "index.html"))

    vendor = os.path.join(skill_root(), "assets", "vendor", "gsap.min.js")
    if os.path.exists(vendor):
        shutil.copy2(vendor, os.path.join(proj, "assets", "vendor", "gsap.min.js"))
        vertical_dir = os.path.join(proj, "vertical_douyin")
        os.makedirs(os.path.join(vertical_dir, "assets", "vendor"), exist_ok=True)
        shutil.copy2(vendor, os.path.join(vertical_dir, "assets", "vendor", "gsap.min.js"))

    vertical_template = os.path.join(skill_root(), "assets", "starter_retro_v2_vertical")
    if os.path.isdir(vertical_template):
        shutil.copytree(vertical_template, os.path.join(proj, "vertical_douyin"),
                        dirs_exist_ok=True)
    else:
        vertical_tpl = os.path.join(skill_root(), "assets", "starter_retro_stage_9x16.html")
        if os.path.exists(vertical_tpl):
            shutil.copy2(vertical_tpl, os.path.join(proj, "vertical_douyin", "index.html"))


def build_route2(proj, args, code, spec):
    for d in ["notes", "frames", "renders"]:
        os.makedirs(os.path.join(proj, d), exist_ok=True)

    starter = os.path.join(skill_root(), "assets", spec["scaffold"] or "starter_style_b")
    if not os.path.isdir(starter):
        print(f"[!] 风格 {code} 的脚手架尚未落地：{starter}", file=sys.stderr)
        print("    目录已建好，但没有可运行的模板；请按 references/style-library.md "
              f"{spec['spec_anchor'] or ''} 手工搭。", file=sys.stderr)
        return False
    for fn in sorted(os.listdir(starter)):
        src = os.path.join(starter, fn)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(proj, fn))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="项目目录名，如 20261005-丰田-第一集")
    ap.add_argument("--style", default=None,
                    help="风格代号或关键词：A1/A2/A3/B/C，或 vox/vibe/huashu/3d科普")
    ap.add_argument("--need", default=None, help="需求原文，用于自动识别风格")
    ap.add_argument("--need-file", default=None, help="需求文件路径，用于自动识别风格")
    ap.add_argument("--brief", default=None, help="目标时长与章节 / 主题一句话")
    ap.add_argument("--topic", default="", help="路线 2：主题")
    ap.add_argument("--anchor", default="", help="路线 2：锚词 2–4 字（写文案前必填）")
    ap.add_argument("--music", default="《千年之后》氛围版（约 2:38）", help="路线 2：背景音乐")
    ap.add_argument("--beat", type=float, default=17.0, help="路线 2：第一个重拍秒数")
    ap.add_argument("--root", default=None, help="覆盖 projects_root")
    args = ap.parse_args()

    code, src = _choose_style(args)
    spec = styler.STYLES[code]

    root = expand(args.root or (cfg_get(_CFG, "projects_root", ".") if _CFG else "."))
    proj = os.path.join(root, args.name)
    if os.path.exists(proj):
        print(f"项目已存在：{proj}", file=sys.stderr)
        sys.exit(1)

    ok = True
    if spec["route"] == 1:
        build_route1(proj, args, code, spec)
    else:
        ok = build_route2(proj, args, code, spec)

    duration = args.brief or ("8分钟，5章" if spec["route"] == 1 else "跟随音乐")
    platform = args.brief or "B 站长版 / 抖音短版"
    if spec["route"] == 1 and args.brief:
        platform = "B 站长版 / 抖音短版"

    tmpl = BRIEF_ROUTE1 if spec["route"] == 1 else BRIEF_ROUTE2
    with open(os.path.join(proj, "BRIEF.md"), "w", encoding="utf-8") as f:
        f.write(tmpl.format(
            name=args.name,
            date=datetime.date.today().isoformat(),
            code=code,
            style_name=spec["name"],
            duration=duration,
            platform=platform,
            topic=args.topic or "（填主题）",
            anchor=args.anchor or "（填 2–4 字锚词）",
            music=args.music,
            beat=f"{args.beat:g}",
            beat_frame=int(round(args.beat * 30)),
        ))
    with open(os.path.join(proj, "notes", "研究笔记.md"), "w", encoding="utf-8") as f:
        subtitle = ("（品牌/车型历史调研贴这里，写口播稿前先沉淀事实）"
                    if spec["route"] == 1 else
                    "（事实/年份/人名/数字的来源链接贴这里，发布前要逐条核对）")
        f.write(f"# {args.name} · 研究笔记\n\n{subtitle}\n")

    print("项目已创建：", proj)
    print(f"风格：{code} · {spec['name']}（{src}）→ 路线 {spec['route']}")
    if spec["route"] == 1:
        print("下一步：填 BRIEF.md 时长与章节，然后写 scripts/视频脚本_版本A.md")
    elif ok:
        print("下一步：")
        print("  1. 填 BRIEF.md 的锚词（写文案之前先定）")
        print("  2. 改 film.html 顶部 CONFIG（字幕表 / 锚词 / 术语 / 高潮秒）")
        print("  3. python render.py        逐帧渲染到 frames/")
        print("  4. powershell build.ps1    合成 MP4（BGM + 冲击音）")


if __name__ == "__main__":
    main()
