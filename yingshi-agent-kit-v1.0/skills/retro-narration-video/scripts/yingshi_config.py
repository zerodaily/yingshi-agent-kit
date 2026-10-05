#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""硬视产线统一配置读取。

查找顺序：
  1. 环境变量 YINGSHI_CONFIG 指向的 JSON 文件
  2. skill 根目录下的 config.json
  3. config.template.json 的默认值（只读回退，不要求用户先建文件）

用法：
    from yingshi_config import load_config, cfg_get
    cfg = load_config()
    model_dir = cfg_get(cfg, "zimage.model_dir")
"""
import json
import os

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE = os.path.join(_SKILL_ROOT, "config.template.json")
_CONFIG = os.path.join(_SKILL_ROOT, "config.json")


def _deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path=None):
    """返回合并后的配置 dict（含模板默认值）。"""
    with open(_TEMPLATE, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg_path = path or os.environ.get("YINGSHI_CONFIG") or _CONFIG
    if cfg_path and os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            cfg = _deep_merge(cfg, json.load(f))
    return cfg


def cfg_get(cfg, dotted, default=None):
    cur = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def expand(p):
    """展开 ~ 与环境变量；保持 Windows 盘符写法。"""
    if not p:
        return p
    return os.path.expandvars(os.path.expanduser(p))


def skill_root():
    return _SKILL_ROOT
