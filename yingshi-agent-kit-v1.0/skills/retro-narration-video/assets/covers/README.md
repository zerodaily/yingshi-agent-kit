# 封面模板使用说明

4 套排版轮换使用，保证系列感但不单调。三层权威：封面**风格/落位/模板**规则见
`references/cover-and-layout.md`；人物 **IP 外貌与生图提示词**见
`references/cover-ip-prompt.md`；**出图技术参数**见 `references/image-pipeline.md`。
视觉基准见 `style-reference-modern-16x9.jpg` 与
`style-reference-modern-9x16.jpg`。

| 模板 | 文件 | 适用 |
|---|---|---|
| 经典款 | template1_classic.html | 常规品牌介绍，顶部标题 + 车与「言同学」互动 |
| 左图右文款 | template2_side_text.html | 竖排品牌名，适合名字短的品牌 |
| 沉浸款 | template3_immersive.html | 有故事感的单品/事件 |
| 对比款 | template4_compare.html | 老车 vs 新车、换代对比 |

用法：
1. 复制一份模板到项目目录（如 `<项目>/封面/cover_丰田.html`）。
2. 按 `references/cover-ip-prompt.md` 先出一张**车与「言同学」同框互动**的完整场景底图，
   再把 `.ph` 占位 div 换成实际出图 `<img src="cover_hero.png">`。不要分别生成车和人物再拼；
   车单独出图 + PIL 贴人的拆层路线已废弃。
3. 改品牌名/英文副标题/钩子文案。
4. 每个比例单独构图，浏览器打开截图或渲染为 PNG；B 站先上传 4:3 PNG，再同步 16:9。

铁律：封面使用米黄旧纸底 + 撕边毛边纸卡 + 黑白半调/木刻排线车图，人物是黑色钢笔线稿
言同学（外貌定稿唯一权威见 `cover-ip-prompt.md`）；顶部给超大品牌名留出米黄纸面；
车和人物必须同框互动；生图不带文字；印章「言同学」是白底朱红边框磨损款，放右下角
（模板 2 放左下角）。风格、落位、模板与禁止项细则以 `cover-and-layout.md` 为准。
