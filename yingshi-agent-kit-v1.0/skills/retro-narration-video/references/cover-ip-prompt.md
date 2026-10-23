# 封面人物 IP 提示词（小黑线描「他」·露肤版）

> 这是硬视封面中固定人物 IP 的唯一生图提示词。人物视觉源来自
> `ian-xiaohei-illustrations` 的小黑风格，IP 使用其 fork
> `jonny-illustrations` 的「他」。封面整体则采用已验证的现代项目风格：
> 米黄纸底、深墨绿充墨插画、顶部超大中文品牌名、小号英文副标题和朱红印章。
> 不再使用大头卡通、写实肖像、小胡子人物或整张纯白线稿封面。

视觉校准文件：

- `assets/covers/style-reference-modern-16x9.jpg`
- `assets/covers/style-reference-modern-9x16.jpg`

## 使用边界

- 封面先生成一张完整场景底图，人物和车必须同框互动，不要先生成车、再单独贴一个人物。
- 生图只负责画面，不负责标题、品牌名、年份、标签和印章；这些文字全部由 HTML/CSS 叠加。
- 一个尺寸一张原生构图。不得先生成 4:3 再机械裁切成六个尺寸。
- 只要画面出现真实五官、写实照片感、可爱大头、Q 版吉祥物，直接重生成。
- 封面必须是“彩底充墨插画”，不是纯白正文配图；字体区保留大块米黄纸面。

## 固定 IP：他

- 瘦高、中等身高的极简手绘人类卡通，比例自然，不是黑色剪影。
- 脸、耳朵和手使用浅米色皮肤；五官只用最少线条表达。
- 鹅蛋脸，短黑发用整块实心形状表现，不画发丝。
- 细黑框眼镜，镜片内两个小而清楚的深色点状眼睛。
- 下半脸保留肤色，嘴只用一条冷静的平线；不画胡须。
- 黑色短袖 T 恤，左胸一个极小图标作为识别点。
- 一条细窄斜挎带，从右肩连到左胯。
- 深色长裤和黑色帆布鞋；手仍保持简化，不画真实五指细节。
- 默认不拿口罩；只有叙事需要时，可出现一只淡蓝色一次性口罩，频率不超过三成。
- 表情始终冷静、认真、略带笨拙，不卖萌。
- 严禁整个人涂成黑色、做成阴影人、无脸人或纯剪影。

## 可复制提示词

```text
Generate one standalone Chinese knowledge-video cover illustration that combines
the fixed Ian Xiaohei character language with the approved dense retro-green
cover style.

Canvas:
{宽高比与像素尺寸}

Visual DNA:
Warm cream paper background, deep pine-green filled ink illustration and
near-black hand-drawn outlines. Dense editorial screenprint with subtle paper
grain and strong dark-green silhouette masses. Leave a large clean cream band at
the top for future large Chinese typography. One restrained vermilion accent.
No pure-white background, no glossy 3D render, no commercial vector style, no PPT
infographic look, no cute mascot poster, no children's illustration, no realistic
portrait.

Recurring character required:
"他", a lean medium-height minimalist hand-drawn human cartoon, NOT a solid-black
silhouette. Warm light-beige skin on the face, ears, arms and hands. Oval head.
Short solid-black hair without individual strands. Thin dark rectangular glasses
with two small dark dot eyes. Clear jawline and light lower face with one calm
flat mouth line. No beard, no exaggerated expression. Solid-black short-sleeve
T-shirt with one tiny simple icon at the left chest. A thin diagonal crossbody
strap from the right shoulder to the left hip. Dark slim trousers and simple
black canvas shoes. Simplified hands, but the skin colour must remain visible.
Deadpan, serious and slightly awkward; never cute and never resembling a real
person's face. He must remain a readable cartoon man, not an all-black figure.

Scene and action:
{人物必须与车或核心物件发生物理互动：靠车门、指发动机、蹲在车轮边量尺寸、
拉安全带、掀开图纸、站在碰撞测试装置旁等。写明人物位置、动作、车辆位置和景别。}

Composition:
{主视觉主体与占画比例；人物约占画面 1/4–1/3；保留标题和数字的干净负空间。}

Color accents:
Black for the character, car outline and structure. Red only for one key warning
or result. Orange only for one movement/path accent. Blue only for one secondary
note. Keep at least 35% of the canvas visually quiet.

Text:
No text, no letters, no numbers, no logos and no fake typography anywhere in the
generated image. Leave clean negative space for HTML/CSS typography.

Constraints:
One cover tells one clear story. The character must perform an essential action,
not stand beside the car as decoration. Keep the vehicle recognizable. Do not
copy an existing cover composition. No realistic face, no mascot proportions, no
commercial polish, no dense diagram, no decorative frame, no all-white line-art
cover, no all-black character, no faceless shadow figure, no flat infographic.
```

## 沃尔沃封面动作示例

把 Scene and action 替换为：

```text
The fixed-character IP crouches beside the front wheel of a vintage Volvo,
pulling one hand along the three-point seatbelt and pointing with the other at
the buckle. His warm beige face and hands must remain clearly visible against
the deep green scene. The car and industrial background fill the lower two-thirds
with deep pine-green ink masses and black outlines. Keep the top third as a
quiet warm-cream band for the HTML headline and year.
```

不要生成写实人脸，也不要生成全黑人形。人物必须是米色皮肤的小黑线描人类卡通「他」，
并且动作直接说明安全带或安全结构。
