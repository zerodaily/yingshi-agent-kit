# 封面模板使用说明

4 套排版轮换使用，保证系列感但不单调。封面规则（配色、标题结构、IP 落位、模板选择、反模板套路）见
`references/cover-and-layout.md`；言同学 IP 外貌标准见 `references/image-pipeline.md`。

| 模板 | 文件 | 适用 |
|---|---|---|
| 经典款 | template1_classic.html | 常规品牌介绍，顶部巨字+车+IP |
| 左图右文款 | template2_side_text.html | 竖排品牌名，适合名字短的品牌 |
| 沉浸款 | template3_immersive.html | 有故事感的单品/事件 |
| 对比款 | template4_compare.html | 老车 vs 新车、换代对比 |

用法：
1. 复制一份模板到项目目录（如 `<项目>/封面/cover_丰田.html`）。
2. 把 `.ph` 占位 div 换成实际出图 `<img src="...">`：
   - 主车图：按 Z-Image 风格前缀出，车+言同学互动动作。
   - 言同学 IP 外貌、穿着、比例严格按 `image-pipeline.md` 标准，不在本模板里另写一份。
3. 改品牌名/英文副标题/钩子文案。
4. 浏览器打开截图，或用 hyperframes 渲染出 4:3 PNG（B 站封面先传 4:3）。

铁律：每次封面必须出现言同学 IP；禁止深绿底+米白字（配色反了）；印章「言同学」放右下角（模板 2 放左下角）。细则与禁止项以 `cover-and-layout.md` 为准。
