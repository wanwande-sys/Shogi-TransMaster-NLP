# Shogi-TransMaster-NLP
# Shogi-TransMaster-NLP

**AI 驱动的将棋视频自动翻译与字幕压制工具**

一个基于 Streamlit 的全自动工作台，支持从 YouTube 下载日语将棋解说视频 → Whisper 语音识别 → 大模型翻译 → FFmpeg 硬件加速字幕压制 → 输出中文字幕视频。

### 核心功能
- 支持单视频 / 播放列表 / 专栏批量下载（自动提取日文字幕）
- 将棋专用优化：坐标规范（7七金）、术语纠正（打入、成、同）、自定义词库
- 多种字幕样式：B站经典风、竖排、半透明遮挡板、高位防挡 UI
- 支持双语对照 / 仅中文 输出
- RTX NVENC 硬件加速压制，速度快、画质高
- 生肉自动备份

### 技术栈
- 语音识别：faster-whisper large-v3 (CUDA)
- 翻译模型：DeepSeek-V3 / Gemini 1.5 Flash
- 下载工具：yt-dlp
- 字幕压制：ffmpeg h264_nvenc
- 前端界面：Streamlit

### 快速启动
```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
streamlit run app.py
