#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新项目脚手架：一键搭好硬视产线项目目录（替代"复制已验收工程再改"）。

用法：
    python new_project.py "20261005-丰田-第一集" [--brief "目标时长8分钟，5章"]
目录建在 config projects_root 下：
    <项目>/
      BRIEF.md  notes/研究笔记.md  scripts/  audio/
      assets/illustrations/  renders/  vertical_douyin/  抖音竖屏图集_9x16/
      index.html + compositions/（从 skill 动态纸墨 v2 项目模板复制）
"""
import argparse
import datetime
import os
import shutil
import sys

try:
    from yingshi_config import load_config, cfg_get, expand, skill_root
    _CFG = load_config()
except Exception:
    _CFG = {}

BRIEF_TMPL = """# {name} · BRIEF

- 创建日期：{date}
- 目标时长：{duration}（先定死，再写口播稿）
- 目标平台：B 站长版 / 抖音短版
- 画风：动态纸墨 / Vox 拼贴 / huashu 艺术动态（B 站长片只用动态纸墨）
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="项目目录名，如 20261005-丰田-第一集")
    ap.add_argument("--brief", default="8分钟，5章", help="目标时长与章节")
    ap.add_argument("--root", default=None, help="覆盖 projects_root")
    args = ap.parse_args()

    root = expand(args.root or (cfg_get(_CFG, "projects_root", ".") if _CFG else "."))
    proj = os.path.join(root, args.name)
    if os.path.exists(proj):
        print(f"项目已存在：{proj}", file=sys.stderr)
        sys.exit(1)

    for d in ["scripts", "audio", "assets/illustrations", "assets/vendor", "compositions", "notes",
              "renders", "vertical_douyin", "抖音竖屏图集_9x16"]:
        os.makedirs(os.path.join(proj, d), exist_ok=True)

    with open(os.path.join(proj, "BRIEF.md"), "w", encoding="utf-8") as f:
        f.write(BRIEF_TMPL.format(
            name=args.name,
            date=datetime.date.today().isoformat(),
            duration=args.brief,
        ))
    with open(os.path.join(proj, "notes", "研究笔记.md"), "w", encoding="utf-8") as f:
        f.write(f"# {args.name} · 研究笔记\n\n（品牌/车型历史调研贴这里，写口播稿前先沉淀事实）\n")

    template_dir = os.path.join(skill_root(), "assets", "starter_retro_v2")
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

    print("项目已创建：", proj)
    print("下一步：填 BRIEF.md 的目标时长与章节结构，然后写 scripts/视频脚本_版本A.md")


if __name__ == "__main__":
    main()
