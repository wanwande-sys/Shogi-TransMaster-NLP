<div align="right">
  <a href="README.md">🇨🇳 中文</a> | <a href="README_ja.md">🇯🇵 日本語</a>
</div>

# ☗ Shogi-TransMaster：基于大模型的特定垂直领域视频翻译与人机协同工作流

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📸 系统交互界面 (HITL GUI)

![Uploading image.png…]()


> ▲ 基于 Streamlit 构建的 MTPE（机器翻译译后编辑）可视化控制台。采用 **HITL（Human-in-the-Loop，人机协同）** 设计理念，支持领域专家对大模型输出结果进行极低成本的最终校验与微调。

---

## 📌 项目研发背景与行业痛点

在当前的 AI 翻译领域，通用大语言模型（LLM）和语音识别（ASR）在处理大众化语料时表现优异。但在面对**高度垂直、具有极强文化壁垒的小众领域（Domain-Specific）**（如日本将棋、传统手工艺、古籍解析）时，存在严重的“水土不服”：

1. **专有名词幻觉（Hallucination）**：例如将棋坐标“1四歩”被错误识别为“14步”，战术动作“打つ（打入）”被直译为“打字”。
2. **长尾文化传播受阻**：纯人工翻译门槛极高且耗时巨大，导致此类小众硬核知识的跨文化传播效率极低。

本项目以此为切入点，旨在通过**“语言学规则 + 大模型工程”**的跨学科交叉，构建一套高准度、低成本的垂直领域自动翻译解决方案。

---

## 💡 核心技术与创新点 (Approach)

本项目并非简单调用通用 API，而是通过以下三种轻量级“领域自适应（Domain Adaptation）”手段，彻底解决模型幻觉问题：

1. **动态领域字典注入 (Dynamic Glossary Injection)**
   利用自建的特定领域术语知识库（`shogi_glossary.json`），在翻译执行层强制干预 LLM 的词汇映射，精准规避未登录词（OOV）的误译。
2. **结构化提示词约束 (Prompt Engineering)**
   设计专门针对记谱法和解说语境的 System Prompt，强制大模型以行业标准格式（如“7七金”）输出结果。
3. **人机协同工作流 (Human-in-the-Loop)**
   系统不盲目追求“全自动”，而是将繁杂的音视频处理交由机器，保留前端 GUI 供人类专家进行最终把控，实现“技术赋能人”的温情设计。

---

## 📊 落地成果与市场验证

本系统已在真实环境中投入使用，产出的精校教学视频在 Bilibili 平台获得了极佳的市场反馈。
* **实际产出案例**：[【精校中字】山口惠梨子将棋讲座 01：形势判断基础](https://www.bilibili.com/video/BV1f2AtzvEHN)
* **用户反馈**：在硬核受众群体中，互动率（点赞/播放比）远超同类常规搬运视频，验证了“高质量专业翻译”在长尾文化受众中的巨大刚需。

---

## 🛠️ 技术架构 (Tech Stack)

* **声学模型 (ASR)**: Faster-Whisper (large-v3, 针对本地 GPU 推理优化)
* **翻译基座 (LLM)**: DeepSeek-V3 / Gemini 1.5 Flash
* **音视频引擎**: yt-dlp, FFmpeg (基于 h264_nvenc 硬件加速硬编码)
* **交互前端**: Streamlit

---

## 🚀 快速启动 (Quick Start)

⚠️ **前置要求**：请确保本地已安装 **Python 3.9+**，并已全局安装 **FFmpeg**（必须添加至系统环境变量，用于音视频处理）。

**1. 克隆项目并安装依赖**
```bash
git clone [https://github.com/wanwande-sys/Shogi-TransMaster-NLP.git](https://github.com/wanwande-sys/Shogi-TransMaster-NLP.git)
cd Shogi-TransMaster-NLP
pip install -r requirements.txt


# Windows 用户直接双击或运行：
run.bat

# Mac/Linux 用户请在终端运行：
streamlit run app.py
