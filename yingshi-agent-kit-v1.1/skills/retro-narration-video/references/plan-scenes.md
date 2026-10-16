# plan_scenes.py - 长片分镜自动排布

12 分钟片子约 180 个画面，手工排版不现实。`plan_scenes.py` 用转写自动出分镜：

```bash
python scripts/plan_scenes.py \
  --transcript <项目>/audio/transcript.json \
  --elements  <项目>/assets/elements \
  --chapters  <项目>/audio/chapters.json \
  --slots     references/example-film.json \
  --out       <项目>/film.json --scene 4.0
```

`--slots` 传一份已有分镜（如 `example-film.json`），用来抄槽位坐标、画布与字体规格。

## 它做的五件事

1. **切场景**：按 `--scene`（默认 4 秒）累积转写句子，长片 12 分钟约 180 场。
2. **画面跟着旁白走**：场景文本里出现"九三零""勒芒"这类词时，优先挑同名元素当主图
   （映射表见脚本里的 `TOKEN_HINTS`，新领域往里加词即可）。
3. **角色轮换**：实物当主图、地图/碎片当衬底、人物每 `--portrait-every` 场出现一次，
   另一部分场景补一张小图。
4. **标签粗提**：从文本抓年份（`一九六三`）与型号（`911`、`GT3`）做 `label1`，
   取第一短句前 14 字做 `label2`。**这是粗提，出片前必须人工过一遍标签**。
5. **章节卡**：每章开头插一张 `--chapter-card` 秒（默认 3 秒）的章节卡，时间轴整体后移。

## 产出后的必做检查

```bash
python scripts/build_film.py <项目>/film.json --orientation land --out <项目>/index.html
```

构建时会打印质检摘要：变体分布、相邻同构图数（必须 0）、元素库用量排行。
接着照常 `hyperframes check`。

## 人工要补的三件事

- **标签**：自动提的年份/型号只是占位，语义准确要人改；
- **元素与画面是否对得上**：自动挑图只看关键词，可能把 964 的图放到讲 993 的句子上；
- **章节卡标题**：直接用 `chapters.json` 的标题，必要时改口语些。
