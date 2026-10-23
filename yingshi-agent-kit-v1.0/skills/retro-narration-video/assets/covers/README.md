# 封面模板使用说明

4 套排版轮换使用，保证系列感但不单调。封面规则见
`references/cover-and-layout.md`；封面人物 IP 标准见 `references/image-pipeline.md`；
完整同框生图提示词见 `references/cover-ip-prompt.md`。
视觉基准见 `style-reference-modern-16x9.jpg` 与
`style-reference-modern-9x16.jpg`。

| 模板 | 文件 | 适用 |
|---|---|---|
| 经典款 | template1_classic.html | 常规品牌介绍，顶部标题 + 车与「他」互动 |
| 左图右文款 | template2_side_text.html | 竖排品牌名，适合名字短的品牌 |
| 沉浸款 | template3_immersive.html | 有故事感的单品/事件 |
| 对比款 | template4_compare.html | 老车 vs 新车、换代对比 |

用法：
1. 复制一份模板到项目目录（如 `<项目>/封面/cover_丰田.html`）。
2. 按 `references/cover-ip-prompt.md` 先出一张**车与「他」同框互动**的完整场景底图，
   再把 `.ph` 占位 div 换成实际出图 `<img src="cover_hero.png">`。不要分别生成车和人物再拼。
3. 改品牌名/英文副标题/钩子文案。
4. 每个比例单独构图，浏览器打开截图或渲染为 PNG；B 站先上传 4:3 PNG，再同步 16:9。

铁律：封面使用米黄纸底 + 深墨绿充墨插画，固定人物 IP 是米色皮肤的小黑线描人物「他」；
顶部给超大中文品牌名留出米黄纸面；车和人物必须同框互动；生图不带文字；
印章「言同学」放右下角（模板 2 放左下角）。细则与禁止项以
`cover-and-layout.md` 为准。
