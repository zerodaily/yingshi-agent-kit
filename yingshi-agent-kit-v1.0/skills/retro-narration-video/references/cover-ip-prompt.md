# 封面人物 IP 提示词（言同学 · 照片原型定稿 · 扁平卡通版）

> 这是硬视封面中固定人物 IP 的唯一生图提示词。人物识别点以照片原型定稿为准
> （`Y:\Projects\自媒体\言同学IP形象描述_照片原型.md`），封面整体仍采用已验证的
> 现代项目风格：米黄纸底、深墨绿充墨插画、顶部超大中文品牌名、小号英文副标题和
> 朱红印章。不再使用大头卡通、写实肖像或整张纯白线稿封面。

视觉校准文件：

- `assets/covers/style-reference-modern-16x9.jpg`
- `assets/covers/style-reference-modern-9x16.jpg`

## 使用边界

- 封面先生成一张完整场景底图，人物和车必须同框互动，不要先生成车、再单独贴一个人物。
- 生图只负责画面，不负责标题、品牌名、年份、标签和印章；这些文字全部由 HTML/CSS 叠加。
- 一个尺寸一张原生构图。不得先生成 4:3 再机械裁切成六个尺寸。
- 只要画面出现真实五官、写实照片感、可爱大头、Q 版吉祥物，直接重生成。
- 封面必须是“彩底充墨插画”，不是纯白正文配图；字体区保留大块米黄纸面。

## 固定 IP：言同学（定稿，不得擅自改特征）

- **整体**：成年男性，四十岁上下，中等偏壮实体型；扁平卡通，比例自然，不是黑色剪影。
- **发型**：短黑发，两侧剪短，黑色乱发，画出发丝细节；不要整块实心黑发、不要炸毛蓬松。
- **脸型与肤色**：方圆脸，脸颊略丰满，下巴圆润，自然黄肤色。
- **眼镜与眼睛**：黑色细框矩形眼镜；圆形眼睛略睁大平视镜头，眼神平和略带好奇；黑色平直浓眉。
- **胡须**：上唇一小撮短髭，下巴一小撮山羊胡，两颊无须；嘴唇抿着，嘴角轻微上扬，似笑非笑；双耳可见。
- **穿着**：黑色圆领短袖 T 恤，左胸白色圆形小 logo（圆圈内两道闪电状折线），下方极小白色字样；黑色斜挎包肩带从右肩斜向左胯；黑色长裤。
- **配饰**：左手腕黑色手表，右手腕黑色细腕带。**不画口罩**。
- **神态**：平静、认真，略带笨拙和一点笑意；不卖萌。
- 严禁整个人涂成黑色、做成阴影人、无脸人或纯剪影；严禁写实人脸、大头 Q 版吉祥物。

## 可复制提示词

```text
Generate one standalone Chinese knowledge-video cover illustration using the
fixed Yan Tongxue character with the approved dense retro-green cover style.

Canvas:
{宽高比与像素尺寸}

Visual DNA:
Warm cream paper background, deep pine-green filled ink illustration and
near-black hand-drawn outlines. Flat cartoon character on a dense editorial
screenprint with subtle paper grain and strong dark-green silhouette masses.
Leave a large clean cream band at the top for future large Chinese typography.
One restrained vermilion accent. No pure-white background, no glossy 3D render,
no commercial vector style, no PPT infographic look, no cute mascot poster, no
children's illustration, no realistic portrait.

Recurring character required:
Yan Tongxue, a flat cartoon adult man in his early forties, medium stocky
build, not slim, NOT a solid-black silhouette. Short black hair cropped short
on the sides, slightly messy black strands with individual hair strands drawn.
Round-square face, slightly full cheeks, rounded chin, natural yellow skin
tone. Thin black rectangular glasses, horizontal rectangle with a thin frame.
Round eyes slightly wide open, looking straight at the camera, calm and faintly
curious. Straight dark-black eyebrows of medium thickness. A small mustache on
the upper lip and a small goatee on the chin, clean-shaven on both cheeks.
Lips pressed together, mouth corners slightly raised, a quiet half-smile. Ears
visible. He wears a black crew-neck short-sleeve T-shirt with a small white
circular logo on the left chest: a circle outline containing two lightning-like
zigzag marks, with tiny white lettering beneath the logo. A black crossbody bag
strap runs from his right shoulder to his left hip. Black trousers. A black
watch on the left wrist and a thin black wristband on the right wrist. No face
mask. Neutral, serious yet slightly awkward expression with a faint smile.
Keep him a readable flat cartoon man, not an all-black figure and not a
realistic photo face.

Scene and action:
{人物必须与车或核心物件发生物理互动：靠车门、指发动机、蹲在车轮边量尺寸、
拉安全带、掀开图纸、站在碰撞测试装置旁等。写明人物位置、动作、车辆位置和景别。}

Composition:
{主视觉主体与占画比例；人物约占画面 1/4–1/3；保留标题和数字的干净负空间。}

Color accents:
Black for the character, car outline and structure. Red only for one key
warning or result. Orange only for one movement/path accent. Blue only for one
secondary note. Keep at least 35% of the canvas visually quiet.

Text:
No text, no letters, no numbers, no logos and no fake typography anywhere in
the generated image. Leave clean negative space for HTML/CSS typography.

Constraints:
One cover tells one clear story. The character must perform an essential
action, not stand beside the car as decoration. Keep the vehicle recognizable.
Do not copy an existing cover composition. No realistic face, no mascot
proportions, no commercial polish, no dense diagram, no decorative frame, no
all-white line-art cover, no all-black character, no faceless shadow figure,
no flat infographic.
```

## 沃尔沃封面动作示例

把 Scene and action 替换为：

```text
Yan Tongxue crouches beside the front wheel of a vintage Volvo, pulling one
hand along the three-point seatbelt and pointing with the other at the red
buckle. His natural-yellow face and hands, mustache and goatee must remain
clearly visible against the deep green scene. The car and industrial
background fill the lower two-thirds with deep pine-green ink masses and black
outlines. Keep the top third as a quiet warm-cream band for the HTML headline
and year.
```

不要生成写实人脸，也不要生成全黑人形。人物必须是自然黄肤、留上唇小髭和下巴山羊胡
的扁平卡通男性，并且动作直接说明安全带或安全结构。
