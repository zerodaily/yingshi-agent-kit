#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Y 盘项目 <-> WSL 出图工作目录的文件同步 + 引用校验。

解决 image-pipeline.md 里最高频的事故：
  - WSL 没有挂载 Y 盘，prompts.json / 出图产物全靠手拷，容易拷错、拷漏；
  - 多批次编号都从 01 开始，回填 index.html 前必须重编号；
  - 缺图会静默渲染成黑屏——本脚本在回填后逐张校验引用。

配置来自 yingshi_config（wsl_temp / zimage.workdir）。

用法（Windows 上跑）：
    python sync_assets.py push <项目目录> [--batch 01]
        # <项目>/prompts.json -> wsl_temp -> WSL ~/projects/Z-Image/prompts/<项目>/
    python sync_assets.py pull <项目目录> --project <项目名> [--batch batch_01]
        # WSL outputs/<项目>/<批次>/*.png -> wsl_temp -> <项目>/assets/illustrations/<key>_2048.png
        # （假定已在 Windows 侧用 Real-ESRGAN 放大为 *_2048.png；见 esrgan_batch 模式）
    python sync_assets.py verify <项目目录> [--html index.html]
        # 解析 index.html 里所有 img src，逐张检查磁盘上存在
"""
import glob
import os
import re
import shutil
import subprocess
import sys

try:
    from yingshi_config import load_config, cfg_get, expand
    _CFG = load_config()
except Exception:
    _CFG = {}


def _cf(key, default):
    return cfg_get(_CFG, key, default) if _CFG else default


def wsl_run(cmd):
    r = subprocess.run(["wsl", "-d", "Ubuntu", "-e", "bash", "-lc", cmd],
                       capture_output=True, text=True)
    return r


def to_wsl_mnt(win_path):
    p = win_path.replace("\\", "/")
    return "/mnt/" + p[0].lower() + p[2:]


def cmd_push(project):
    src = os.path.join(project, "prompts.json")
    if not os.path.exists(src):
        print(f"找不到 {src}", file=sys.stderr)
        sys.exit(1)
    proj_name = os.path.basename(os.path.normpath(project))
    tmp = expand(_cf("wsl_temp", r"C:\Users\jonny\AppData\Local\Temp"))
    os.makedirs(tmp, exist_ok=True)
    staged = os.path.join(tmp, f"prompts_{proj_name}.json")
    shutil.copy2(src, staged)
    wsl_work = _cf("zimage.workdir", "~/projects/Z-Image").rstrip("/")
    wsl_run(f"mkdir -p {wsl_work}/prompts/{proj_name}")
    r = wsl_run(f"cp {to_wsl_mnt(staged)} {wsl_work}/prompts/{proj_name}/prompts.json && ls -la {wsl_work}/prompts/{proj_name}/")
    print(r.stdout[-500:] or r.stderr[-500:])
    print(f"已推送 prompts.json -> WSL {wsl_work}/prompts/{proj_name}/")
    print(f"出图命令：wsl … python zimage_gen.py {wsl_work}/prompts/{proj_name}/prompts.json --project {proj_name}")


def cmd_pull(project, proj_name, batch):
    """把 WSL 侧出图拷回。期望 WSL 侧已按 outputs/<项目>/<批次>/ 隔离（zimage_gen.py --project）。"""
    tmp = expand(_cf("wsl_temp", r"C:\Users\jonny\AppData\Local\Temp"))
    os.makedirs(tmp, exist_ok=True)
    wsl_work = _cf("zimage.workdir", "~/projects/Z-Image").rstrip("/")
    wsl_out = f"{wsl_work}/outputs/{proj_name}/{batch}"
    r = wsl_run(f"ls {wsl_out}/*.png 2>/dev/null | head -40")
    files = [x.strip() for x in r.stdout.splitlines() if x.strip().endswith(".png")]
    if not files:
        print(f"WSL 侧没有出图：{wsl_out}", file=sys.stderr)
        sys.exit(1)
    dest_dir = os.path.join(tmp, f"zimg_{proj_name}_{batch}")
    os.makedirs(dest_dir, exist_ok=True)
    for f in files:
        wsl_run(f"cp {f} {to_wsl_mnt(dest_dir)}/")
    got = sorted(glob.glob(os.path.join(dest_dir, "*.png")))
    print(f"拷回 {len(got)} 张 -> {dest_dir}")
    # 重编号归位：zimg_NN_<key>_512.png -> <项目>/assets/illustrations/<key>_2048.png
    # （ESRGAN 放大后改名；若还没放大，先按 <key>_512.png 归位，放大脚本再改名）
    ill = os.path.join(project, "assets", "illustrations")
    os.makedirs(ill, exist_ok=True)
    for g in got:
        m = re.search(r"zimg_\d+_(.+?)_512\.png$", os.path.basename(g))
        key = m.group(1) if m else os.path.splitext(os.path.basename(g))[0]
        shutil.copy2(g, os.path.join(ill, f"{key}_512.png"))
    print(f"已按场景 key 归位到 {ill}（*_512.png，放大后改名为 *_2048.png）")


def cmd_verify(project, html_name="index.html"):
    html_path = os.path.join(project, html_name)
    if not os.path.exists(html_path):
        print(f"找不到 {html_path}", file=sys.stderr)
        sys.exit(1)
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    refs = sorted(set(re.findall(r'<img[^>]+src="([^"]+)"', html)))
    missing = [s for s in refs
               if s.startswith(("http", "data:"))
               or not os.path.exists(os.path.join(project, s))]
    # data: 与 http 视为外部资源，不判缺失
    missing = [s for s in missing if not s.startswith(("http", "data:"))]
    print(f"index.html 引用图片 {len(refs)} 张，缺失 {len(missing)} 张")
    for s in missing:
        print("  MISSING:", s)
    if missing:
        print("有缺失！渲染会出黑屏，先补图再 render。", file=sys.stderr)
        sys.exit(1)
    print("全部存在，可以渲染。")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    mode, project = sys.argv[1], sys.argv[2]
    if mode == "push":
        cmd_push(project)
    elif mode == "pull":
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--project", required=True)
        ap.add_argument("--batch", default="batch_01")
        a = ap.parse_args([x for x in sys.argv[3:] ])
        cmd_pull(project, a.project, a.batch)
    elif mode == "verify":
        html = "index.html"
        for i, x in enumerate(sys.argv):
            if x == "--html" and i + 1 < len(sys.argv):
                html = sys.argv[i + 1]
        cmd_verify(project, html)
    else:
        print("mode 必须是 push / pull / verify", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
