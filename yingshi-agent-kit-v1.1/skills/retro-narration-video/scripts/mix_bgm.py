#!/usr/bin/env python3
"""mix_bgm.py - BGM 严格让位口播的混音。

为什么不能只调 volume：实测旁白 -27.2 LUFS、BGM -15.9 LUFS，音乐比人声响 11 LU，
浏览器里给个 volume=0.16 根本压不住。这里做四件事：

1. 按响度算增益：BGM 压到旁白之下 keep-below LU（默认 13），不再拍脑袋给数字；
2. 人声频段让位：180Hz 高通去掉低频轰鸣，2.5kHz 衰减 3dB 让出清晰度带；
3. 侧链闪避：旁白一出声，BGM 再自动下沉（默认约 4dB，可调）；
4. 限幅：真峰值不超过 -1.5 dBTP。

输出单轨 <项目>/口播混音.wav，画面合成里只挂这一条音轨，不再靠播放器音量。

用法：
  python mix_bgm.py <项目目录> [--keep-below 13] [--duck-ratio 4] [--bgm assets/bgm.wav]

经验值：18 LU 太狠，成片里几乎听不见音乐；13 LU + 4:1 闪避是「听得见但不抢口播」的档。
每集可按素材密度微调 11-15。
"""
import argparse
import os
import re
import subprocess
import sys


def lufs(path, stream=None):
    """返回 (integrated LUFS, true peak dBTP)。"""
    cmd = ["ffmpeg", "-hide_banner", "-i", path]
    if stream:
        cmd = ["ffmpeg", "-hide_banner", "-i", path]
    cmd += ["-filter_complex", "ebur128=peak=true", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True, errors="ignore").stderr
    i = re.findall(r"I:\s+(-?\d+\.\d+)\s+LUFS", out)
    p = re.findall(r"Peak:\s+(-?\d+\.\d+)\s+dBFS", out)
    return (float(i[-1]) if i else 0.0, float(p[-1]) if p else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--keep-below", type=float, default=13.0,
                    help="BGM 要比旁白低多少 LU（默认 13；18 实测听不见）")
    ap.add_argument("--duck-ratio", type=float, default=4.0,
                    help="侧链闪避压缩比（默认 4；越大说话时压得越狠）")
    ap.add_argument("--duck-threshold", type=float, default=0.05,
                    help="闪避触发阈值，线性值（默认 0.05 约 -26dB）")
    ap.add_argument("--bgm", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    proj = args.project
    narr = os.path.join(proj, "口播拼接.wav")
    bgm = args.bgm or os.path.join(proj, "assets", "bgm.wav")
    out = args.out or os.path.join(proj, "口播混音.wav")
    for p in (narr, bgm):
        if not os.path.exists(p):
            print("missing: " + p, file=sys.stderr)
            return 2

    l_n, pk_n = lufs(narr)
    l_b, pk_b = lufs(bgm)
    gain = (l_n - args.keep_below) - l_b          # 目标：BGM = 旁白 - keep_below
    print("narration %.1f LUFS (peak %.1f) | bgm %.1f LUFS (peak %.1f)"
          % (l_n, pk_n, l_b, pk_b))
    print("bgm gain %.1f dB -> %.1f LUFS (旁白之下 %.1f LU)"
          % (gain, l_b + gain, args.keep_below))

    chain = (
        f"[1:a]highpass=f=180,equalizer=f=2500:t=q:w=1.2:g=-3,"
        f"volume={gain:.2f}dB[bed];"
        f"[bed][0:a]sidechaincompress=threshold={args.duck_threshold}:"
        f"ratio={args.duck_ratio}:attack=20:release=500:makeup=1[duck];"
        f"[0:a][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix];"
        f"[mix]alimiter=limit=0.84:level=disabled[out]"
    )
    # 输出保持单声道：mono→stereo 的等功率上混会把口播整体压低 3 dB，
    # 导致成片比其它集数明显偏轻。BGM 本来就是铺底，降成单声道在手机外放更清楚。
    cmd = ["ffmpeg", "-y", "-hide_banner", "-i", narr, "-i", bgm,
           "-filter_complex", chain, "-map", "[out]",
           "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", out]
    subprocess.run(cmd, check=True)

    l_m, pk_m = lufs(out)
    print("mix %.1f LUFS (peak %.1f) -> %s" % (l_m, pk_m, out))
    print("相对旁白变化 %.2f LU（越接近 0 说明 BGM 越不抢戏）" % (l_m - l_n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
