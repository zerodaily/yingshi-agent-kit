"""Batch Z-Image-Turbo text-to-image (512x512, 4 steps) for retro illustrations.

Run inside WSL with the wan2gp conda env (Python 3.11), from a Z-Image project
that can load /mnt/e/ai-models/ltxdesktop/Z-Image-Turbo via diffusers:

  ~/miniconda3/envs/wan2gp/bin/python <skill>/scripts/zimage_gen.py prompts.json

prompts.json shape:
  [
    {"key": "help_street", "prompt": "复古中国风插图，... 内容：..."},
    ...
  ]
Output: outputs/zimg_<NN>_<key>_512.png  (same dir as the model repo outputs/)
"""
import json, os, sys, time, torch

try:
    from yingshi_config import load_config, cfg_get, expand
    _CFG = load_config()
except Exception:
    _CFG = {}

os.environ.setdefault("HF_HOME", expand(cfg_get(_CFG, "zimage.hf_home", "/mnt/e/ai-models")))
os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(
    expand(cfg_get(_CFG, "zimage.hf_home", "/mnt/e/ai-models")), "transformers_cache"))

MODEL = expand(cfg_get(_CFG, "zimage.model_dir", "/mnt/e/ai-models/ltxdesktop/Z-Image-Turbo"))
OUT_ROOT = "outputs"  # 可被 --out-root 覆盖；建议按项目隔离见下方
STYLE = (
    "复古中国风插图，老报纸与宣纸质感，米黄色旧纸底，墨色线条，朱红点缀，"
    "拙朴木刻版画与淡彩水墨结合，画面留白，无任何文字。内容："
)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?", default="prompts.json", help="prompts.json 路径")
    ap.add_argument("--project", default="", help="项目名：输出隔离到 outputs/<项目>/<批次>/")
    ap.add_argument("--batch", default="", help="批次名（默认按时间生成 batch_01…）")
    ap.add_argument("--out-root", default=OUT_ROOT, help="输出根目录")
    ap.add_argument("--seed", type=int, default=20260910)
    args = ap.parse_args()

    spec_path = args.spec
    with open(spec_path, encoding="utf-8") as f:
        specs = json.load(f)
    print("loading model...", flush=True)
    from diffusers import ZImagePipeline

    pipe = ZImagePipeline.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True
    )
    pipe.to("cuda")
    print("loaded, start batch", flush=True)
    out_dir = args.out_root
    if args.project:
        batch = args.batch or "batch_01"
        # 同项目已有批次时自动递增，避免同名覆盖
        n = 1
        while os.path.exists(os.path.join(args.out_root, args.project, "batch_%02d" % n)):
            n += 1
        batch = args.batch or ("batch_%02d" % n)
        out_dir = os.path.join(args.out_root, args.project, batch)
    os.makedirs(out_dir, exist_ok=True)
    seed = args.seed
    for i, spec in enumerate(specs, 1):
        prompt = (spec.get("style") or "") + spec["prompt"]
        if not spec.get("custom_style"):
            prompt = STYLE + spec["prompt"]
        gen = torch.Generator("cuda").manual_seed(seed + i)
        t0 = time.time()
        img = pipe(
            prompt=prompt,
            height=512,
            width=512,
            num_inference_steps=4,
            guidance_scale=0.0,
            generator=gen,
        ).images[0]
        out = os.path.join(out_dir, "zimg_%02d_%s_512.png" % (i, spec['key']))
        img.save(out)
        print(f"[{i}/{len(specs)}] {spec['key']} saved {time.time() - t0:.1f}s -> {out}", flush=True)
    print("BATCH DONE ->", out_dir, flush=True)


if __name__ == "__main__":
    main()
