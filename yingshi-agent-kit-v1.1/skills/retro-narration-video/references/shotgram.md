# shotgram.py - 镜头语言与分镜细化

只换元素落点不算"换镜头"。`shotgram.py` 按电影语法给每一场分派完整镜头规格，
再由 `build_film.py` 落成几何、运动与转场。

## 六个维度

| 维度 | 取值 | 作用 |
|---|---|---|
| 景别 `scale` | ELS 大远景 / LS 远景 / MS 中景 / CU 近景 / ECU 特写 / INSERT 插入 | 主体占画框多大；远景交代环境，特写压细节，插入镜头点证据 |
| 机位 `angle` | eye 平视 / topdown 俯拍平铺 / low 仰拍 | 俯拍像摊在桌上看，仰拍显得主角压过来 |
| 运动 `move` | static 固定 / push 推 / pull 拉 / drift 缓移 / pan 横摇 | 整层做位移或缩放，就是镜头在动 |
| 构图 `comp` | center / left / right / negative 大留白 / diag 对角 | 主体落在哪，留白给谁 |
| 转场 `trans` | cut 硬切 / dissolve 叠化 / match 匹配剪辑 | 场景之间怎么换 |
| 时长 | 由文本密度算 2.4–7.5 秒 | 短镜头=紧，长镜头=缓 |

## 分配规则（可解释，不是随机）

```
景别：按 MS→LS→CU→MS→ECU→LS→INSERT→CU 轮换；
      章首强制 ELS/LS；转折句偶尔给 CU；数字短句偶尔给 INSERT；收束句给 LS
机位：远景里每 8 场一次俯拍平铺；每 9 场一次仰拍；其余平视
运动：push→drift→static→pull→pan 轮换；收束改拉或静；转折改推；
      景别不允许的运动自动退回该景别允许的集合（如特写不做横摇）
构图：center→left→right→negative→center→diag→right→left 轮换；
      远景偏留白、近景居中或对角
转场：硬切为主；景别落差大且每 4 场一次叠化；每 6 场一次匹配剪辑
时长：短句 0.75 倍、长句 1.3 倍，章首 +0.6s、章尾 +0.4s，钳在 2.4–7.5s
```

**关键是"轮换为主、内容覆盖为辅"**：第一版让"转折/数字"这类词主导，结果 91% 平视、
48% 推镜、0 叠化——又变回一种镜头。内容词现在只在少数位置改写轮换结果。

## 落地方式

- `plan_scenes.py` 逐场调用 `shotgram.assign()`，把 `_shot` 写进 `film.json`
- `build_film.py` 读到 `_shot` 后：用 `hero_geom()` / `support_geom()` 算位置，
  给每场套一个 `.shot` 容器并在其上做推/拉/缓移/横摇，按 `trans` 决定出场方式
- 镜头时长反过来影响分镜切分：`plan_scenes` 用 `planned_shot_len()` 决定一场装几句，
  所以**镜头长短是变化的，但场景边界始终贴住旁白时间轴**

## 性能注意

整层做 scale/位移比只动元素贵得多：加了镜头运动后渲染从 ~13fps 掉到 ~10fps
（12 分钟片约 22 分钟 → 35 分钟）。`.shot` 容器已加 `will-change: transform` 缓解。
要更快就减少带运动的镜头比例（`move_cycle` 里多放 `static`）。

## 渲染前先做样片

长片不要直接渲全片：先切前 90 秒做样片（4 分钟），确认景别与节奏再跑全片。
注意 `hyperframes render` 读的是**目录下的 `index.html`**——样片要放进独立子目录
（如 `proof/index.html`），只改文件名不会被渲染到（我在这上面白跑过两次）。
