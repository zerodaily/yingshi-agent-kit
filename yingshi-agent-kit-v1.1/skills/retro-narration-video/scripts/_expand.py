# -*- coding: utf-8 -*-
"""把四章补到 400 字以上（机械插入，脚本正文是单行长文本，用 apply_patch 不便逐行改）。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "视频脚本_版本A.md")

EDITS = [
    ("九一一的机会，是后面几十年一点点挣回来的。",
     "九一一的机会，是后面几十年一点点挣回来的。"
     "当时德国的跑车市场很小。大家更愿意买便宜的敞篷车，或者干脆买台大轿车。"
     "一台后置发动机的小跑车，听起来像小众里的小众。"),
    ("这两点，被骂了很多年。",
     "这两点，被骂了很多年。论坛上有人写过一句话。"
     "这不是九一一，这是保时捷的背叛。话说得很重。"),
    ("用来补低速的扭矩。",
     "用来补低速的扭矩。电池不大，纯电只能跑很短一段路。"),
    ("剩下的都可以谈。",
     "剩下的都可以谈。还有一个细节。九一一的车主，很多人一开就是十几年。"
     "他们不是买不起别的车。是换了别的车，总觉得少点什么。"
     "有人说是方向盘的手感。有人说是发动机的声音。"
     "也有人说是坐进去之后那种熟悉。这种熟悉，新东西给不了。"),
    ("靠的不是每天都搞新花样，而是知道哪一样不能动。",
     "靠的不是每天搞新花样。靠的是知道哪一样不能动。"),
    ("这种熟悉，新东西给不了。",
     "这种熟悉，新东西给不了。这大概就是六十年攒下来的东西。"),
]


def main() -> None:
    with io.open(P, encoding="utf-8") as fh:
        s = fh.read()
    for old, new in EDITS:
        if old not in s:
            if new in s or new[:20] in s:
                continue            # 已经补过，跳过
            raise SystemExit("anchor missing: " + old[:20])
        s = s.replace(old, new, 1)
    with io.open(P, "w", encoding="utf-8") as fh:
        fh.write(s)
    print("expanded, total chars =", len(s))


if __name__ == "__main__":
    main()
