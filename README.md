<div align="right">
  <a href="README.md">🇨🇳 中文</a> | <a href="README_ja.md">🇯🇵 日本語</a>
</div>

# ☗ Shogi-TransMaster：基于大模型的垂直领域视频翻译与人机协同系统

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📸 系统交互界面 (HITL GUI)

<img width="2467" height="1266" alt="Image" src="https://github.com/user-attachments/assets/de983344-ecdd-4cfd-ae13-9e234350c405" />

> ▲ 基于 Streamlit 构建的机器翻译后编辑（MTPE）可视化界面。采用 Human-in-the-Loop（人机协同）设计，支持领域专家对模型输出进行高效校验和优化。

---

## 📌 项目背景与行业痛点

当前通用大语言模型（LLM）和语音识别（ASR）在处理大众化语料时已较为成熟，但在高度垂直、专业性强且文化壁垒明显的特定领域（如日本将棋、传统手工艺、古籍整理等），仍面临显著挑战：

1. **专有名词识别偏差**：例如将棋坐标“1四歩”常被误识别为“14步”，战术动作“打つ（打入）”被直译为“打字”，导致专业含义完全丢失。
2. **文化语境理解不足**：纯人工翻译门槛高、耗时长，使得此类小众硬核知识的跨文化传播效率较低，许多优质将棋教学内容难以被国际爱好者准确理解。

Shogi-TransMaster 项目以此为切入点，专注于日本将棋领域的音视频翻译，结合语言学规则与大模型工程，构建一套适用于垂直领域的翻译解决方案。

---

## 💡 核心技术特点

项目采用轻量级领域适配策略，提升模型在特定场景下的准确性，主要包括以下三种方法：

1. **动态领域字典注入 (Dynamic Glossary Injection)**  
   利用自建的将棋专业术语知识库（`shogi_glossary.json`），在翻译流程中强制引导 LLM 的词汇映射。例如遇到“7七金”时，系统会直接注入标准术语，避免通用模型的随意改写。

2. **结构化提示词设计 (Prompt Engineering)**  
   针对将棋记谱法和专业解说语境，设计专用 System Prompt，指导模型严格按照行业标准格式输出（如“7七金”“▲1四歩”），确保记谱准确无误。

3. **人机协同工作流 (Human-in-the-Loop)**  
   将音视频处理、初步翻译等重复性任务交给机器，同时保留可视化控制台供领域专家进行最终审核与微调，实现“机器干重活、专家把关”的高效协作。

---

## 📊 应用成果

本系统已在实际生产环境中使用，产出的精校将棋教学视频在 Bilibili 平台获得较好反馈。

**实际产出案例**：  
[【精校中字】山口惠梨子将棋讲座 01：形势判断基础](https://www.bilibili.com/video/BV1f2AtzvEHN)

---

## 🛠️ 技术架构

- **语音识别 (ASR)**：Faster-Whisper (large-v3，本地 GPU 优化)  
- **翻译模型 (LLM)**：DeepSeek-V3 / Gemini 1.5 Flash  
- **音视频处理**：yt-dlp + FFmpeg（支持 NVIDIA h264_nvenc 硬件加速）  
- **用户界面**：Streamlit

---

## 🚀 快速开始

**环境要求**：Python 3.9+，并确保已全局安装 FFmpeg（需添加至系统环境变量）。

```bash
git clone https://github.com/wanwande-sys/Shogi-TransMaster-NLP.git
cd Shogi-TransMaster-NLP
pip install -r requirements.txt

# Windows 用户可直接运行：
run.bat

# Mac/Linux 用户请在终端执行：
streamlit run app.py
