#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口播稿硬规则校验（TTS 之前的最后一道闸）。

检查 audio/chapters.json，规则来源：references/script-rules.md
（平台差异、结构、标点、去 AI 味、字数口径）。
硬错误 -> exit 1（必须修完才能进 TTS）；警告 -> exit 0（建议修）。

用法：
    python validate_script.py <项目目录> [--platform bilibili|douyin] [--strict]
    --strict：警告也视为失败
"""
import argparse
import json
import os
import re
import sys

try:
    from yingshi_config import load_config, cfg_get
    _CFG = load_config()
except Exception:
    _CFG = {}

HARD_PATTERNS = [
    ("〇", "年份用了「〇」，必须改成「零」（如二零二四），否则 TTS 读错"),
    ("颜同学", "品牌名错误，必须写「言同学」"),
    (r"[#*_`>]", "正文含 Markdown 符号（# * _ ` >）"),
    (r"[（）()【】\[\]]", "正文含括号（中/英文/方括号全禁）"),
    (r"[—–]", "正文含破折号（一律删掉或改写）"),
]

AI_CLICHES = [
    "值得一提的是", "总而言之", "综上所述", "不仅", "而且",
    "众所周知", "毋庸置疑", "换句话说",
]

GREETING = (cfg_get(_CFG, "fixed_copy.opening_line", "欢迎回来，我是言同学。")
            if _CFG else "欢迎回来，我是言同学。")
ENDING_1 = (cfg_get(_CFG, "fixed_copy.ending_line",
                    "好了，今天的故事就到这里。我是言同学，我们下辆车再见。")
            if _CFG else "好了，今天的故事就到这里。我是言同学，我们下辆车再见。")
ENGAGE_RE = r"评论区|聊聊|你觉得|说说|评论"

LIMITS = {
    "bilibili": {"total": (1500, 2400), "chapter_min": 300},
    "douyin": {"total": (300, 450), "chapter_min": 0},
}


def sentences(text):
    parts = re.split(r"[。！？…～\n]+", text)
    return [s.strip() for s in parts if s.strip()]


def cjk_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def validate(chapters, platform="bilibili"):
    errors = []
    warnings = []
    if platform not in LIMITS:
        raise ValueError("unknown platform: %s" % platform)
    for pat, msg in HARD_PATTERNS:
        for c in chapters:
            m = re.search(pat, c["text"])
            if m:
                ctx = c["text"][max(0, m.start() - 12):m.end() + 12]
                errors.append("[第%d章] %s：…%s…" % (c["idx"], msg, ctx))
    flat = "".join(c["text"] for c in chapters)
    total_cjk = cjk_count(flat)
    lo, hi = LIMITS[platform]["total"]
    if not (lo <= total_cjk <= hi):
        errors.append("[篇幅] %s 需要 %d–%d 个汉字，当前 %d" %
                      (platform, lo, hi, total_cjk))
    chapter_min = LIMITS[platform]["chapter_min"]
    if chapter_min:
        for c in chapters:
            n = cjk_count(c["text"])
            if n < chapter_min:
                errors.append("[第%d章] 至少 %d 字，当前 %d" %
                              (c["idx"], chapter_min, n))

    if chapters:
        ch1 = chapters[0]["text"].strip()
        tail = chapters[-1]["text"].replace(" ", "")
        if platform == "bilibili":
            if ch1.startswith(GREETING):
                errors.append("[第1章] 禁止用欢迎语开头：第一句必须是炸弹钩子，第二句再一字不差接" + GREETING)
            elif GREETING not in ch1:
                errors.append("[第1章] hook 之后必须一字不差出现：" + GREETING)
            if ENDING_1.replace(" ", "") not in tail:
                errors.append("[结尾] 必须一字不差以固定句收尾：" + ENDING_1)
            if not re.search(ENGAGE_RE, tail):
                warnings.append("[结尾] 固定句后建议加一句本集专属互动引导（评论区 / 聊聊 / 你觉得）")
        else:
            if GREETING.replace(" ", "") in flat.replace(" ", ""):
                errors.append("[抖音短版] 禁止出现固定欢迎语：" + GREETING)
            if not re.search(ENGAGE_RE, tail):
                errors.append("[抖音短版] 结尾必须是本集互动问题（评论区 / 聊聊 / 你觉得 / 说说）")
            if ENDING_1.replace(" ", "") in tail:
                errors.append("[抖音短版] 不使用 B 站长片固定告别句")
    for c in chapters:
        for s in sentences(c["text"]):
            if len(s) > 15:
                warnings.append("[第%d章] 长句 %d 字（建议≤15字拆短）：%s…" % (c["idx"], len(s), s[:22]))
        for cl in AI_CLICHES:
            if cl in c["text"]:
                warnings.append("[第%d章] AI 套话「%s」，建议删掉或改口语" % (c["idx"], cl))
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--platform", choices=sorted(LIMITS), default="bilibili")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    project = args.project
    strict = args.strict
    ch_path = os.path.join(project, "audio", "chapters.json")
    if not os.path.exists(ch_path):
        print("找不到 %s，先跑 parse_script.py" % ch_path, file=sys.stderr)
        sys.exit(2)
    with open(ch_path, encoding="utf-8") as f:
        chapters = json.load(f)
    errors, warnings = validate(chapters, platform=args.platform)
    for w in warnings:
        print("WARN " + w)
    for e in errors:
        print("ERROR " + e)
    print("\n校验完成：%d 个硬错误，%d 个警告" % (len(errors), len(warnings)))
    if errors or (strict and warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()
