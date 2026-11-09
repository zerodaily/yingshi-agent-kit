# -*- coding: utf-8 -*-
"""风格 B 逐帧渲染：playwright 无头 Chrome 截图 → frames/fNNNN.png

用法（在项目目录里）：
    python render.py                     # 全片
    python render.py --fps 30            # 指定帧率
    python render.py --from 500 --to 550 # 只重渲高潮附近（局部返修，别整片重出）
    python render.py --chrome "D:\\Chrome\\chrome.exe"

片长与高潮秒数自动从 film.html 的 CONFIG 读，不用在这再写一遍。
"""
import argparse
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, "film.html")
FRAMES = os.path.join(BASE, "frames")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def read_total():
    """从 film.html 的 CONFIG 里读片长（秒）。"""
    try:
        src = open(HTML, encoding="utf-8").read()
        m = re.search(r"total\s*:\s*([0-9.]+)", src)
        return float(m.group(1)) if m else 20.0
    except Exception:
        return 20.0


def find_chrome(explicit=None):
    if explicit:
        if os.path.exists(explicit):
            return explicit
        sys.exit(f"指定的 Chrome 不存在：{explicit}")
    env = os.environ.get("YINGSHI_CHROME")
    if env and os.path.exists(env):
        return env
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    sys.exit("找不到 Chrome。用 --chrome 指定，或 set YINGSHI_CHROME=路径。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--from", dest="f0", type=int, default=0, help="起始帧（含）")
    ap.add_argument("--to", dest="f1", type=int, default=None, help="结束帧（含）")
    ap.add_argument("--chrome", default=None)
    args = ap.parse_args()

    if not os.path.exists(HTML):
        sys.exit(f"缺少 film.html：{HTML}")

    total = read_total()
    last = int(round(total * args.fps))
    f1 = last if args.f1 is None else min(args.f1, last)
    f0 = max(0, args.f0)
    os.makedirs(FRAMES, exist_ok=True)

    chrome = find_chrome(args.chrome)
    url = "file:///" + HTML.replace("\\", "/")

    from playwright.sync_api import sync_playwright
    log = open(os.path.join(BASE, "render.log"), "a", encoding="utf-8")

    def say(*a):
        m = " ".join(str(x) for x in a)
        print(m); log.write(m + "\n"); log.flush()

    t0 = time.time()
    say(f"[render] {f0}..{f1} @{args.fps}fps  chrome={chrome}")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.goto(url)
        pg.wait_for_timeout(400)
        for n in range(f0, f1 + 1):
            pg.evaluate(f"setState({(n/args.fps):.4f})")
            pg.screenshot(path=os.path.join(FRAMES, f"f{n:04d}.png"))
            if (n - f0) % 50 == 0:
                say(f"  frame {n} elapsed {time.time()-t0:.1f}s")
        br.close()
    say(f"[render] DONE {f1-f0+1} frames in {time.time()-t0:.1f}s")
    log.close()


if __name__ == "__main__":
    main()
