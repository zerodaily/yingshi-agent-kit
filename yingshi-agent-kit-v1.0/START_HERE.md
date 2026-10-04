# 硬视产线 · Agent 部署套件 v1.0

**这是什么**：一整套在用户本地电脑上搭建「AI 视频工厂」的交付包——选题 → 深度研究 → 口播稿（硬校验）→ AI 音色克隆配音 → 复古插画自动生成放大 → 合成渲染 → （可选）多平台自动发布。

**怎么用（只有两步）**：

1. 把整个 `yingshi-agent-kit` 文件夹发给客户（zip / 网盘 / 私有 git 仓库均可）
2. 告诉客户一句话：

> 「把这个文件夹解压后，丢给你的任意 AI 助手，说：**请阅读 AGENT_INSTALL.md 并完成部署**。」

Agent 会自动完成：环境预检 → 访谈收集配置（API/音色/风格图）→ 部署全部本地服务 → 冒烟测试出片 → 交付验收报告。

## 目录结构

```
yingshi-agent-kit/
├── START_HERE.md            ← 本文件（给客户看）
├── AGENT_INSTALL.md         ← Agent 执行手册（核心，部署从这里开始）
├── config/
│   ├── onboarding.md        ← Agent 访谈清单
│   └── config.template.json ← 配置模板（访谈后生成 config.json）
├── skills/
│   └── retro-narration-video/   ← 视频产线 Skill（规则+脚本+踩坑文档）
├── assets-customer/         ← 客户自备素材（音色样本、风格参考图）
└── references/
    └── faq-旧流程踩坑.md     ← 历史踩坑库
```

## 客户机器的最低要求

- Windows 10/11 + NVIDIA 显卡（≥8GB 显存）
- 硬盘剩余 ≥ 60GB（模型权重占大头）
- 其余（Python/Node/ffmpeg/WSL）Agent 会自动装

## 客户需要准备的东西

1. **一段 ≥10 秒的自己的声音录音**（干音，无背景音乐）
2. **1-3 张喜欢的视觉风格参考图**（自己的 IP 形象或海报）
3. 部署时回答 Agent 的访谈问题（品牌、人群、平台等）

## 合规提醒

- 音色与形象素材必须是本人或已授权的
- 自动发布模块（MediaCrawler）为 GPL 开源，套件不内置，由客户决定是否启用并自担平台条款风险
- 发布 AI 生成内容需遵守各平台 AI 内容标识规定

---
版本 v1.0 · 出品：硬视 YINGSHI
