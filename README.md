# 硬视 Agent Kit v1.0

「言同学」复古纸墨风汽车知识口播视频自动化产线。从选题到B站草稿全流程本地闭环，无需在线API，22GB显存单卡跑完全部流程。

## 核心能力

一条视频从选题到B站草稿箱，全自动完成：
1. 品牌/车型历史调研 → 2. 口播稿撰写（硬规则校验）→ 3. IndexTTS2 本地音色克隆配音
4. Z-Image 本地批量出复古配图 → 5. Real-ESRGAN 4倍放大 → 6. HyperFrames 横/竖屏合成渲染
7. 自动按新规范上传B站草稿（封面同步、简介、粉丝动态、精选评论）

最终产出：横屏1920×1080 + 抖音竖屏1080×1920 两个版本，6尺寸封面，23张复古插画，发布物料齐全。

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
yingshi-agent-kit-v1.0/
├── AGENT_INSTALL.md           # 部署指南
├── START_HERE.md              # 快速上手指引
├── config/                    # 全局配置文件
│   ├── config.json
│   ├── config.template.json
│   └── onboarding.md
├── references/                # 通用参考文档
│   ├── FAQ-高频问题解答.md
│   └── 选题库模板.md
├── skills/
│   └── retro-narration-video/ # 核心产线skill
│       ├── SKILL.md           # 8步产线规范 + B站发布流程
│       ├── scripts/           # 自动化脚本
│       │   ├── parse_script.py
│       │   ├── indextts2_speak.py
│       │   ├── zimage_gen.py
│       │   └── transcribe_wsl.py
│       ├── references/        # 各步骤详细规范
│       └── assets/            # 模板素材
└── assets-customer/           # 客户侧素材说明
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
