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

# 篇幅档位（v1.1）。默认目标档是长片；老的一分钟短片走「短片」档，
# 用 --band short 显式声明，避免把既有产线一刀切死。
BANDS = [("long", "长片", 3000, 5000),
         ("mid", "中片", 1200, 2500),
         ("short", "短片", 250, 1000)]
CHAPTER_MIN = 400
# 实测语速（14 集样本平均 5.43 字/秒），用来把字数换算成时长与画面数
CHARS_PER_SECOND = 5.43
SECONDS_PER_SCENE = 4.0
TARGET_BAND = "long"      # 由 --band 覆盖；老项目用 --band short


def sentences(text):
    parts = re.split(r"[。！？…～\n]+", text)
    return [s.strip() for s in parts if s.strip()]


def validate(chapters):
    errors = []
    warnings = []
    total = sum(len(re.sub(r"\s+", "", c["text"])) for c in chapters)
    band = next((b for b in BANDS if b[2] <= total <= b[3]), None)
    target = next((b for b in BANDS if b[0] == TARGET_BAND), BANDS[0])
    in_long = band is not None and band[0] == "long"
    if band is None:
        errors.append("[篇幅] 全文 %d 字，不落在任何档位：%s"
                      % (total, "、".join("%s %d–%d" % (n, lo, hi) for _, n, lo, hi in BANDS)))
    elif band[0] != target[0]:
        warnings.append("[篇幅] 全文 %d 字落在「%s」档；本项目目标档是「%s」（%d–%d 字）"
                        % (total, band[1], target[1], target[2], target[3]))

    if in_long:
        scenes = total / CHARS_PER_SECOND / SECONDS_PER_SCENE
        est_min = total / CHARS_PER_SECOND / 60
        if scenes > 200:
            warnings.append(
                "[篇幅] 预计 %.1f 分钟 / 约 %.0f 个画面：画面数偏多，"
                "必须靠元素库复用 + 场景变体摊薄（见 references/film-json.md）"
                % (est_min, scenes))
        else:
            warnings.append("[篇幅] 预计 %.1f 分钟 / 约 %.0f 个画面" % (est_min, scenes))

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
        clen = len(re.sub(r"\s+", "", c["text"]))
        if in_long and clen < CHAPTER_MIN:
            errors.append("[第%d章] 本章 %d 字，长片每章至少 %d 字"
                          % (c["idx"], clen, CHAPTER_MIN))
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
    global TARGET_BAND
    if "--band" in sys.argv:
        i = sys.argv.index("--band")
        if i + 1 < len(sys.argv):
            TARGET_BAND = sys.argv[i + 1]
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

