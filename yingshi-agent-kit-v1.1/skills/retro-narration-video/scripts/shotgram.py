#!/usr/bin/env python3
"""shotgram.py - 镜头语言分配器（分镜细化）。

依据电影语法（field size / camera angle / movement / composition / pacing / transition），
给每一场分派一个完整镜头规格，再交给 build_film.py 落成几何与缓动。

维度与取值：
  景别 scale : ELS 大远景 / LS 远景 / MS 中景 / CU 近景 / ECU 特写 / INSERT 插入镜头
  机位 angle : eye 平视 / topdown 俯拍平铺 / low 仰拍
  运动 move  : static 固定 / push 推 / pull 拉 / drift 缓移 / pan 横摇
  构图 comp  : center 中心 / left 左三分 / right 右三分 / diag 对角 / negative 大留白
  转场 trans : cut 硬切 / dissolve 叠化 / match 匹配剪辑

规则来源（简述）：
- 景别按"画框里能看到多少主体"分档，远景交代环境、特写强调细节、插入镜头用来点证据；
- 镜头时长决定节奏：短镜头=紧张，长镜头=舒缓（ASL 概念），长片要有节奏曲线而不是等长切；
- 蒙太奇靠对比与积累产生意义：把不相似的镜头并置，或用同类镜头堆出一致性；
- 转场最省事的是硬切，叠化用于时间跳跃，匹配剪辑用于把两个场景"缝"在一起。
"""
from __future__ import annotations

# 画框里主体占多宽（画布宽度比例）与纵向落点
SCALE_GEOM = {
    "land": {
        "ELS":    {"w": 0.34, "y": 0.30},
        "LS":     {"w": 0.50, "y": 0.30},
        "MS":     {"w": 0.62, "y": 0.28},
        "CU":     {"w": 1.00, "y": 0.14},
        "ECU":    {"w": 1.55, "y": 0.02},
        "INSERT": {"w": 0.30, "y": 0.34},
    },
    "port": {
        "ELS":    {"w": 0.62, "y": 0.34},
        "LS":     {"w": 0.80, "y": 0.32},
        "MS":     {"w": 0.92, "y": 0.30},
        "CU":     {"w": 1.24, "y": 0.22},
        "ECU":    {"w": 1.80, "y": 0.12},
        "INSERT": {"w": 0.52, "y": 0.34},
    },
}

# 构图 → 横向落点（返回左边界比例）
def comp_x(comp: str, w: float) -> float:
    if comp == "left":
        return 0.03
    if comp == "right":
        return max(0.02, 1.0 - w - 0.03)
    if comp == "diag":
        return 0.05
    if comp == "negative":
        return max(0.02, min(0.62, 1.0 - w - 0.02))
    return max(0.02, (1.0 - w) / 2)          # center


def hero_geom(shot: dict, orient: str) -> dict:
    """按镜头规格算出主图的位置、宽度与旋转。"""
    g = dict(SCALE_GEOM[orient][shot["scale"]])
    if shot["angle"] == "topdown":
        g["y"] = max(0.05, g["y"] - 0.06)
    elif shot["angle"] == "low":
        g["y"] = min(0.62, g["y"] + 0.10)
        g["w"] = min(1.9, g["w"] * 1.08)
    x = comp_x(shot["comp"], g["w"])
    if shot["comp"] == "negative" and shot.get("side", "right") == "left":
        x = 0.03
    rot = 6.5 if shot["comp"] == "diag" else 0.0
    return {"x": x, "y": g["y"], "w": g["w"], "rot": rot}


def support_geom(shot: dict, role: str, orient: str, hero: dict) -> dict:
    """陪体：碎片压在角上、小图补信息、人物用竖幅。位置随构图镜像。"""
    W = SCALE_GEOM[orient]
    if role == "scrap":
        if shot["comp"] in ("left", "negative"):
            return {"x": 0.62, "y": 0.58, "w": 0.30, "rot": 3.0}
        return {"x": 0.02, "y": 0.48, "w": 0.28, "rot": -3.5}
    if role == "mini":
        if shot["scale"] in ("CU", "ECU"):
            return {"x": 0.66, "y": 0.06, "w": 0.24, "rot": 1.2}
        return {"x": 0.04, "y": 0.06, "w": 0.22, "rot": -1.2}
    if role == "portrait":
        return {"x": 0.72 if shot["comp"] != "right" else 0.04, "y": 0.08,
                "w": 0.20, "rot": -1.5}
    if role == "hero_b":
        return {"x": 0.60, "y": 0.56, "w": 0.34, "rot": 0.0}
    if role == "scrap2":
        return {"x": 0.70, "y": -0.08, "w": 0.26, "rot": 2.5}
    return hero


# 不同景别的镜头运动与转场：远景给缓移，特写给推进，插入镜头固定
MOVE_BY_SCALE = {
    "ELS": ["drift", "pull", "pan"],
    "LS": ["drift", "push", "pull", "pan"],
    "MS": ["push", "drift", "static", "pull"],
    "CU": ["push", "static", "pull"],
    "ECU": ["push", "drift", "pull"],
    "INSERT": ["static", "push", "pull"],
}


def assign(text: str, i: int, prev: dict | None, chapter_start: bool,
           chapter_end: bool, dense: bool) -> dict:
    """按文本与位置分派镜头。规则是可解释的，不是随机数。"""
    has_number = any(ch.isdigit() for ch in text) or ("年" in text and "第" in text)
    is_turn = any(k in text for k in ("但", "却", "可是", "反而", "差点", "危机", "争议"))
    is_summary = any(k in text for k in ("所以", "最后", "这就是", "六十", "总结"))
    short_text = len(text) < 18

    # 以轮换为主、内容覆盖为辅：内容词只在少数位置改写轮换结果，
    # 否则"转折/数字"这类词会吃掉整片，又变回一种镜头。
    scale_cycle = ["MS", "LS", "CU", "MS", "ECU", "LS", "INSERT", "CU"]
    scale = scale_cycle[i % len(scale_cycle)]
    if chapter_start:
        scale = "ELS" if i % 2 == 0 else "LS"           # 章首交代环境
    elif is_turn and i % 3 == 0:
        scale = "CU"                                     # 转折偶尔给近景
    elif (has_number and short_text) and i % 4 == 1:
        scale = "INSERT"                                 # 数字/证据偶尔给插入镜头
    elif is_summary and i % 5 == 0:
        scale = "LS"                                     # 收束拉远

    if (scale in ("ELS", "LS")) and i % 8 == 5:
        angle = "topdown"                                # 俯拍平铺：章首或远景
    elif i % 9 == 4 or (is_turn and i % 7 == 3):
        angle = "low"                                    # 仰拍：每九场一次，转折处加一次
    else:
        angle = "eye"

    # 镜头运动：四种按序轮换，保证"推/拉/缓移/静止"都出现
    move_cycle = ["push", "drift", "static", "pull", "pan", "push", "drift", "static"]
    move = move_cycle[i % len(move_cycle)]
    if is_summary or chapter_end:
        move = "pull" if i % 2 == 0 else "static"        # 收束：拉或静
    elif is_turn and i % 4 == 2:
        move = "push"                                    # 转折：推进
    if move not in MOVE_BY_SCALE[scale]:                 # 景别不合就退回该景别允许的运动
        move = MOVE_BY_SCALE[scale][i % len(MOVE_BY_SCALE[scale])]

    comp_cycle = ["center", "left", "right", "negative", "center", "diag", "right", "left"]
    comp = comp_cycle[i % len(comp_cycle)]
    if scale in ("ELS", "LS"):                           # 远景偏留白
        comp = ["left", "negative", "right"][i % 3]
    elif scale in ("CU", "ECU"):                         # 近景居中或对角
        comp = ["center", "diag"][i % 2]

    # 转场：硬切为主，景别落差大时叠化，每 6 场一次匹配剪辑把两场缝起来
    if i % 6 == 2:
        trans = "match"
    elif prev and prev["scale"] != scale and i % 4 == 1:
        trans = "dissolve"
    else:
        trans = "cut"

    return {"scale": scale, "angle": angle, "move": move, "comp": comp,
            "trans": trans, "side": "left" if comp in ("left", "negative") else "right"}


def planned_shot_len(text: str, base: float, chapter_start: bool,
                     chapter_end: bool) -> float:
    """镜头时长：短句快切，长句给够时间；章首章尾各加一点呼吸。"""
    n = len(text)
    if n < 14:
        d = base * 0.75
    elif n < 26:
        d = base
    else:
        d = base * 1.3
    if chapter_start:
        d += 0.6
    if chapter_end:
        d += 0.4
    return round(max(2.4, min(7.5, d)), 2)
