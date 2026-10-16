#!/usr/bin/env python3
"""make_story_film.py - 把「叙事单元表」展开成完整分镜（覆盖镜头）。

一个叙事单元 = 一组覆盖镜头：
  1 环境镜头（先交代在哪）
  2 人物镜头（谁在场）
  3 主体镜头（发生了什么）
  4 结果镜头（事件文字 / 装置）
这样 40 来个叙事单元就能展开成 140+ 个镜头，既有故事逻辑，也有镜头节奏。
"""
import io
import json
import os
import sys

# 每章：起始秒、时长、以及本章的叙事单元
# 单元 = (场景件, [人物], 主体, 事件文字, 年份, 角标, 装置)
CHAPTERS = [
    (0.0, 86.05, [
        ("scene_motorshow", [], "p901_1963", "一九六三年九月 · 法兰克福车展的角落", "1963", "FRANKFURT", None),
        ("scene_workshop", ["role_engineer"], "p901_1963", "车身很低，尾巴上顶着一台发动机", "901", "REAR ENGINE", None),
        (None, [], "p911_1965", "六十年后 · 它卖出了一百万台", "1,000,000", "SOLD", {"type": "counter", "value": 1000000, "unit": "台"}),
        ("scene_motorshow", [], "p901_1963", "一台叫九零一的新车", "901", "DEBUT", None),
        ("scene_office_stuttgart", [], "draw:letter", "标致抗议：中间那个零是我们的", "1963", "PARIS", None),
        (None, [], "p911_1965", "把零改成一 · 九零一变九一一", "911", "RENAMED", {"type": "substitute", "old": "901", "new": "911"}),
        ("scene_road", [], "p911_1968", "如果当年改成八八八", "1963", "WHAT IF", None),
        ("scene_factory", ["role_owner"], "p911_sc", "那年展台没人排队，机会是后来挣的", "1963", "EMPTY HALL", None),
        ("scene_drawing", ["role_engineer"], "draw:blueprint", "德国跑车市场很小，它本来是小众里的小众", "1963", "NICHE", None),
    ]),
    (86.05, 75.87, [
        ("scene_drawing", ["person_ferdinand"], "beetle", "一九三零年代 · 甲壳虫，发动机就在后面", "1930", "BEETLE", None),
        ("scene_road", ["person_ferry"], "p356", "一九四八年 · 费里拿出一台叫三五六的小跑车", "1948", "356", None),
        ("scene_showroom", ["role_owner"], "p356_speedster", "三五六卖得很好", "1948", "SOLD WELL", None),
        (None, [], "p356", "有人说：这不就是换了壳的大众吗", "1950s", "CRITICISM", {"type": "highlight", "word": "换壳"}),
        ("scene_drawing", ["person_ferry", "person_butzi"], "draw:blueprint", "费里让儿子布齐画一台真正属于自己的车", "1959", "HANDOVER", None),
        ("scene_factory", [], "p901_1963", "四年时间，内部吵过很多次", "1963", "FOUR YEARS", {"type": "timeline", "years": [1959, 1961, 1963]}),
    ]),
    (161.92, 77.54, [
        ("scene_workshop", ["role_engineer"], "p930_turbo", "后置发动机：不用长传动轴，又轻又压得住后轮", "TECH", "REAR", None),
        ("scene_road", ["role_driver"], "p911_1968", "代价是车尾容易甩出去", "RISK", "OVERSTEER", {"type": "verdict", "word": "危险"}),
        ("scene_boardroom", [], "draw:blueprint", "七十年代想过把发动机挪到中间，算完账放弃了", "1970s", "REJECTED", None),
        ("scene_workshop", [], "p964", "风冷：没有水箱水泵，冬天也不怕冻", "AIR", "AIR COOLED", None),
        (None, ["role_engineer"], "p911_sc", "别人早改水冷，保时捷一直拖到一九九八", "1998", "LAST AIR", {"type": "timeline", "years": [1963, 1973, 1989, 1998]}),
    ]),
    (239.46, 72.96, [
        (None, [], "p930_turbo", "一九七四年 · 把涡轮装上去，马力翻倍", "1974", "930 TURBO", None),
        ("scene_track", ["role_driver"], "p930_turbo", "涡轮介入很突然，脚一抖车就横过来", "1975", "SNAP", None),
        ("scene_showroom", ["role_owner"], "p964", "一九八九年的九六四 · 四驱、助力转向、气囊", "1989", "964", None),
        (None, ["role_owner"], "p993", "一九九三年的九九三 · 最后一台风冷", "1993", "993", {"type": "highlight", "word": "最后一台"}),
        ("scene_workshop", [], "p993_turbo", "一九九八年停产 · 风冷的故事结束", "1998", "THE END", {"type": "verdict", "word": "停产"}),
    ]),
    (312.42, 75.09, [
        ("scene_showroom", [], "p964", "八十年代后期 · 为了多卖车，做了一些不像保时捷的东西", "1980s", "DRIFT", None),
        ("scene_office_stuttgart", [], "draw:newspaper", "美国经济放慢，日本泡沫破裂", "1990", "MARKETS", None),
        ("scene_factory", ["role_engineer"], "p993", "一年只卖出一万多台车", "1993", "14,000", {"type": "counter", "value": 14000, "unit": "台"}),
        ("scene_boardroom", [], "draw:newspaper", "业内传：保时捷可能被卖掉", "1993", "FOR SALE?", {"type": "verdict", "word": "危机"}),
        ("scene_boardroom", ["role_engineer"], "draw:blueprint", "一九九三年换帅 · 做便宜入门车，让九一一跟它共用零件", "1993", "TURNING", None),
    ]),
    (387.51, 83.16, [
        (None, [], "p996", "一九九七年 · 第一台水冷九一一上市", "1997", "996", None),
        ("scene_showroom", [], "p996", "风冷粉丝当场炸了", "1997", "OUTRAGE", {"type": "verdict", "word": "争议"}),
        (None, [], "p996", "共用发动机、炒蛋大灯，被骂成背叛", "1997", "BETRAYAL", None),
        ("scene_showroom", ["role_owner"], "boxster", "买得最多的是新客户：更好开、故障更少", "1999", "SALES BACK", {"type": "bars", "bars": [{"label": "1993", "value": 14000}, {"label": "2000", "value": 50000}]}),
        (None, [], "carrera_gt", "省下的钱养活了卡雷拉 GT、帕纳梅拉、九一八", "2004", "PAYBACK", None),
        ("scene_factory", [], "panamera", "如果当年坚持风冷，公司撑不到现在", "TODAY", "SURVIVED", {"type": "verdict", "word": "活下来"}),
    ]),
    (470.67, 69.63, [
        ("scene_track", ["role_driver"], "p356_speedster", "一九五一年 · 三五六第一次去勒芒就拿下同级冠军", "1951", "FIRST WIN", None),
        ("scene_track", [], "p917", "一九七零年 · 九一七第一次拿下全场冠军", "1970", "917", None),
        (None, [], "p956", "一九八二年 · 九五六上场，气动被所有车队抄", "1982", "956", None),
        ("scene_track", [], "p919", "二零一五到二零一七 · 九一九混动连续三年夺冠", "2015", "919", {"type": "timeline", "years": [1970, 1982, 2015, 2017]}),
        (None, [], "prop_trophy", "到今天 · 勒芒十九次全场冠军", "19", "LE MANS WINS", {"type": "counter", "value": 19, "unit": "次冠军"}),
    ]),
    (540.31, 76.61, [
        (None, [], "p992", "二零一九年 · 九九二上市，二零二四加入混动", "2024", "992 HYBRID", None),
        ("scene_showroom", [], "p992", "位置还是那个位置，还是水平对置六缸", "TODAY", "SAME LAYOUT", None),
        ("scene_drawing", ["role_engineer"], "draw:newspaper", "老车迷又开始担心变味", "TODAY", "WORRY", None),
        ("scene_factory", [], "p911_1965", "二零一七年 · 第一百万台九一一下线", "2017", "1,000,000", {"type": "counter", "value": 1000000, "unit": "台"}),
        ("scene_showroom", ["role_owner"], "p993", "风冷九九三现在比新车还贵", "TODAY", "PRICE", None),
        (None, [], "p992", "它是唯一一台六十年没换过逻辑的跑车", "60", "UNCHANGED", {"type": "highlight", "word": "唯一"}),
    ]),
    (616.92, 89.06, [
        (None, [], "p992", "技术几乎全换过：风冷到水冷、化油器到直喷、自吸到混动", "60 YEARS", "ALL CHANGED", None),
        (None, [], "p911_1965", "但它守住三样：后置发动机、圆灯、下滑的车顶线", "60 YEARS", "THE LINE", {"type": "highlight", "word": "三样"}),
        ("scene_road", ["role_owner"], "p911_sc", "很多人一开就是十几年", "OWNER", "DAILY", None),
        (None, [], "p992", "换别的车总觉得少点什么", "OWNER", "FEELING", None),
        ("scene_factory", [], "draw:blueprint", "一件事能做得久，靠的是知道哪一样不能动", "END", "THE POINT", {"type": "verdict", "word": "不变"}),
    ]),
]

# 覆盖镜头：一个叙事单元展开成 3-4 个镜头（环境 → 人物 → 主体 → 结果）
# show = 这个镜头里出现哪些层：只给该镜头需要的，避免"同样三个元素摆四次"
# 时长权重：交代要慢、细节要快、结果略停；章尾再乘呼吸系数
COVERAGE = [
    ("where",  "LS",     "left",     "drift",  0.32, ["where"]),
    ("who",    "MS",     "right",    "push",   0.20, ["where", "who"]),
    ("what",   "CU",     "center",   "push",   0.30, ["what"]),
    ("event",  "INSERT", "negative", "static", 0.18, ["what"]),
]

# 章节卡：每章开头压一张（track 2 叠加，不占时长）
CHAPTER_CARDS = [
    (86.05, "02", "甲壳虫的儿子"), (161.92, "03", "为什么发动机在后面"),
    (239.46, "04", "风冷的三十年"), (312.42, "05", "差点死掉"),
    (387.51, "06", "九九六的争议"), (470.67, "07", "赛道上的十九次"),
    (540.31, "08", "六十年的固执"), (616.92, "09", "为什么不变反而值钱"),
]


PROP_TEXT = {
    "标致抗议：中间那个零是我们的": {"head": "PARIS · 1963", "key": "车名中间的那个零，是我们的",
                          "stamp": "0"},
    "费里让儿子布齐画一台真正属于自己的车": {"cap": "ENTWURF 1959 · B. PORSCHE"},
    "七十年代想过把发动机挪到中间，算完账放弃了": {"cap": "MITTMOTOR · VERWORFEN"},
    "德国跑车市场很小，它本来是小众里的小众": {"cap": "MARKT · KLEIN"},
    "一九九三年换帅 · 做便宜入门车，让九一一跟它共用零件": {"cap": "PLAN 1993 · GLEICHTEILE"},
    "一件事能做得久，靠的是知道哪一样不能动": {"cap": "DIE LINIE · 1963-2024"},
    "美国经济放慢，日本泡沫破裂": {"headline": "两个市场同时熄火", "sub": "一九九零 · 美国放缓 · 日本泡沫"},
    "业内传：保时捷可能被卖掉": {"headline": "保时捷可能被出售", "sub": "一九九三 · 买家传闻是奔驰"},
    "老车迷又开始担心变味": {"headline": "这还是九一一吗", "sub": "论坛争论 · 从一九九七吵到今天"},
}


def main():
    proj = sys.argv[1] if len(sys.argv) > 1 else "."
    base = json.load(io.open(os.path.join(proj, "film_story.json"), encoding="utf-8"))
    scenes, n = [], 0
    for ci, (ch_start, ch_len, units) in enumerate(CHAPTERS, 1):
        weight = sum(1.0 for u in units)
        t = ch_start
        for ui, (where, who, what, event, year, tag, device) in enumerate(units):
            unit_len = ch_len / weight
            active = []
            for c in COVERAGE:
                kind = c[0]
                if kind == "where" and not where:
                    continue
                if kind == "who" and not who:
                    continue
                if kind == "event" and not device and ui % 2 == 1:
                    continue                       # 装置镜头不必每单元都有
                active.append(c)
            # 单元至少三个镜头，否则一个镜头会吃掉整个单元（出现十几秒的长镜）
            extra = [("what", "CU", "center", "push", 0.30, ["what"]),
                     ("what", "ECU", "right", "drift", 0.24, ["what"]),
                     ("what", "MS", "left", "static", 0.22, ["what"])]
            ei = 0
            while len(active) < 3 and ei < len(extra):
                active.append(extra[ei])
                ei += 1
            share_total = sum(c[4] for c in active) or 1.0
            for kind, scale, comp, move, share, show in active:
                dur = round(unit_len * share / share_total, 2)
                dur = min(dur, 6.5)                # 单镜头上限：长了就靠补镜头分掉
                if dur < 2.2:
                    dur = 2.2
                if t + dur > ch_start + ch_len + 0.01:
                    dur = round(ch_start + ch_len - t, 2) - 0.01   # 别和下一章咬边
                if dur <= 1.0:
                    continue
                n += 1
                focus = {"where": where, "who": (who[0] if who else None),
                         "what": what, "event": what}[kind]
                if focus is None:
                    continue
                sc = {
                    "id": "u%03d" % n, "start": round(t, 3), "duration": dur,
                    "story": {"where": where if kind != "event" else None,
                              "who": (who if kind != "event" else []),
                              "what": focus,
                              "event": event, "year": year, "tag": tag,
                              "show": show},
                    "_shot": {"scale": scale, "angle": "eye", "move": move,
                              "comp": comp,
                              "trans": ("dissolve" if ui == 0 else "cut"),
                              "side": "right"},
                }
                if focus.startswith("draw:"):
                    sc["story"]["prop"] = PROP_TEXT.get(event, {})
                    sc["story"]["what"] = focus
                if kind == "event" and device:
                    sc["_device"] = device
                if kind == "event" and not sc["story"]["where"]:
                    sc["story"].pop("where")
                scenes.append(sc)
                t += dur
    # 章节卡：track 2 叠加，不推迟旁白
    for at, no, title in CHAPTER_CARDS:
        scenes.append({"id": "card%s" % no, "start": at, "duration": 3.0, "track": 2,
                       "chapter": {"no": no, "title": title}})
    scenes.sort(key=lambda s: (s["start"], s.get("track", 1)))
    base["scenes"] = scenes
    track1 = [s for s in scenes if s.get("track", 1) == 1]
    # 1) 先补齐到整条音轨：余量摊给末尾三场（别造出十几秒的长镜头）
    span = sum(s["duration"] for s in track1)
    tail = 706.0 - span
    if tail > 0.5:
        tailers = track1[-3:] if len(track1) >= 3 else track1
        share = tail / len(tailers)
        for s in tailers:
            s["duration"] = round(min(s["duration"] + share, s["duration"] * 1.6), 2)
    # 2) 再顺序重排（起点=上一场结尾），从构造上杜绝重叠与空隙
    cursor = track1[0]["start"] if track1 else 0.0
    for s in track1:
        s["start"] = round(cursor, 3)
        cursor = round(cursor + s["duration"], 3)
    base["duration"] = round(cursor, 3)
    out = os.path.join(proj, "film_story_full.json")
    json.dump(base, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s  scenes=%d  %.1fs (%.1f min)" % (out, len(scenes), base["duration"],
                                               base["duration"] / 60))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
