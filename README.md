# 硬视 Agent Kit

「言同学」知识口播视频自动化产线。从选题到 B站草稿全流程本地闭环，无需在线 API。

仓库里有两个版本目录：

| 目录 | 说明 |
|---|---|
| `yingshi-agent-kit-v1.0/` | 初版。只有复古纸墨一个画风，8 步产线 + B站发布 |
| `yingshi-agent-kit-v1.1/` | **当前版本**。多画风 × 多领域，新增分层舞台与本地元素引擎 |

## 核心能力

一条视频从选题到B站草稿箱，全自动完成：
1. 品牌/车型历史调研 → 2. 口播稿撰写（硬规则校验）→ 3. IndexTTS2 本地音色克隆配音
4. Z-Image 本地批量出复古配图 → 5. Real-ESRGAN 4倍放大 → 6. HyperFrames 横/竖屏合成渲染
7. 自动按新规范上传B站草稿（封面同步、简介、粉丝动态、精选评论）

最终产出：横屏1920×1080 + 抖音竖屏1080×1920 两个版本，6尺寸封面，23张复古插画，发布物料齐全。

## v1.1 新增能力

v1.1 把产线从「单一画风」改成**两个正交维度**：

```
画风（styles/） × 领域（domains/） = 一条片子
看起来怎样          讲的是什么
```

- **画风包**：`00-retro-paper`（复古纸墨，默认）、`10-collage-archive`（档案调查拼贴）、`20-collage-design`（设计拼贴）
- **领域包**：`automotive`、`ai`、`history`；新领域只需写一份 `DOMAIN.md`

**分层舞台**是 v1.1 的核心：一个画面由多个图层按时间轴逐件组装，
替代 AI 视频模型的镜头动画，不依赖任何视频生成模型。

- **本地元素引擎**：`photo_to_cutout.py` 把真实照片变成半调剪影纸片
  （抠图 → 半调网点 → 双色调上纸 → 撕边 → 透明 PNG），纯 CPU，7 个元素约 12 秒，不占显存
- **分镜构建器**：`build_film.py` 读一份 `film.json` 自动生成横竖两个工程，
  自动排节拍、长场景补第二波、左出右进、红绳自动连线；`build_film_split.py` 按章拆子合成
- **镜头语言**：`shotgram.py` 控制景别 / 机位 / 运动 / 构图 / 转场分布，避免「一个模子切 150 次」
- **音频**：`mix_bgm.py` 按响度对齐 + 侧带闪避 + 限幅，输出单轨混音
- **四个分层舞台模板**（包 A/B × 横竖）+ 4 套封面模板

详见 `yingshi-agent-kit-v1.1/CHANGELOG-v1.1.md`。

## 已完成案例

已按此产线批量完成 20+ 条汽车品牌/经典车型视频：丰田、本田、福特、雪佛兰、日产、凯迪拉克、现代、起亚、兰博基尼、法拉利、阿尔法罗密欧、标致、雪铁龙、雷诺、沃尔沃、吉普牧马人、奔驰300SL、思域TypeR、道奇Viper、陆地巡洋舰等。

## 快速开始

### 环境依赖
- Windows + WSL2（Ubuntu）
- NVIDIA 22GB+ 显存显卡（2080Ti 22G 可跑）
- ffmpeg / Node.js 18+ / Python 3.11

### 部署
```bash
# 1. 克隆仓库
git clone https://github.com/zerodaily/yingshi-agent-kit.git
cd yingshi-agent-kit

# 2. 按 AGENT_INSTALL.md 配置本地模型路径
# 配置文件位置：config/config.json
# 需要本地部署：
# - IndexTTS2 (WSL, 端口7860)
# - Z-Image-Turbo (WSL conda env: wan2gp)
# - Real-ESRGAN 放大工具
# - HyperFrames (npx 全局安装)

# 3. 安装skill到你的Agent工作区
# 把 skills/retro-narration-video 整个目录复制到 .user_skills/ 下
```

## 目录结构

```
yingshi-agent-kit-v1.1/          # 当前版本
├── AGENT_INSTALL.md             # 部署指南
├── START_HERE.md                # 快速上手指引
├── CHANGELOG-v1.1.md            # 版本变更
├── config/                      # 全局配置
├── styles/                      # 画风包（00 复古纸墨 / 10 档案拼贴 / 20 设计拼贴）
├── domains/                     # 领域包（automotive / ai / history）
└── skills/
    └── retro-narration-video/   # 核心产线skill
        ├── SKILL.md
        ├── scripts/             # 33 个自动化脚本
        ├── references/          # 10 份步骤规范
        └── assets/              # 分层舞台模板 + 封面模板

yingshi-agent-kit-v1.0/          # 初版（仅复古纸墨）
├── AGENT_INSTALL.md
├── START_HERE.md
├── config/
├── references/
├── skills/
│   └── retro-narration-video/
└── assets-customer/
```

### 外部 skill（git 子模块）

`yingshi-agent-kit-v1.0/skills/` 下的 3 个第三方 skill 以 **git 子模块**形式引入。
克隆时必须带 `--recurse-submodules`，否则这三个目录是空的：

| 目录 | 上游 |
|---|---|
| `gbro-collage-broll` | https://github.com/pyang5166/gbro-collage-broll.git |
| `minimax-h3-vox` | https://github.com/panxxpan/Minimax-H3-Vox.git |
| `huashu-art-motion` | https://github.com/alchaincyf/huashu-art-motion.git（约 284MB） |

```bash
git clone --recurse-submodules https://github.com/zerodaily/yingshi-agent-kit.git

# 已经克隆过的话：
git submodule update --init --recursive
```

## 关键规范（踩坑沉淀）

1. 年份用「零」不用「〇」，避免TTS读错
2. 口播正文禁止Markdown符号/括号/破折号
3. 每个画面必须配一张复古插画，禁止纯文字页
4. B站发布禁止用Playwright（有风控），改用Browser Use操作用户登录的Chrome
5. 封面用 `input[accept*='image']` 选择器上传，避免选到视频input
6. 更多设置默认折叠，必须先展开再填互动内容
7. 粉丝动态必写，按placeholder精确定位输入框

## License
私有项目，仅供内部使用。
