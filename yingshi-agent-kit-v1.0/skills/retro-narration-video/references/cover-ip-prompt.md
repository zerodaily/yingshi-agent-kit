# 封面人物 IP 提示词（小黑风「他」）

> 这是硬视封面中固定人物 IP 的唯一生图提示词。视觉源来自
> `ian-xiaohei-illustrations` 的小黑风格，IP 使用其 fork
> `jonny-illustrations` 的「他」。不再使用大头卡通、写实肖像、小胡子人物或圆眼镜人物。

## 使用边界

- 封面先生成一张完整场景底图，人物和车必须同框互动，不要先生成车、再单独贴一个人物。
- 生图只负责画面，不负责标题、品牌名、年份、标签和印章；这些文字全部由 HTML/CSS 叠加。
- 一个尺寸一张原生构图。不得先生成 4:3 再机械裁切成六个尺寸。
- 只要画面出现真实五官、写实照片感、可爱大头、Q 版吉祥物，直接重生成。

## 固定 IP：他

- 偏瘦、中等身高，整体竖长的黑色实心几何人形剪影。
- 鹅蛋脸，短黑发用整块实心形状表现，不画发丝。
- 细黑框眼镜，镜片为白色实底，镜片内两个小白点作为眼睛。
- 下半脸留白，嘴只用一条冷静的平线；不画鼻子、耳朵和胡须。
- 黑色实心短袖 T 恤，左胸一个极小图标作为识别点。
- 一条细窄斜挎带，从右肩连到左胯。
- 手是黑色实心小块，不画五指；裤子和鞋也是黑色实心块面。
- 默认不拿口罩；只有叙事需要时，可出现一只淡蓝色一次性口罩，频率不超过三成。
- 表情始终冷静、认真、略带笨拙，不卖萌。

## 可复制提示词

```text
Generate one standalone Chinese knowledge-video cover illustration in the same
minimal black hand-drawn visual language as Ian Xiaohei illustrations.

Canvas:
{宽高比与像素尺寸}

Visual DNA:
Pure white background. Minimalist black hand-drawn line art with slightly wobbly
pen strokes. Lots of clean white space. A few restrained red, orange and blue
handwritten accents are allowed, but no paper texture, no warm beige background,
no gradients, no shadows, no commercial vector style, no PPT infographic look,
no cute mascot poster, no children's illustration, no realistic portrait.

Recurring character required:
"他", a lean medium-height black solid silhouette humanoid in geometric
hand-drawn style. Oval face. Short solid-black hair without individual strands.
Thin dark rectangular glasses with white-filled lenses, each containing one small
white dot eye. Lower face left white with one calm flat mouth line. No nose, no
ears, no facial hair. Solid-black short-sleeve T-shirt with one tiny simple icon
at the left chest. A thin diagonal crossbody strap from the right shoulder to the
left hip. Hands are small solid-black blocks without five distinct fingers.
Solid-black trousers and block-like shoes. Deadpan, serious and slightly awkward;
never cute and never resembling a real person's face. The character must be a
stylized geometric silhouette, not a portrait.

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
commercial polish, no dense diagram, no decorative frame, no paper grain.
```

## 沃尔沃封面动作示例

把 Scene and action 替换为：

```text
The fixed-character IP crouches beside the front wheel of a vintage Volvo,
pulling one hand along the three-point seatbelt and pointing with the other at
the buckle. The car fills the middle-right of the frame in a bold three-quarter
view. Keep the left and top areas open for the HTML headline and year.
```

不要生成「一个写实男人站在车边」的画面。人物必须是黑色几何剪影「他」，并且动作直接说明
安全带或安全结构。
