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

os.environ.setdefault("HF_HOME", "/mnt/e/ai-models")
os.environ.setdefault("TRANSFORMERS_CACHE", "/mnt/e/ai-models/transformers_cache")

MODEL = "/mnt/e/ai-models/ltxdesktop/Z-Image-Turbo"
STYLE = (
    "复古中国风插图，老报纸与宣纸质感，米黄色旧纸底，墨色线条，朱红点缀，"
    "拙朴木刻版画与淡彩水墨结合，画面留白，无任何文字。内容："
)


def main() -> None:
    spec_path = sys.argv[1] if len(sys.argv) > 1 else "prompts.json"
    with open(spec_path, encoding="utf-8") as f:
        specs = json.load(f)
    print("loading model...", flush=True)
    from diffusers import ZImagePipeline

    pipe = ZImagePipeline.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True
    )
    pipe.to("cuda")
    print("loaded, start batch", flush=True)
    os.makedirs("outputs", exist_ok=True)
    seed = 20260910
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
        out = f"outputs/zimg_{i:02d}_{spec['key']}_512.png"
        img.save(out)
        print(f"[{i}/{len(specs)}] {spec['key']} saved {time.time() - t0:.1f}s", flush=True)
    print("BATCH DONE", flush=True)


if __name__ == "__main__":
    main()
