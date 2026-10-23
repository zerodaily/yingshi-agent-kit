# 封面人物 IP 提示词（言同学 · 照片原型定稿 · 黑色钢笔线稿版 · 形象层唯一权威）

> 本册是封面固定人物 IP 的**唯一权威**：外貌、穿戴、神态、英文生图段、动作示例都以本册为准，
> 其他分册只写指针、不复述特征。人物识别点以照片原型定稿为准
> （`Y:\Projects\自媒体\言同学IP形象描述_照片原型.md`）。
>
> 分层归属：**形象层（本册）** = 人物特征与画风实现；**风格层**（纸底、撕边纸卡、黑白半调、
> 配色 token、标题、印章、六模板、禁止项）唯一权威在 `references/cover-and-layout.md`；
> **技术层**（出图参数、同步、放大）唯一权威在 `references/image-pipeline.md`。
> 封面整体回归已验收的复古剪报线稿风，不再使用大头卡通、写实肖像、整张纯白线稿封面，也不再使用
> 此前跑偏的「深墨绿充墨扁平插画 + 黄肤扁平人物」口径。

视觉校准文件：

- `assets/covers/style-reference-retro-clipping-16x9.jpg`
- `assets/covers/style-reference-retro-clipping-9x16.jpg`

## 使用边界

- **封面路线**：车人同框一张出、拆层贴人路线废弃；路线与落位规则见 `cover-and-layout.md` §4。
- 生图只负责画面，不负责标题、品牌名、年份、标签和印章；这些文字全部由 HTML/CSS 叠加。
- 一个尺寸一张原生构图。不得先生成 4:3 再机械裁切成六个尺寸。
- 只要画面出现真实五官、写实照片感、可爱大头、Q 版吉祥物，直接重生成。
- 纸底、撕边纸卡、半调质感、配色、印章、模板等**风格细则**权威在 `cover-and-layout.md`；
  本册生图段为可执行自包含成品，禁止项与其保持一致。

## 固定 IP：言同学（定稿，不得擅自改特征）

> 照片原型的辨识特征一条不改；封面画风为黑色钢笔线稿，黄肤在线稿里被墨色替代、靠白线勾体积，
> 不单独铺肤色块。

- **整体**：成年男性，四十岁上下，中等偏壮实体型；黑色钢笔线稿，比例自然，不是整块黑色剪影。
- **发型**：短黑发，两侧剪短，黑色乱发，用墨线画出发丝层次；不要整块实心黑发、不要炸毛蓬松。
- **脸型**：方圆脸，脸颊略丰满，下巴圆润；面部以墨线勾勒、留白勾体积，不铺肤色块。
- **眼镜与眼睛**：黑色细框矩形眼镜；圆形眼睛略睁大平视镜头，眼神平和略带好奇；黑色平直浓眉。
- **胡须**：上唇一小撮短髭，下巴一小撮山羊胡，两颊无须；嘴唇抿着，嘴角轻微上扬，似笑非笑；双耳可见。
- **穿着**：黑色圆领短袖 T 恤，左胸白色圆形小 logo（圆圈内两道闪电状折线），下方极小白色字样；黑色斜挎包肩带从右肩斜向左胯；黑色长裤。
- **配饰**：左手腕黑色手表，右手腕黑色细腕带。**不画口罩**。
- **神态**：平静、认真，略带笨拙和一点笑意；不卖萌。
- 严禁整个人涂成黑色、做成阴影人、无脸人或纯剪影；严禁写实人脸、大头 Q 版吉祥物、扁平肤色色块卡通。

## 可复制提示词

```text
Generate one standalone Chinese knowledge-video cover illustration in the
approved retro editorial paper-collage style, with the fixed Yan Tongxue
character drawn in black pen-and-ink line art.

Canvas:
{宽高比与像素尺寸}

Visual DNA（风格细则权威在 cover-and-layout.md；本段为生图自包含成品，口径与其一致）:
Warm cream aged-paper background #efe2c1 with fine paper grain, faint stains and
soft creases. The subject sits inside a torn deckle-edge paper card with a
cream keylight edge and a soft drop shadow; no hard rectangular frame.
The car, engine or scene is rendered in black-and-white halftone, old-photo
grain and woodcut hatching with gray tonal volume; one restrained accent
color appears only on a small local patch, never filling the whole vehicle.
The character is black pen-and-ink line art: ink-black hair and clothing,
white line highlights defining volume, no flat skin-tone fill. Leave a
large clean cream band at the top for future large Chinese typography.
No pure-white background, no glossy 3D render, no commercial vector style,
no PPT infographic look, no cute mascot poster, no children's illustration,
no realistic portrait, no solid-color filled car body.

Recurring character required:
Yan Tongxue, a pen-and-ink line-art adult man in his early forties, medium
stocky build, drawn in near-black ink with white highlights for volume; NOT
a solid-black silhouette and NOT a flat skin-tone cartoon. Short black hair
cropped short on the sides, slightly messy strands with individual hair
lines. Round-square face, slightly full cheeks, rounded chin; face and
hands are ink outlines with reserved white highlights, no flat yellow skin
fill. Thin black rectangular glasses, horizontal rectangle with a thin
frame. Round eyes slightly wide open, looking straight ahead, calm and
faintly curious. Straight dark-black eyebrows of medium thickness. A small
mustache on the upper lip and a small goatee on the chin, clean-shaven on
both cheeks. Lips pressed together, mouth corners slightly raised, a quiet
half-smile. Ears visible. He wears a black crew-neck short-sleeve T-shirt
with a small white circular logo on the left chest: a circle outline
containing two lightning-like zigzag marks, with tiny white lettering
beneath the logo. A black crossbody bag strap runs from his right shoulder
to his left hip. Black trousers. A black watch on the left wrist and a thin
black wristband on the right wrist. No face mask. Neutral, serious yet
slightly awkward expression with a faint smile.

Scene and action:
{人物必须与车或核心物件发生物理互动：蹲在车尾抱箱装车、握方向盘过弯、俯身调试发动机、
靠车门、指发动机、拉安全带、站在碰撞装置旁等。写明人物位置、动作、车辆位置和景别；
身体要有扭转和重心，不要僵硬站立。}

Composition:
{主视觉主体与占画比例；人物约占画面 1/4–1/3；保留标题和数字的干净负空间。}

Color accents:
Black ink #1b1b1a for the character, car outline and hatching. One restrained
accent color (vermilion #c0392b / deep green #1c3a32 / navy blue) for a title
patch or one local area only. Keep at least 35% of the canvas visually quiet cream paper.

Text:
No text, no letters, no numbers, no logos and no fake typography anywhere in
the generated image. Leave clean negative space for HTML/CSS typography.

Constraints:
One cover tells one clear story. The character must perform an essential
action, not stand beside the car as decoration. Keep the vehicle recognizable.
Do not copy an existing cover composition. No realistic face, no mascot
proportions, no commercial polish, no dense diagram, no decorative hard
frame, no all-white line-art background, no all-black character, no faceless
shadow figure, no flat infographic, no solid-color filled car body.
```

## 动作示例（替换 Scene and action 段）

### 沃尔沃 · 安全带
```text
Yan Tongxue crouches beside the front wheel of a vintage Volvo, pulling one
hand along the three-point seatbelt and pointing with the other at the red
buckle. He is drawn in black pen-and-ink line art with white highlights;
mustache, goatee and thin-frame glasses stay clearly readable. The car and
industrial background are black-and-white halftone with woodcut hatching,
filling the lower two-thirds inside a torn paper card. Keep the top third as
a quiet warm-cream band for the HTML headline and year.
```

### 五菱 · 装车
```text
Yan Tongxue crouches at the open tailgate of a micro van, lifting a
cardboard box into the cargo hold, body leaning forward with real weight
and balance. Black pen-and-ink line art, ink-black T-shirt and trousers,
white highlights on hands and face; mustache, goatee and thin-frame glasses
readable. The van is black-and-white halftone old-photo style inside a torn
paper card; one vermilion circular color patch balances the right side.
```

### 日产 · 过弯
```text
Yan Tongxue grips the steering wheel of a sports coupe through a sweeping
bend, shoulders turned into the corner. Black pen-and-ink line art with
white highlights; mustache, goatee and thin-frame glasses readable. The
coupe and curved track are black-and-white halftone with speed hatching
inside a torn paper card; keep the top band clean cream for the headline.
```

不要生成写实人脸，也不要生成全黑人形。人物必须是留上唇小髭和下巴山羊胡、戴细框眼镜的
黑色钢笔线稿男性，动作直接说明本集主题；车与场景是黑白半调木刻质感，和线稿人物拼贴在
同一张撕边纸卡内。
