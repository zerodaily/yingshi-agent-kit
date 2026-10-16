#!/usr/bin/env python3
"""plan_scenes.py - 按转写自动排分镜（长片的命脉）。

输入：转写 + 元素库 + 章节表；输出：film.json（交给 build_film.py）。

1. 按目标秒数切场景（默认 4 秒一场）
2. 旁白里点名了哪个型号，就优先上同名元素
3. 角色轮换：实物当主图、地图当衬底、人物每 N 场一次
4. 从文本抠年份与型号做标签（粗提，出片前人工过一遍）
5. 章节开头插章节卡，时间轴整体后移
"""
from __future__ import annotations

import argparse
import json
import os
import re

try:
    import shotgram
except Exception:  # noqa: BLE001
    shotgram = None

try:
    import devices
except Exception:  # noqa: BLE001
    devices = None

YEAR_RE = re.compile(r"[一二三四五六七八九零]{4}年")
SPEC_RE = re.compile(r"[0-9]{2,4}|[A-Za-z][A-Za-z0-9]{1,8}")

TOKEN_HINTS = {
    "p901_1963": ["九零一", "901"],
    "p911_1965": ["九一一", "911"],
    "p911_1968": ["九一一", "911"],
    "p911_sc": ["九一一", "911"],
    "p356": ["三五六", "356"],
    "p356_speedster": ["三五六", "356", "敞篷"],
    "p930_turbo": ["九三零", "930", "涡轮"],
    "p964": ["九六四", "964"],
    "p993": ["九九三", "993"],
    "p993_turbo": ["九九三", "993"],
    "p996": ["九九六", "996"],
    "p992": ["九九二", "992"],
    "p917": ["九一七", "917"],
    "p956": ["九五六", "956"],
    "p918": ["九一八", "918"],
    "p919": ["九一九", "919"],
    "boxster": ["博克斯特"],
    "carrera_gt": ["卡雷拉"],
    "panamera": ["帕纳梅拉"],
    "beetle": ["甲壳虫"],
    "peugeot": ["标致"],
    "lemans_map": ["勒芒"],
    "museum": ["博物馆"],
}


def load_elements(elements_dir):
    man = os.path.join(elements_dir, "manifest.json")
    roles = {"object": [], "portrait": [], "map": [], "scrap": []}
    if os.path.exists(man):
        data = json.load(open(man, encoding="utf-8"))
        for e in data.get("elements", []):
            roles.setdefault(e.get("role", "object"), []).append(e["name"])
    else:
        for fn in sorted(os.listdir(elements_dir)):
            if fn.endswith(".png") and not fn.startswith("_"):
                roles["object"].append(os.path.splitext(fn)[0])
    return roles


def pick_hero(text, objects, i):
    for name in objects:
        for hint in TOKEN_HINTS.get(name, []):
            if hint in text:
                return name
    return objects[i % len(objects)] if objects else ""


def label_from_text(text, fallback_big):
    year = YEAR_RE.search(text)
    spec = SPEC_RE.search(text)
    big = year.group(0) if year else (spec.group(0) if spec else fallback_big)
    small = spec.group(0).upper() if spec else "ARCHIVE"
    first = re.split(r"[，。！？、]", text)[0]
    first = re.sub(r"\s+", "", first)
    return ({"big": big, "small": small}, first[:14])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--elements", required=True)
    ap.add_argument("--chapters", default=None)
    ap.add_argument("--timeline", default=None,
                    help="章节起始时间表（chapters.json 没有 start 时读它）")
    ap.add_argument("--slots", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scene", type=float, default=4.0)
    ap.add_argument("--chapter-card", type=float, default=3.0)
    ap.add_argument("--portrait-every", type=int, default=6)
    ap.add_argument("--density", choices=["normal", "dense"], default="dense",
                    help="dense: 每场至少两个实物元素并补胶带，画面更满")
    args = ap.parse_args()

    ref = json.load(open(args.slots, encoding="utf-8"))
    segs = json.load(open(args.transcript, encoding="utf-8")).get("segments", [])
    if not segs:
        raise SystemExit("transcript has no segments")
    roles = load_elements(args.elements)
    objects = roles["object"] or roles["scrap"]
    maps = roles["map"] or roles["scrap"] or objects
    portraits = roles["portrait"]

    chapters = []
    if args.chapters and os.path.exists(args.chapters):
        chapters = json.load(open(args.chapters, encoding="utf-8"))
    tl_path = args.timeline or (os.path.join(os.path.dirname(args.chapters),
                                             "timeline.json") if args.chapters else None)
    if chapters and "start" not in chapters[0] and tl_path and os.path.exists(tl_path):
        tl = json.load(open(tl_path, encoding="utf-8"))
        for c, t in zip(chapters, tl):
            c["start"] = t.get("start", 0.0)
    ch_starts = [(float(c["start"]), c) for c in chapters if "start" in c]

    starts = [cs for cs, _ in ch_starts]

    def is_ch_start(t0):
        return any(abs(t0 - cs) < 1.2 for cs in starts[1:])

    # 镜头时长由文本密度决定（短句快切、长句给足），但场景边界始终贴住旁白时间轴
    beats = []
    buf = []
    for si, seg in enumerate(segs):
        buf.append(seg)
        t0 = float(buf[0]["start"])
        span = float(buf[-1]["end"]) - t0
        text = "".join(x["text"] for x in buf)
        nxt_ch = si + 1 < len(segs) and is_ch_start(float(segs[si + 1]["start"]))
        target = (shotgram.planned_shot_len(text, args.scene, is_ch_start(t0), nxt_ch)
                  if shotgram else args.scene)
        last = si == len(segs) - 1
        if span < target - 0.7 and not last:
            continue
        cps = len(re.sub(r"\s+", "", text)) / max(1.0, span)
        beats.append({"text": text, "start": t0, "dur": span,
                      "ch_start": is_ch_start(t0), "ch_end": nxt_ch,
                      "dense": cps > 5.9})
        buf = []

    # 镜头规格：景别 / 机位 / 运动 / 构图 / 转场
    # 先把过短的镜头并进下一场（避免 1 秒闪帧）
    merged = []
    for b in beats:
        if merged and (merged[-1]["dur"] < 2.0 or b["dur"] < 2.0):
            merged[-1]["text"] += b["text"]
            merged[-1]["dur"] = (b["start"] + b["dur"]) - merged[-1]["start"]
            merged[-1]["ch_end"] = b["ch_end"]
            continue
        merged.append(b)
    beats = merged

    if shotgram:
        prev = None
        for i, b in enumerate(beats):
            b["shot"] = shotgram.assign(b["text"], i, prev, b["ch_start"],
                                        b["ch_end"], b["dense"])
            prev = b["shot"]

    # 视觉诠释：把"意思"翻成画面装置（改名、判决、数字、年表、因果、对比）
    if devices:
        for b in beats:
            b["device"] = devices.detect(b["text"], b.get("ch_start", False))

    cards = []
    for idx, (cs, c) in enumerate(ch_starts):
        if idx == 0:
            continue
        cards.append({"at": cs, "no": "%02d" % c.get("idx", idx + 1),
                      "title": c.get("title", "")})

    out_scenes = []
    n = 0
    ci = 0
    for beat in beats:
        # 章节卡是叠加层：放在 track 2，与画面同时进行，不推迟旁白
        while ci < len(cards) and cards[ci]["at"] <= beat["start"] + 1e-6:
            out_scenes.append({
                "id": "c%03d" % n,
                "start": round(cards[ci]["at"], 3),
                "track": 2,
                "duration": args.chapter_card,
                "chapter": {"no": cards[ci]["no"], "title": cards[ci]["title"]},
            })
            n += 1
            ci += 1
        hero = pick_hero(beat["text"], objects, n)
        cast = {"hero": hero, "scrap": maps[n % len(maps)]}
        if portraits and n % args.portrait_every == args.portrait_every - 1:
            cast["portrait"] = portraits[(n // args.portrait_every) % len(portraits)]
        dense = args.density == "dense"
        if len(objects) > 1 and (dense or n % 3 == 1):
            cast["mini"] = objects[(n * 3 + 1) % len(objects)]
        if dense and n % 3 == 1:
            cast["scrap2"] = maps[(n * 5 + 2) % len(maps)]
        lab, note = label_from_text(beat["text"], "%04d" % n)
        sc = {"id": "n%03d" % n, "start": round(beat["start"], 3),
              "duration": round(beat["dur"], 3), "cast": cast,
              "label1": lab, "label2": note}
        if beat.get("shot"):
            sc["_shot"] = beat["shot"]
        if beat.get("device"):
            sc["_device"] = beat["device"]
        if dense:
            sc["tape"] = ["tape0"] if n % 2 else ["tape1"]
            if n % 3 == 0:
                sc["tape"].append("tape0")
                sc["stamp"] = "档案"
            if n % 4 == 2:
                sc["underline"] = True
            if n % 6 == 3:
                sc["string"] = ["pinA", "pinB", "pinC"]
        else:
            if n % 4 == 0:
                sc["stamp"] = "档案"
            if n % 5 == 2:
                sc["underline"] = True
            if n % 6 == 3:
                sc["string"] = ["pinA", "pinB", "pinC"]
        out_scenes.append(sc)
        n += 1

    film = {
        "title": ref.get("title", "") + " auto",
        "audio": ref.get("audio", "口播混音.wav"),
        "element_shadow": ref.get("element_shadow", "baked"),
        "duration": round(out_scenes[-1]["start"] + out_scenes[-1]["duration"], 3),
        "canvas": ref["canvas"], "type": ref["type"], "plate": ref["plate"],
        "slots": ref["slots"], "scenes": out_scenes,
    }
    if ref.get("bgm"):
        film["bgm"] = ref["bgm"]
    json.dump(film, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    names = set(objects) | set(maps) | set(portraits)
    print("%s  scenes=%d  chapters=%d  %.1fs (%.1f min)  elements=%d"
          % (args.out, len(out_scenes), len(cards), film["duration"],
             film["duration"] / 60, len(names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
