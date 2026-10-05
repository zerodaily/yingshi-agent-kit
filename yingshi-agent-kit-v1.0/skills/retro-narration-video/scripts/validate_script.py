#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口播稿硬规则校验（TTS 之前的最后一道闸）。

检查 audio/chapters.json，规则来源：SKILL.md 关键规则 + 脚本去AI味规则。
硬错误 -> exit 1（必须修完才能进 TTS）；警告 -> exit 0（建议修）。

用法：
    python validate_script.py <项目目录> [--strict]
    --strict：警告也视为失败
"""
import json
import os
import re
import sys

HARD_PATTERNS = [
    ("〇", "年份用了「〇」，必须改成「零」（如二零二四），否则 TTS 读错"),
    (r"[#*_`>]", "正文含 Markdown 符号（# * _ ` >）"),
    (r"[（）()【】\[\]]", "正文含括号（中/英文/方括号全禁）"),
    (r"[—–]", "正文含破折号（一律删掉或改写）"),
]

AI_CLICHES = [
    "值得一提的是", "总而言之", "综上所述", "不仅", "而且",
    "众所周知", "毋庸置疑", "换句话说",
]

GREETING = "欢迎回来，我是言同学。"
ENDING_1 = "好了，今天的故事就到这里。我是言同学，我们下辆车再见。"
ENDING_2 = "对了，你最想让我讲哪台车？评论区告诉我。"


def sentences(text):
    parts = re.split(r"[。！？…～\n]+", text)
    return [s.strip() for s in parts if s.strip()]


def validate(chapters):
    errors = []
    warnings = []
    for pat, msg in HARD_PATTERNS:
        for c in chapters:
            m = re.search(pat, c["text"])
            if m:
                ctx = c["text"][max(0, m.start() - 12):m.end() + 12]
                errors.append("[第%d章] %s：…%s…" % (c["idx"], msg, ctx))
    if chapters:
        ch1 = chapters[0]["text"].strip()
        if ch1.startswith(GREETING):
            errors.append("[第1章] 禁止用欢迎语开头：第一句必须是炸弹钩子，第二句再一字不差接" + GREETING)
        elif GREETING not in ch1:
            errors.append("[第1章] hook 之后必须一字不差出现：" + GREETING)
        tail = chapters[-1]["text"].replace(" ", "")
        if ENDING_1.replace(" ", "") not in tail:
            warnings.append("[结尾] 建议以固定话术收尾：" + ENDING_1)
        if ENDING_2.replace(" ", "") not in tail:
            warnings.append("[结尾] 建议加一句互动引导：" + ENDING_2)
    for c in chapters:
        for s in sentences(c["text"]):
            if len(s) > 15:
                warnings.append("[第%d章] 长句 %d 字（建议≤15字拆短）：%s…" % (c["idx"], len(s), s[:22]))
        for cl in AI_CLICHES:
            if cl in c["text"]:
                warnings.append("[第%d章] AI 套话「%s」，建议删掉或改口语" % (c["idx"], cl))
    return errors, warnings


def main():
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    strict = "--strict" in sys.argv
    ch_path = os.path.join(project, "audio", "chapters.json")
    if not os.path.exists(ch_path):
        print("找不到 %s，先跑 parse_script.py" % ch_path, file=sys.stderr)
        sys.exit(2)
    with open(ch_path, encoding="utf-8") as f:
        chapters = json.load(f)
    errors, warnings = validate(chapters)
    for w in warnings:
        print("WARN " + w)
    for e in errors:
        print("ERROR " + e)
    print("\n校验完成：%d 个硬错误，%d 个警告" % (len(errors), len(warnings)))
    if errors or (strict and warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()
